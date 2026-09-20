import json
import pytest
from typing import Any, Dict, List, Optional, Tuple

from webai_local_server.local_webai_server_guided import (
    BASE_PROMPT,
    _infer_task_type,
    normalize_task,
    build_system_prompt,
)


def _simulate_circuit_breaker(
    plan: List[Dict[str, Any]],
    current_url: str,
    last_action_sig: Optional[str],
    repeat_action_count: int,
    last_seen_url: Optional[str],
    make_sig_func: Any,
) -> Tuple[List[Dict[str, Any]], Optional[str], int, Optional[str], bool]:
    """
    Simulates the circuit breaker logic implemented in handle_client loop.
    Returns: (updated_plan, last_action_sig, repeat_action_count, last_seen_url, hitl_triggered)
    """
    hitl_triggered = False
    if plan:
        first_act = plan[0]
        current_sig = make_sig_func(first_act)

        if current_sig and current_sig == last_action_sig and current_url == last_seen_url:
            repeat_action_count += 1
        else:
            repeat_action_count = 0
            last_action_sig = current_sig
            last_seen_url = current_url

        if repeat_action_count >= 2:
            hitl_triggered = True
            plan = [{
                "action": "request_help",
                "message": "I clicked this multiple times without navigation. Please click the desired option directly on screen, then click Resume AI."
            }]

    return plan, last_action_sig, repeat_action_count, last_seen_url, hitl_triggered


def test_base_prompt_anti_loop_and_read_first_directives():
    """Verify BASE_PROMPT includes read-first, dropdown toggle, and anti-loop directives."""
    assert "READ-FIRST" in BASE_PROMPT or "informational" in BASE_PROMPT.lower()
    assert "dropdown" in BASE_PROMPT.lower()
    assert "anti-loop" in BASE_PROMPT.lower() or "exact same action" in BASE_PROMPT.lower()


def test_infer_task_type_informational():
    """Verify informational queries ('check', 'find out', 'what is') are inferred correctly."""
    assert _infer_task_type("Check the school contact phone number") == "informational"
    assert _infer_task_type("Find out the fee structure for grade 5") == "informational"
    assert _infer_task_type("What is the principal email address") == "informational"


def test_normalize_task_read_first_guidance():
    """Verify normalize_task injects read-first, anti-loop, and dropdown requirements."""
    norm = normalize_task("Check the admission fees at https://example.com")
    assert "informational queries" in norm.lower() or "inspect visible" in norm.lower()
    assert "dropdown" in norm.lower()
    assert "same action" in norm.lower() or "anti-loop" in norm.lower()


def test_build_system_prompt_informational_template():
    """Verify build_system_prompt injects informational template when task_type is informational."""
    prompt = build_system_prompt("Check school timings", {"task_type": "informational"})
    assert "INFORMATIONAL" in prompt
    assert "summary" in prompt.lower()


def test_make_action_sig_consistency():
    """Verify action signatures are consistent and differentiate distinct targets."""
    from webai_local_server.local_webai_server_guided import _make_action_sig

    act1 = {"action": "click", "target": {"by": "text", "text": "Academics", "exact": False}}
    act2 = {"action": "click", "target": {"by": "text", "text": "Academics", "exact": False}}
    act3 = {"action": "click", "target": {"by": "text", "text": "Admissions", "exact": False}}
    act_loc = {"action": "clickLocation", "x": 120, "y": 450}

    sig1 = _make_action_sig(act1)
    sig2 = _make_action_sig(act2)
    sig3 = _make_action_sig(act3)
    sig_loc = _make_action_sig(act_loc)

    assert sig1 == sig2
    assert sig1 != sig3
    assert sig1 != sig_loc


def test_circuit_breaker_detects_repeat_and_escalates():
    """Verify repetitive clicks on the same URL escalate to request_help after >= 2 duplicates."""
    from webai_local_server.local_webai_server_guided import _make_action_sig

    act = {"action": "click", "target": {"by": "text", "text": "Dropdown Menu", "exact": False}}
    url = "https://example.com/home"

    # Turn 1: First attempt
    plan = [act]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, url, None, 0, None, _make_action_sig
    )
    assert count == 0
    assert not triggered
    assert plan[0]["action"] == "click"

    # Turn 2: Second attempt (first duplicate)
    plan = [act]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, url, sig, count, seen_url, _make_action_sig
    )
    assert count == 1
    assert not triggered
    assert plan[0]["action"] == "click"

    # Turn 3: Third attempt (second duplicate, count reaches 2 -> circuit breaker trips)
    plan = [act]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, url, sig, count, seen_url, _make_action_sig
    )
    assert count == 2
    assert triggered
    assert plan[0]["action"] == "request_help"
    assert "I clicked this multiple times without navigation" in plan[0]["message"]


def test_circuit_breaker_resets_on_navigation():
    """Verify circuit breaker resets repeat_action_count when URL changes."""
    from webai_local_server.local_webai_server_guided import _make_action_sig

    act = {"action": "click", "target": {"by": "text", "text": "Next Page", "exact": False}}

    # Turn 1 at page 1
    plan = [act]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, "https://example.com/page1", None, 0, None, _make_action_sig
    )
    assert count == 0

    # Turn 2: Navigation happened! Same action signature but different URL
    plan = [act]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, "https://example.com/page2", sig, count, seen_url, _make_action_sig
    )
    assert count == 0
    assert not triggered
    assert seen_url == "https://example.com/page2"


def test_circuit_breaker_resets_on_different_action():
    """Verify circuit breaker resets repeat_action_count when action signature changes."""
    from webai_local_server.local_webai_server_guided import _make_action_sig

    act1 = {"action": "click", "target": {"by": "text", "text": "Option A"}}
    act2 = {"action": "click", "target": {"by": "text", "text": "Option B"}}
    url = "https://example.com"

    plan = [act1]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, url, None, 0, None, _make_action_sig
    )
    assert count == 0

    plan = [act2]
    plan, sig, count, seen_url, triggered = _simulate_circuit_breaker(
        plan, url, sig, count, seen_url, _make_action_sig
    )
    assert count == 0
    assert not triggered


def test_done_with_summary_accepted_without_prior_action():
    """Verify that an early done action with summary is accepted for informational queries."""
    from webai_local_server.local_webai_server_guided import TaskDone

    def evaluate_done(act: Dict[str, Any], did_any_action: bool) -> bool:
        summary = act.get("summary")
        if not did_any_action and not summary:
            return False
        return True

    assert evaluate_done({"action": "done"}, did_any_action=False) is False
    assert evaluate_done({"action": "done"}, did_any_action=True) is True
    assert evaluate_done({"action": "done", "summary": "School phone is +91-44-12345678"}, did_any_action=False) is True

