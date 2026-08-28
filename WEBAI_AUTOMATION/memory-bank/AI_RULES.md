# AI Assistant Core Rules & Operational Vibe Protocol

**CRITICAL: All AI assistants (Antigravity, Cline, Gemini, Cursor, etc.) MUST strictly follow these rules when operating in this repository.**

---

## 1. Documentation & Code Synchronization
- **Docstrings:** Whenever you modify Python code (functions, classes, methods), you MUST automatically update the corresponding docstrings to reflect the new behavior or parameters.
- **Continuous Knowledge & Diagram Synchronization:** Upon modifying any source code, you MUST update all associated graph and documentation artifacts before marking the task complete:
  - **Graphify Index:** Update the AST knowledge graph (`graphify update .`).
  - **Mermaid Diagrams:** Regenerate or align Mermaid diagrams via `python scripts/graphify_to_mermaid.py` and update relevant system/sequence/ER diagrams.
  - **Memory Bank Artifacts:** Update `memory-bank/activeContext.md`, `memory-bank/progress.md`, and affected `.md` files to maintain strict parity between code implementation and project documentation.
- **Verification:** Never finish a task without confirming that the documentation, visual diagrams, knowledge graphs, and codebase are perfectly in sync.

---

## 2. Memory Bank Maintenance
This project uses a `memory-bank/` directory to track state, progress, and architectural decisions. You are responsible for keeping it updated:
- **Bug Fixes & Daily Work:** Log every completed task, bug fix, or minor code change in `memory-bank/activeContext.md` (under "Recent Work Completed") and `memory-bank/progress.md` (under "Recently Fixed Issues" or feature status).
- **Architectural Changes:** Any significant design choice, new dependency, or alternative approach considered MUST be documented in `memory-bank/decisionLog.md`.
- **System Patterns:** If a new core mechanic is introduced, update `memory-bank/systemPatterns.md`.

---

## 3. Code Quality & Style
- **Minimal Targeted Changes & Comment Sync:** Modify ONLY the lines necessary to solve the task. Do NOT rewrite entire functions or reformat unrelated code. Modify or delete existing inline comments if they become outdated due to code changes. Ensure all comments remain perfectly in sync with current code.
- **Type Hinting:** All new Python functions MUST include strict type hints for arguments and return values (e.g., `def get_user(id: int) -> Optional[User]:`).
- **Graceful Error Handling:** Never leave bare `except:` blocks. Always catch specific exceptions and log them meaningfully instead of failing silently.

---

## 4. Testing & Verification
- **Mandatory Verification:** Before concluding that a bug is fixed or a feature is complete, you MUST run a test (using `pytest` or a manual script execution) to prove the code works. Never assume code works just by looking at it.
- **No Syntax Errors:** Always verify there are no indentation or syntax errors after injecting code into an existing file.

---

## 5. Dependency Management
- **Check Before Importing:** Before importing a third-party library, check if it exists in `requirements.txt`. If missing, ask the user for permission before running `pip install`.
- **Use Virtual Environments:** When executing Python commands in the terminal, always ensure you are using the local virtual environment (e.g., `.\venv\Scripts\python.exe`), not the global system Python.

---

## 6. Safety & Permissions
- **No Destructive Actions:** You MUST explicitly ask the user for permission before executing any command that deletes files, drops database tables, or makes irreversible changes.
- **No Git Commits:** Do NOT run `git commit` autonomously. You may stage files or run `git diff`, but the user must be the one to officially commit the changes.

---

# VIBE CODING & AUTONOMOUS STABILITY PROTOCOL

The following 5 points dictate how the AI must execute new features, refactors, and bug fixes without breaking existing codebase functionality.

---

## 7. Test-Driven Vibe Coding (TDVC)
Do not write or modify core implementation files (`local_webai_server_guided.py`, `fallback_helpers.py`, `recorder.py`, etc.) based purely on user feature requests without tests.

1. **Write the Test First:** Before implementing a feature (e.g., Conditional Branching), create a new test in `webai_local_server/tests/` or `scratch/` (e.g., `test_conditional_branching.py`).
2. **Mock & Assert:** The test must mock the required state (e.g., `page.__extracted_data__`) and assert the expected outcome.
3. **The Guardrail:** Run the test using `pytest`. Implement the feature only after the test is written. If your implementation breaks any existing passing tests, you must immediately read the `stderr` traceback and fix your code without altering the test assertions.

---

## 8. The Context Diet (Graphify Integration)
Do not attempt to read 1,600+ line files in their entirety. You will lose context and destroy implicit dependencies.

1. **Query the Graph:** Use your Graphify skill to map the target area. Run `graphify explain "<function_name>"` to understand specific components.
2. **Isolate Subgraphs:** Use `graphify path "<File A>" "<File B>"` to inspect how components interact (e.g., how `recorder.py` sends data to `fallback_helpers.py`).
3. **Minimal Edits:** Request and edit only the specific line numbers or functions identified by the Graphify output.

---

## 9. The Plugin Architecture Pattern
Do not inject new feature logic directly into core execution loops (e.g., the main `while` loop in the AI server or the `__recordEvent` listener in the browser).

1. **Event-Driven Design:** Treat the core engine as an immutable Event Bus. It should only broadcast events (e.g., `on_action_complete`, `on_extraction_success`, `on_step_failed`).
2. **Isolate Features:** For new features (e.g., Jira Integration, Variable Persistence), create a distinct Python class in a separate module/plugin.
3. **Subscribe & Execute:** The plugin must subscribe to the Event Bus. If the plugin throws an exception, it must be caught inside a `try/except` block so the primary Playwright/WebAI execution loop never crashes.

---

## 10. Strict Prompting Contracts
Before writing any implementation code to disk, you MUST output a **Modification Plan** and wait for human confirmation.

The Modification Plan must include:
1. The exact files and function names you intend to modify.
2. A brief explanation of how core functionality will remain unaffected.
3. A verification step showing how `LOCATOR_PRIORITY` rules and existing test suites are preserved.

---

## 11. Autonomous E2E Validation Loop (Self-Healing)
You are authorized to autonomously test and patch your own code using Playwright, pytest, and process exit codes.

1. **Test Runner Harness:** Create or run a test runner script in `scratch/` that executes your target Playwright test via `subprocess.run()`.
2. **The Iteration Loop:** Wrap execution in a `while` loop (capped at 5 maximum iterations).
3. **Observe & Patch:**
   - **If `exit_code == 0`:** Log success, run `graphify update .`, and complete the task.
   - **If `exit_code != 0`:** Capture `stderr` tracebacks and Playwright failure reasons (e.g., `TimeoutError: locator not found`). Use this error context to patch the target implementation file.
4. **Forbidden Test Modification:** You are **strictly forbidden** from modifying assertion lines in `tests/` to force a pass. You must fix the implementation code.
5. **Hard Stop:** If the loop reaches 5 failed attempts, stop immediately and report the architectural blocker to the user.