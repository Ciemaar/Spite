# Spite: Agent Instructions

You are an expert software engineer tasked with implementing "Spite", a clean-room software recreation tool. This application allows users to point to a GitHub repository and generate either a set of specifications (for manual implementation) or a fully rewritten, functional clone using local AI models (Ollama).

Please strictly adhere to the following guidelines and instructions as you implement Spite.

## 1. Project Context

- **Name:** Spite
- **Purpose:** Provide a legal "clean room" recreation of open-source dependencies by analyzing only public interfaces and generating a new implementation from scratch using AI.
- **Tech Stack:**
  - Backend: Python (FastAPI or Flask recommended for HTMX support).
  - Frontend: HTMX with a minimal CSS framework (Tailwind CSS or similar).
  - AI Integration: Local Ollama (Primary) and user-provided API keys (OpenAI/Anthropic).

## 2. Core Implementation Directives

### 2.1 Enforce the Clean Room (Crucial)

You must implement a strict architectural boundary between the "Dirty" and "Clean" phases.

- The module that fetches and analyzes the target repository (the "Dirty" side) must **never** pass source code implementation details to the specification generator.
- It should only extract and pass: `README.md`, documentation, exported type definitions (e.g., `.d.ts`, `__init__.py` stubs), public function signatures, as well as context gathered from external public documentation and discussion forums.
- If you use an LLM to help extract these signatures, that LLM session must be isolated and its output strictly formatted as Markdown specifications.
- **Critical Configuration:** The Clean agent MUST be explicitly configured with an exclude blocklist (using `SOURCE_EXCLUDES.txt` output from the Dirty agent) to strictly forbid it from searching, querying, or referencing the original source code or repository.
- **Restricted Communication:** A restricted Q&A channel is permitted during implementation. The Dirty agent must act as a behavioral oracle, and the Clean agent must act as a blind implementer. Both must strictly adhere to an "observable behavior only" constraint. All interactions must be logged.

### 2.2 Implement Delivery Phases

You must build three distinct delivery phases and support a workflow that allows the user to progress through them sequentially:

- **Phase 1 (Zip Plan Generation):**
  - The system analyzes the target and generates eight key files: `REQUIREMENTS.md`, `TESTING.md`, `IMPLEMENTATION_PLAN.md`, `AGENT_INSTRUCTIONS.md` (which are instructions for *another* agent to write the code), `IMPROVEMENTS.md` (capturing opportunities for improvement based on usage and features), `DIRTY_BIBLIOGRAPHY.md` (links and commentary on sources considered by the analysis agent), `SYSTEM_OVERVIEW.md` (original 1-sentence, 1-paragraph, and 1-page descriptions of the system alongside a proposed replacement name), and `SOURCE_EXCLUDES.txt` (a blocklist of known original sources and URLs).
  - Package these into a `.zip` file and serve it to the user via the frontend, offering a UI prompt to proceed to Phase 2.
- **Phase 2 (Full AI Implementation):**
  - The system performs the analysis above (or takes the output if Phase 1 was already completed), but then automatically initializes a new local Git repository.
  - It instantiates a fresh, isolated AI session (the "Clean" agent) using the user's selected model (e.g., via Ollama).
  - The system MUST configure the Clean agent using the `SOURCE_EXCLUDES.txt` blocklist to enforce absolute separation.
  - It feeds the generated specifications to this Clean agent and runs an execution loop to generate the code, write the files, and commit them to the new Git repository. Ensure the Clean agent explicitly states it has not accessed original sources and generates a `CLEAN_BIBLIOGRAPHY.md` file detailing the valid specifications and sources it used during implementation.
  - The execution loop must log any questions asked of the Dirty agent and save them to `CLEAN_DIRTY_QA_LOG.md`, committing this alongside the code.
  - Serve the resulting path to the user, offering a UI prompt to proceed to Phase 3.
- **Phase 3 (AI Autonomous Recreation & Enhancement):**
  - After completing Phase 2, the Clean agent is supplied with the generated `IMPROVEMENTS.md`.
  - It performs a secondary execution loop to aggressively apply these improvements to the codebase, which may include making breaking changes to the original API or functionality.
  - It updates `CLEAN_BIBLIOGRAPHY.md` and commits these enhancements to the local Git repository.

### 2.3 Frontend Requirements (HTMX)

- Build a clean, professional web interface. Avoid any satirical or "evil" tone; keep it strictly utilitarian and professional.
- Use HTMX for dynamic updates. Specifically, use HTMX Server-Sent Events (SSE) or polling to provide the user with real-time feedback during the long-running analysis and generation phases (e.g., "Fetching repository...", "Analyzing public API...", "Generating requirements...", "Writing code...", "Applying improvements...").
- Include form inputs for:
  - Target GitHub URL.
  - Supplemental URLs (for public documentation, discussion forums) and a checkbox to enable automated web search (enabled by default).
  - AI Provider Selection (Ollama model dropdown or API Key input field).
  - Target Phase Selector (Phase 1: Zip, Phase 2: Full Repo, Phase 3: Enhanced Repo), designed to support sequential progression between phases.

## 3. Development Workflow & Rules

1. **Test-Driven Development (TDD):** Where possible, write tests for your core logic before implementing it. Specifically, write robust tests for the GitHub fetching logic and the type/signature extraction logic.
1. **Local AI First:** Always default to and test with Ollama. Assume the user is running Ollama locally on `http://localhost:11434`. Provide clear error messages if Ollama is not reachable or the requested model is not pulled.
1. **Modularity:** Separate the application into clear modules:
   - `ingest.py`: Handling GitHub fetching and filtering.
   - `analyze.py`: The "Dirty" agent logic for generating specifications.
   - `generate.py`: The "Clean" agent logic for executing the specifications (Phase 2 & 3).
   - `package.py`: Logic for creating the Zip archive (Phase 1) and Git repository.
   - `web.py`: The FastAPI/Flask application and HTMX endpoints.
1. **Error Handling:** Gracefully handle GitHub API rate limits, large repositories (implement a reasonable size or file count limit), and LLM timeout/context window errors.
1. **Security:** Do not execute any code fetched from the target repository. The analysis must be purely static.

## 4. Getting Started

To begin, please review the `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md` files in this repository. Start by setting up the Python backend and a basic HTMX skeleton before tackling the complex AI orchestration.

Good luck, and build Spite with precision and care.
