# Spite Implementation Plan

This document breaks down the development of Spite into actionable, sequential steps for an AI agent or human developer.

## Phase 1: Project Setup and Foundational Architecture
1. **Initialize Project:** Create a standard Python virtual environment (or use Poetry/uv). Install core dependencies: `fastapi` (or `flask`), `uvicorn`, `httpx` (for GitHub API), and any chosen LLM interface library (e.g., `ollama` python package, `openai`).
2. **Directory Structure:** Set up directories for `src/` (backend logic), `templates/` (HTML/HTMX), `static/` (CSS/JS), and `tests/`.
3. **Basic UI Skeleton:** Create a base HTML template with HTMX included (via CDN) and a minimal CSS framework (like Tailwind or PicoCSS). Implement a simple form with:
   - Input for GitHub URL.
   - Text area/input for supplemental URLs (public documentation, discussion forums) and a checkbox to enable automated web search (enabled by default).
   - Dropdown/Input for AI Provider (Ollama model selection or API Key).
   - Radio buttons/Toggle for Delivery Option (Zip vs. Full Repo).
4. **FastAPI Routes:** Create the basic routes to serve the UI and handle form submissions via HTMX.

## Phase 2: Ingestion and "Dirty" Analysis
1. **GitHub Ingestion Module (`src/ingest.py`):**
   - Implement a function to take a GitHub URL, parse the owner/repo, and use the GitHub REST API (via `httpx`) to fetch the repository tree.
   - Update ingestion logic to also fetch content from provided supplemental URLs and via automated web search (if enabled) to gather public documentation and discussion forum context.
   - **Crucial Filtering:** Implement logic to *strictly* filter the file list. Only download files matching documentation (`README.md`, `*.md`, `*.rst`, `*.html`) or type definitions (`*.d.ts`, `__init__.pyi`, etc.). *Never* download implementation source files (`*.py`, `*.js`, `*.go` unless they are explicitly type stubs). Incorporate fetched supplemental content as valid contextual input.
2. **LLM Interface (`src/llm.py`):**
   - Create a uniform interface to interact with Ollama (primary) and cloud providers (secondary).
   - Implement error handling for connection issues, rate limits, and context window exhaustion.
3. **The "Dirty" Agent (`src/analyzer.py`):**
   - Construct a prompt that feeds the filtered documentation/types to the LLM, as well as any fetched public documentation and discussion forum context. The prompt must instruct the LLM to act as a clean-room specification writer.
   - The prompt must mandate outputting exactly five sections (or distinct JSON keys): Requirements, Testing Strategy, Implementation Plan, Agent Instructions, and Improvements (opportunities for improvement based on usage and features, e.g., behavioral changes).
   - Implement logic to parse this response into five distinct Markdown strings (including `IMPROVEMENTS.md`).

## Phase 3: Delivery Option 1 (Zip Generation)
1. **Packaging Module (`src/packager.py`):**
   - Implement a function `create_zip_payload(specs_dict)`. It should take the five Markdown strings from the Analyzer and create an in-memory `.zip` file (using Python's `zipfile` module).
2. **API Integration:**
   - Update the FastAPI route handling the form submission. If "Option 1" is selected, trigger the Ingest -> Analyze -> Package pipeline.
   - Return the generated `.zip` file to the user as a downloadable response.
   - *UX Improvement:* Use HTMX to show a loading spinner or progress text ("Analyzing repository...") while this backend process runs.

## Phase 4: Delivery Option 2 (Full AI Implementation)
1. **Git Initialization:**
   - In `src/packager.py`, add a function `init_local_repo()`. This should create a new temporary directory on the local filesystem and run `git init`.
2. **The "Clean" Agent (`src/generator.py`):**
   - Instantiate a *new, fresh* LLM session. Do not pass any context from the "Dirty" agent other than the generated Markdown specifications.
   - Construct a prompt instructing the LLM to act as the implementing developer. Provide it with the generated `IMPLEMENTATION_PLAN.md` and `REQUIREMENTS.md`.
   - Implement an agentic loop (if necessary) or a single-shot generation if the task is simple enough, asking the LLM to output file paths and corresponding file contents.
3. **Execution & Committing:**
   - Parse the LLM's code output.
   - Write the generated files to the newly initialized Git directory.
   - Run `git add .` and `git commit -m "Initial clean-room implementation"`.
4. **API Integration:**
   - Update the FastAPI route. If "Option 2" is selected, run the full pipeline: Ingest -> Analyze -> Generate Code -> Commit.
   - Return an HTMX response displaying the local path to the generated Git repository, indicating success.

## Phase 5: Refinement and Testing
1. **Testing:** Execute the unit and integration tests defined in `TESTING.md`. Ensure the strict filtering in Phase 2 holds up.
2. **UX Polish:** Enhance the HTMX interactions. Implement Server-Sent Events (SSE) to stream progress updates (e.g., "Fetching from GitHub...", "Analyzing public API...", "Generating specifications...", "Writing code...").
3. **Documentation:** Finalize the project's own `README.md` explaining how to install, run, and use Spite.