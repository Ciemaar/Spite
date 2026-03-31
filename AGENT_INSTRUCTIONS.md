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
- It should only extract and pass: `README.md`, documentation, exported type definitions (e.g., `.d.ts`, `__init__.py` stubs), and public function signatures.
- If you use an LLM to help extract these signatures, that LLM session must be isolated and its output strictly formatted as Markdown specifications.

### 2.2 Implement Delivery Options
You must build two distinct delivery pipelines:
- **Delivery Option 1 (Zip Plan Generation):**
  - The system analyzes the target and generates four key files: `REQUIREMENTS.md`, `TESTING.md`, `IMPLEMENTATION_PLAN.md`, and `AGENT_INSTRUCTIONS.md` (which are instructions for *another* agent to write the code).
  - Package these into a `.zip` file and serve it to the user via the frontend.
- **Delivery Option 2 (Full AI Implementation):**
  - The system performs the analysis above, but then automatically initializes a new local Git repository.
  - It instantiates a fresh, isolated AI session (the "Clean" agent) using the user's selected model (e.g., via Ollama).
  - It feeds the generated specifications to this Clean agent and runs an execution loop to generate the code, write the files, and commit them to the new Git repository.

### 2.3 Frontend Requirements (HTMX)
- Build a clean, professional web interface. Avoid any satirical or "evil" tone; keep it strictly utilitarian and professional.
- Use HTMX for dynamic updates. Specifically, use HTMX Server-Sent Events (SSE) or polling to provide the user with real-time feedback during the long-running analysis and generation phases (e.g., "Fetching repository...", "Analyzing public API...", "Generating requirements...", "Writing code...").
- Include form inputs for:
  - Target GitHub URL.
  - AI Provider Selection (Ollama model dropdown or API Key input field).
  - Delivery Option Toggle (Zip vs. Full Implementation).

## 3. Development Workflow & Rules

1. **Test-Driven Development (TDD):** Where possible, write tests for your core logic before implementing it. Specifically, write robust tests for the GitHub fetching logic and the type/signature extraction logic.
2. **Local AI First:** Always default to and test with Ollama. Assume the user is running Ollama locally on `http://localhost:11434`. Provide clear error messages if Ollama is not reachable or the requested model is not pulled.
3. **Modularity:** Separate the application into clear modules:
   - `ingest.py`: Handling GitHub fetching and filtering.
   - `analyze.py`: The "Dirty" agent logic for generating specifications.
   - `generate.py`: The "Clean" agent logic for executing the specifications (Option 2).
   - `package.py`: Logic for creating the Zip archive (Option 1) and Git repository.
   - `web.py`: The FastAPI/Flask application and HTMX endpoints.
4. **Error Handling:** Gracefully handle GitHub API rate limits, large repositories (implement a reasonable size or file count limit), and LLM timeout/context window errors.
5. **Security:** Do not execute any code fetched from the target repository. The analysis must be purely static.

## 4. Getting Started
To begin, please review the `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md` files in this repository. Start by setting up the Python backend and a basic HTMX skeleton before tackling the complex AI orchestration.

Good luck, and build Spite with precision and care.