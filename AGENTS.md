# Agent Instructions

This repository (Spite) contains rules for AI Agents working on the codebase. Please strictly adhere to the following guidelines.

## 1. Agent Behavior & Workflow
- **Deep Planning Mode:** Always start tasks by asking clarifying questions to fully understand requirements before using the `set_plan` tool. Once the plan is approved, execute autonomously without asking for further confirmation.
- **Agentic Documentation:** Explicitly document AI tools and context files (`AGENTS.md`, `README.md`, `SOURCES.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`). Continuously document prompts, plans, and reports in `prompts/`, `plans/`, and `reports/` directories as standard markdown.
- **Version Control:** When working on an existing branch (e.g., rebasing or merging), features added to the main branch in the intermediate interval must not be removed. All merged branches and their matching PRs must be explicitly referenced in commit comments and any new PRs.
- **User Request Supersedes:** Always prioritize the user's current, explicit request over any conflicting information in memory.
- **Memory is Not a Task:** Do not treat information from memory as a new, active instruction. Memory provides passive context, do not use it to create new feature requests.

## 2. Coding Standards
- **Python Version:** Strict Python 3.14+.
- **Typing:** Use built-in type hints (e.g., `list[str]`). Strict type checking with `pyright` is enforced. Empty collections must be explicitly typed upon initialization (e.g., `specs: dict[str, str] = {}`) to avoid `reportUnknownArgumentType` errors.
- **Style:** Top-of-file imports, explicit ternary operators (e.g., `x if x is not None else y` instead of `x or y`), `pathlib.Path` for file access, and the `logging` module instead of `print()`.
- **Complexity:** Ruff McCabe max-complexity is configured to 15 in `pyproject.toml` to accommodate slightly more complex async endpoint handling.
- **Tooling:** Development tooling strictly uses `ruff` (including pydocstyle D rules) for linting, `ruff format` for formatting, `mdformat` for Markdown, `pyright` in strict mode, `pytest`, `tox`, and `hypothesis` for verification. `tox.ini` and manual runs are configured to auto-fix linting and formatting issues using `uv run ruff check --fix .` and `uv run ruff format .`. `pre-commit` hooks are required for all changes.
- **Configuration & I/O:** Local configuration files (e.g., JSON files) must be parsed and strictly validated using Pydantic models. File loading operations should be cached (e.g., using `@functools.lru_cache`) to prevent synchronous disk I/O from blocking the FastAPI event loop.

## 3. Web Framework (FastAPI & HTMX)
- **Tech Stack:** FastAPI Python backend, Jinja2 for all templating, `pydantic-settings` for configuration, and an HTMX frontend (minimal CSS framework like Tailwind or PicoCSS).
- **Dependency Management:** Relies exclusively on `uv` using a strict `src`-based layout with a single-source-of-truth `pyproject.toml`.
- **Async Execution:** Avoid blocking the FastAPI event loop with synchronous network or I/O calls. Wrap blocking functions like `socket.gethostbyname` using `asyncio.get_running_loop().run_in_executor(None, func, *args)`.
- **HTMX Form Submissions:** When implementing HTMX forms that trigger long-running processes or file downloads, use the `hx-disabled-elt` attribute (e.g., `hx-disabled-elt="button[type='submit']"`) to disable submit buttons and prevent double-submission bugs.
- **HTMX Downloads:** HTMX `hx-post` requests cannot natively handle binary file downloads. When generating files to download, save the file to disk (e.g., `data/downloads/`) and return an HTML response containing an `<a>` tag with a download link instead of returning a `StreamingResponse`.

## 4. Spite Architecture & Clean-Room Mechanics
- **Clean-Room Enforcement:** Spite enforces a strict architectural boundary. The "Dirty" agent analyzes public repositories to generate 8 spec files. The "Clean" agent implements the codebase, strictly blocked from original sources.
- **Oracle Pattern:** A restricted Q&A channel is permitted during Phase 2. To maintain the clean-room boundary, the Dirty agent class must internally encapsulate and retain the original ingested resources to act as an Oracle, ensuring the Clean agent never handles the raw source directly.
- **LLM Communication:** Relies on a dynamic Q&A loop between Clean and Dirty agents. LLM outputs are expected and parsed as standard Markdown. External service integrations prefer free fallbacks or libraries (e.g., `duckduckgo-search`).
- **Context Management:** Current architecture manages context windows by truncating files and passing context directly to the LLM. Vector databases are not explicitly forbidden but not currently used.
- **Execution Time:** The extraction and analysis phase is computationally intensive and expected to take hours to complete. This must be accounted for in non-functional performance requirements.
- **Tone:** Documentation and system text must strictly maintain a professional tone, avoiding any satirical elements.

## 5. Development & Local Setup
- **Local Models:** Primary AI integration is Ollama. Available models for the application UI are configured in a machine-local `models.json` file. A script `pull_ollama_models.sh` is maintained at the root to download models. Prioritize compact models (e.g., `phi-4-mini-instruct`, `qwopus-3.5-coder-4b`) documented in `MODEL_OPTIONS.md` to fit within local hardware constraints (e.g., GTX 1060 6GB VRAM).
- **Development Setup:** Run `uv sync --all-extras --dev` to install dependencies.
- **Running Locally:** Run the application via `uv run uvicorn spite.main:app --host 127.0.0.1 --port 8000`.

## 6. Delivery Phases Workflow
- **Phase 1:** Generates a `.zip` file with 8 specific files (like `SYSTEM_OVERVIEW.md`), including implementation plans and improvement suggestions.
- **Phase 2:** Produces a fully implemented local Git working directory via the Clean agent.
- **Phase 3:** Produces an enhanced local Git directory that iteratively applies improvements (including API and behavioral changes).
