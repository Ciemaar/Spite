# Spite Implementation Plan

This document breaks down the development of Spite into actionable, sequential steps for an AI agent or human developer.

## Phase 1: Project Setup and Foundational Architecture

1. **Initialize Project:** Create a standard Python virtual environment (or use Poetry/uv). Install core dependencies: `fastapi` (or `flask`), `uvicorn`, `httpx` (for GitHub API), and any chosen LLM interface library (e.g., `ollama` python package, `openai`).
1. **Directory Structure:** Set up directories for `src/` (backend logic), `templates/` (HTML/HTMX), `static/` (CSS/JS), and `tests/`.
1. **Basic UI Skeleton:** Create a base HTML template with HTMX included (via CDN) and a minimal CSS framework (like Tailwind or PicoCSS). Implement a simple form with:
   - Input for GitHub URL.
   - Text area/input for supplemental URLs (public documentation, discussion forums) and a checkbox to enable automated web search (enabled by default).
   - Dropdown/Input for AI Provider (Ollama model selection or API Key).
   - Radio buttons/Dropdown for Target Phase (Phase 1: Zip, Phase 2: Full Repo, Phase 3: Enhanced Repo).
1. **FastAPI Routes:** Create the basic routes to serve the UI and handle form submissions via HTMX.

## Phase 2: Ingestion and "Dirty" Analysis

1. **GitHub Ingestion Module (`src/ingest.py`):**
   - Implement a function to take a GitHub URL, parse the owner/repo, and use the GitHub REST API (via `httpx`) to fetch the repository tree.
   - Update ingestion logic to also fetch content from provided supplemental URLs and via automated web search (if enabled) to gather public documentation and discussion forum context. The search should include explicit queries for documentation hosted on platforms like GitHub Pages and Read the Docs.
   - **Crucial Filtering:** Implement logic to *strictly* filter the file list. Only download files matching documentation (`README.md`, `*.md`, `*.rst`, `*.html`) or type definitions (`*.d.ts`, `__init__.pyi`, etc.). *Never* download implementation source files (`*.py`, `*.js`, `*.go` unless they are explicitly type stubs). Incorporate fetched supplemental content as valid contextual input.
1. **LLM Interface (`src/llm.py`):**
   - Create a uniform interface to interact with Ollama (primary) and cloud providers (secondary).
   - Implement error handling for connection issues, rate limits, and context window exhaustion.
1. **The "Dirty" Agent (`src/analyzer.py`):**
   - Construct a prompt that feeds the filtered documentation/types to the LLM, as well as any fetched public documentation and discussion forum context. The prompt must instruct the LLM to act as a clean-room specification writer.
   - The prompt must mandate outputting exactly eight sections (or distinct JSON keys): Requirements, Testing Strategy, Implementation Plan, Agent Instructions, Improvements (opportunities for improvement based on usage and features, e.g., behavioral changes), a Dirty Bibliography (links and commentary on sources considered), a System Overview (original descriptions and a proposed replacement name), and Source Excludes (a list of known original sources/URLs to avoid).
   - Implement logic to parse this response into eight distinct files (including `IMPROVEMENTS.md`, `DIRTY_BIBLIOGRAPHY.md`, `SYSTEM_OVERVIEW.md`, and `SOURCE_EXCLUDES.txt`).

## Phase 3: Delivery Mechanism 1 (Phase 1 - Zip Generation)

1. **Packaging Module (`src/packager.py`):**
   - Implement a function `create_zip_payload(specs_dict)`. It should take the eight distinct files from the Analyzer and create an in-memory `.zip` file (using Python's `zipfile` module).
1. **API Integration:**
   - Update the FastAPI route handling the form submission. If "Phase 1" is the target, trigger the Ingest -> Analyze -> Package pipeline.
   - Return the generated `.zip` file to the user as a downloadable response, alongside a UI button to "Proceed to Phase 2".
   - *UX Improvement:* Use HTMX to show a loading spinner or progress text ("Analyzing repository...") while this backend process runs.

## Phase 4: Delivery Mechanism 2 (Phase 2 - Full AI Implementation)

1. **Git Initialization:**
   - In `src/packager.py`, add a function `init_local_repo()`. This should create a new temporary directory on the local filesystem and run `git init`.
1. **The "Clean" Agent (`src/generator.py`):**
   - Instantiate a *new, fresh* LLM session. Do not pass any context from the "Dirty" agent other than the generated Markdown specifications.
   - Explicitly configure the LLM session with a blocklist built from `SOURCE_EXCLUDES.txt` to strictly prevent it from querying, browsing, or referencing the original source code or repository.
   - Construct a prompt instructing the LLM to act as the implementing developer. Provide it with the generated `IMPLEMENTATION_PLAN.md` and `REQUIREMENTS.md`.
   - Establish a messaging interface between the Clean and Dirty agents. Instruct the Dirty agent to only answer questions pertaining to public/observable behavior (rejecting any implementation detail queries), and instruct the Clean agent to only ask such questions.
   - Implement an agentic loop (if necessary) or a single-shot generation if the task is simple enough, asking the LLM to output file paths and corresponding file contents.
   - Ensure the Clean agent is instructed to generate a `CLEAN_BIBLIOGRAPHY.md` file detailing the sources and specs it considered during implementation.
   - The backend must log all Q&A interactions between the agents and generate a `CLEAN_DIRTY_QA_LOG.md` file.
1. **Execution & Committing:**
   - Parse the LLM's code output.
   - Write the generated files (including `CLEAN_DIRTY_QA_LOG.md`) to the newly initialized Git directory.
   - Run `git add .` and `git commit -m "Initial clean-room implementation"`.
1. **API Integration:**
   - Update the FastAPI route. If "Phase 2" is the target, ensure Phase 1 is complete, then trigger: Generate Code -> Commit.
   - Return an HTMX response displaying the local path to the generated Git repository, indicating success, alongside a UI button to "Proceed to Phase 3".

## Phase 5: Delivery Mechanism 3 (Phase 3 - AI Enhancement)

1. **Enhancement Loop (`src/generator.py`):**
   - After Phase 4 completes, if "Phase 3" is the target, supply the Clean Agent with the generated `IMPROVEMENTS.md`.
   - Instruct the LLM to iteratively apply the improvements to the newly generated codebase, making API or functionality changes as required.
   - Instruct the Clean agent to update the `CLEAN_BIBLIOGRAPHY.md` with any new sources or considerations.
   - Run tests (or ask the LLM to update the tests) and commit the changes as subsequent commits to the same Git repository.
1. **API Integration:**
   - Update the FastAPI route. If "Phase 3" is triggered, run the final pipeline: Apply Improvements -> Commit.
   - Return an HTMX response displaying the local path to the generated, enhanced Git repository.

## Phase 6: Refinement and Testing

1. **Testing:** Execute the unit and integration tests defined in `TESTING.md`. Ensure the strict filtering in Phase 2 holds up.
1. **UX Polish:** Enhance the HTMX interactions. Implement Server-Sent Events (SSE) to stream progress updates (e.g., "Fetching from GitHub...", "Analyzing public API...", "Generating specifications...", "Writing code...", "Applying improvements...").
1. **Documentation:** Finalize the project's own `README.md` explaining how to install, run, and use Spite.
