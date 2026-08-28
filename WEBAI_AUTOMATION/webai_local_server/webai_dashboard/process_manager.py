"""
Playback subprocess lifecycle manager for the WebAI dashboard server.

The dashboard triggers browser automations by spawning
`run_from_task_txt_guided.py` as a background subprocess. This module tracks
those processes in a thread-safe registry, reports their live status to the
front-end, and via a daemon watcher thread finalizes the execution record
(`PUT /executions/{id}`) when playback exits. This closes the historical gap
where CLI-triggered executions stayed in running status forever.

It also provides a stale-execution reconciler that sweeps orphan RUNNING rows
on startup and during polling, marking them FAILED when their subprocess is
no longer active.
"""
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


class PlaybackRun:
    """State snapshot for a single spawned playback subprocess."""

    def __init__(self, run_id: int, automation_id: int,
                 execution_id: Optional[int], process: subprocess.Popen) -> None:
        self.run_id = run_id
        self.automation_id = automation_id
        self.execution_id = execution_id
        self.process = process
        self.started_at = datetime.utcnow()
        self.finished_at: Optional[datetime] = None
        self.returncode: Optional[int] = None

    @property
    def status(self) -> str:
        """Live run status: running, success, or failed."""
        if self.process.poll() is None:
            return "running"
        return "success" if self.process.returncode == 0 else "failed"

    def to_dict(self) -> Dict[str, object]:
        """Serialize the run state for JSON API responses."""
        return {
            "run_id": self.run_id,
            "automation_id": self.automation_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "returncode": self.returncode,
        }


class PlaybackProcessManager:
    """Thread-safe registry of playback subprocesses spawned by the dashboard."""

    def __init__(self) -> None:
        self._runs: Dict[int, PlaybackRun] = {}
        self._lock = threading.Lock()
        self._next_run_id: int = 1

    def spawn(self, *, automation_id: int, execution_id: Optional[int],
              python_exe: Path, script: str, cwd: Path, env: Dict[str, str],
              api_url: str, api_key: str) -> PlaybackRun:
        """Spawn a playback subprocess and register a background watcher."""
        process = subprocess.Popen(
            [str(python_exe), script],
            cwd=str(cwd),
            env=env,
        )

        with self._lock:
            run = PlaybackRun(self._next_run_id, automation_id, execution_id, process)
            self._runs[run.run_id] = run
            self._next_run_id += 1

        watcher = threading.Thread(
            target=self._watch,
            args=(run, api_url, api_key),
            daemon=True,
            name=f"playback-watch-{run.run_id}",
        )
        watcher.start()
        return run

    def list_runs(self) -> List[PlaybackRun]:
        """Return snapshots of all tracked runs (active and finished)."""
        with self._lock:
            return list(self._runs.values())

    def get_by_execution(self, execution_id: int) -> Optional[PlaybackRun]:
        """Look up a tracked run by its database execution ID."""
        with self._lock:
            for run in self._runs.values():
                if run.execution_id == execution_id:
                    return run
        return None

    def has_active_runs(self) -> bool:
        """Return True while at least one playback subprocess is still alive."""
        return any(run.status == "running" for run in self.list_runs())

    def active_execution_ids(self) -> List[int]:
        """Return execution IDs of all currently-running playback subprocesses."""
        with self._lock:
            return [run.execution_id for run in self._runs.values()
                    if run.execution_id is not None and run.status == "running"]

    def reconcile_stale_executions(self, api_url: str, api_key: str,
                                   limit: int = 200) -> int:
        """
        Mark orphan RUNNING executions as FAILED.

        Historical executions stay stuck in RUNNING forever when their
        subprocess exited without finalizing the status. This sweeper fetches
        recent executions, finds ones still marked RUNNING that are not tracked
        by this process manager, and calls PUT /executions/{id}?status=failed.

        Args:
            api_url: Base URL of the WebAI API server.
            api_key: X-API-Key with permission to list/update executions.
            limit: How many recent executions to inspect (default 200).

        Returns:
            The number of orphan executions reconciled to FAILED.
        """
        try:
            resp = requests.get(
                f"{api_url}/executions",
                headers={"X-API-Key": api_key},
                params={"limit": limit},
                timeout=15,
            )
        except requests.RequestException as exc:
            print(f"[WARN] Reconcile: could not fetch executions: {exc}")
            return 0

        if resp.status_code != 200:
            print(f"[WARN] Reconcile: upstream returned {resp.status_code}")
            return 0

        executions = resp.json() or []
        active_ids = set(self.active_execution_ids())
        reconciled = 0

        for execution in executions:
            exec_id = execution.get("id")
            status = (execution.get("status") or "").lower()
            live = (execution.get("live_status") or "").lower()

            if exec_id in active_ids:
                continue
            if status != "running":
                continue
            if live == "running":
                continue

            try:
                put_resp = requests.put(
                    f"{api_url}/executions/{exec_id}",
                    params={
                        "status": "failed",
                        "error_message": "Reconciled by dashboard sweeper: process no longer active",
                    },
                    headers={"X-API-Key": api_key},
                    timeout=10,
                )
                if put_resp.status_code == 200:
                    reconciled += 1
                    print(f"[INFO] Reconcile: execution {exec_id} marked FAILED")
            except requests.RequestException as exc:
                print(f"[WARN] Reconcile: failed to update execution {exec_id}: {exc}")

        if reconciled:
            print(f"[INFO] Reconcile: {reconciled} orphan execution(s) finalized")
        return reconciled

    def _watch(self, run: PlaybackRun, api_url: str, api_key: str) -> None:
        """Daemon watcher: block until subprocess exits, then finalize."""
        run.returncode = run.process.wait()
        run.finished_at = datetime.utcnow()
        if run.execution_id is not None:
            self._finalize_execution(run, api_url, api_key)

    def _finalize_execution(self, run: PlaybackRun, api_url: str, api_key: str) -> None:
        """Report the final run status to the API server and append an audit log."""
        final_status = "success" if run.returncode == 0 else "failed"
        params: Dict[str, object] = {"status": final_status}
        if run.returncode != 0:
            params["error_message"] = f"Playback process exited with code {run.returncode}"

        try:
            requests.put(
                f"{api_url}/executions/{run.execution_id}",
                params=params,
                headers={"X-API-Key": api_key},
                timeout=10,
            )
        except requests.RequestException as exc:
            print(f"[WARN] Failed to finalize execution {run.execution_id}: {exc}")
            return

        try:
            requests.post(
                f"{api_url}/logs/batch",
                json={
                    "execution_id": run.execution_id,
                    "logs": [{
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO" if run.returncode == 0 else "ERROR",
                        "source": "api",
                        "message": f"Dashboard playback finished with status '{final_status}' (exit code {run.returncode})",
                        "metadata": {
                            "run_id": run.run_id,
                            "automation_id": run.automation_id,
                            "returncode": run.returncode,
                        },
                    }],
                },
                headers={"X-API-Key": api_key},
                timeout=5,
            )
        except requests.RequestException as exc:
            print(f"[WARN] Failed to log finalization for execution {run.execution_id}: {exc}")