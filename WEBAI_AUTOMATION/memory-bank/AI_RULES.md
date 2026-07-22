# AI Assistant Core Rules

**CRITICAL: All AI assistants (Cline, Gemini, Cursor, etc.) MUST strictly follow these rules when operating in this repository.**

## 1. Documentation & Code Synchronization
- **Docstrings:** Whenever you modify Python code (functions, classes, methods), you MUST automatically update the corresponding docstrings to reflect the new behavior or parameters.
- **Verification:** Never finish a task without confirming that the documentation and the codebase are perfectly in sync.

## 2. Memory Bank Maintenance
This project uses a `memory-bank/` directory to track state, progress, and architectural decisions. You are responsible for keeping it updated:
- **Bug Fixes & Daily Work:** Log every completed task, bug fix, or minor code change in `memory-bank/activeContext.md` (under "Recent Work Completed") and `memory-bank/progress.md` (under "Recently Fixed Issues" or feature status).
- **Architectural Changes:** Any significant design choice, new dependency, or alternative approach considered MUST be documented in `memory-bank/decisionLog.md`.
- **System Patterns:** If a new core mechanic is introduced, update `memory-bank/systemPatterns.md`.

## 3. Code Quality & Style
- **Minimal Targeted Changes & Comment Sync:** Modify ONLY the lines necessary to solve the task. Do NOT rewrite entire functions or reformat unrelated code. However, you MUST modify or delete existing inline comments if they become outdated due to your code changes. The ultimate aim is to ensure all comments remain perfectly in sync with the current code.
- **Type Hinting:** All new Python functions MUST include strict type hints for arguments and return values (e.g., `def get_user(id: int) -> Optional[User]:`).
- **Graceful Error Handling:** Never leave bare `except:` blocks. Always catch specific exceptions and log them meaningfully instead of failing silently.

## 4. Testing & Verification
- **Mandatory Verification:** Before concluding that a bug is fixed or a feature is complete, you MUST run a test (using `pytest` or a manual script execution) to prove the code works. Never assume code works just by looking at it.
- **No Syntax Errors:** Always verify there are no indentation or syntax errors after injecting code into an existing file.

## 5. Dependency Management
- **Check Before Importing:** Before importing a third-party library, you MUST check if it exists in `requirements.txt`. If it is missing, you MUST ask the user for permission before running `pip install`.
- **Use Virtual Environments:** When executing Python commands in the terminal, always ensure you are using the local virtual environment (e.g., `.\venv\Scripts\python.exe`), not the global system Python.

## 6. Safety & Permissions
- **No Destructive Actions:** You MUST explicitly ask the user for permission before executing any command that deletes files, drops database tables, or makes irreversible changes.
- **No Git Commits:** Do NOT run `git commit` autonomously. You may stage files or run `git diff`, but the user must be the one to officially commit the changes.

By following these rules, the codebase will remain maintainable and human-readable, and context will not be lost between different AI agents.
