# Spite Testing Strategy

This document outlines the testing approach for the Spite clean-room implementation tool. Testing is crucial to ensure that the "Dirty" and "Clean" agents remain isolated, that public interfaces are accurately extracted, and that the two delivery options function correctly.

## 1. Unit Tests

### 1.1 Ingestion & Filtering (`test_ingest.py`)
- **Target:** The module responsible for fetching from GitHub, filtering files, and fetching supplemental external URLs/web search results.
- **Tests:**
  - Mock the GitHub API response to simulate a repository with a mix of source code (e.g., `main.py`, `utils.ts`), documentation (`README.md`, `CONTRIBUTING.md`), and type definitions (`index.d.ts`, `__init__.pyi`).
  - Mock external HTTP requests or web search results for supplemental URLs.
  - **Assert:** The filtering function strictly retains only documentation, type definitions, and successfully incorporates external fetched context, and entirely discards implementation source files.
  - Test rate limit handling and error reporting for non-existent repositories or unreachable URLs.

### 1.2 Analysis & Specification Generation (`test_analyze.py`)
- **Target:** The "Dirty" agent logic that generates the `REQUIREMENTS.md`, `TESTING.md`, etc.
- **Tests:**
  - Mock the LLM provider (Ollama/OpenAI/Anthropic) to return a predefined, well-formatted Markdown string containing the five required sections.
  - **Assert:** The parser correctly splits the LLM output into the five distinct specification files (including `IMPROVEMENTS.md`).
  - Test handling of malformed LLM responses (e.g., missing sections, invalid Markdown) with appropriate retries or error messages.

### 1.3 Zip Packaging (`test_package_zip.py`)
- **Target:** The logic for Delivery Option 1 (Zip generation).
- **Tests:**
  - Provide a dictionary of dummy Markdown strings (representing the specs).
  - **Assert:** The function creates a valid `.zip` file in memory or a temp directory containing exactly five files with the correct names (`REQUIREMENTS.md`, `TESTING.md`, `IMPLEMENTATION_PLAN.md`, `AGENT_INSTRUCTIONS.md`, `IMPROVEMENTS.md`) and content.

### 1.4 Git Repository Initialization (`test_package_git.py`)
- **Target:** The setup phase for Delivery Option 2.
- **Tests:**
  - Provide a target directory path.
  - **Assert:** The function successfully calls `git init`, creates an initial empty commit (optional), and the directory is a valid Git repository.

## 2. Integration Tests

### 2.1 Full Delivery Option 1 Pipeline (Zip Generation)
- **Goal:** Verify the end-to-end flow from receiving a GitHub URL to producing the Zip file, *without* relying on a live LLM.
- **Setup:** Use a mocked GitHub client and a mocked LLM client.
- **Execution:** Trigger the main Spite API endpoint for Option 1.
- **Assert:** The endpoint returns a `200 OK` and a valid `.zip` file download containing the mocked specifications.

### 2.2 Full Delivery Option 2 Pipeline (Git Generation)
- **Goal:** Verify the end-to-end flow of generating the code and committing it to a local Git repository, *without* relying on a live LLM.
- **Setup:** Use a mocked GitHub client and a mocked LLM client for *both* the "Dirty" and "Clean" agents.
- **Execution:** Trigger the main Spite API endpoint for Option 2.
- **Assert:**
  - The "Clean" agent mock is called with the output of the "Dirty" agent mock.
  - A new local directory is created.
  - The mocked generated code files are written to this directory.
  - The directory is a valid Git repository with a commit containing the new files.
  - The endpoint returns the path to this directory.

### 2.3 Full Delivery Option 3 Pipeline (Enhanced Git Generation)
- **Goal:** Verify the end-to-end flow of generating the code, applying improvements, and committing to a local Git repository, *without* relying on a live LLM.
- **Setup:** Use a mocked GitHub client and a mocked LLM client for *both* the "Dirty" and "Clean" agents.
- **Execution:** Trigger the main Spite API endpoint for Option 3.
- **Assert:**
  - The "Clean" agent mock is called sequentially: first with the spec output, then with the `IMPROVEMENTS.md` output.
  - A new local directory is created and initial code is written and committed.
  - The mocked enhanced code files are written to the directory, resulting in subsequent commits.
  - The endpoint returns the path to this directory.

## 3. Web UI (HTMX) Tests

### 3.1 Endpoint Validation (`test_web.py`)
- **Target:** The FastAPI/Flask routes serving the HTMX frontend.
- **Tests:**
  - **GET `/`:** Assert it returns a 200 status code and contains the expected HTML form elements (URL input, supplemental URL input, AI provider select, Delivery option selector including Option 3).
  - **POST `/analyze` (HTMX submission):** Assert it returns the appropriate HTML fragment (e.g., a progress indicator or the next step in the UI) and starts the backend job.
  - **SSE/Polling Endpoints:** Test that the endpoint responsible for streaming progress updates correctly yields Server-Sent Events or returns the expected JSON state.

## 4. Manual "Clean-Room" Verification (The Real Test)

Because Spite's core value is legal and architectural isolation, automated tests cannot fully prove the "clean room" guarantee. A manual verification process is required:

1. **Select a Target:** Choose a small, open-source library with clear documentation and a specific license (e.g., a simple string manipulation library in Python).
2. **Run Option 1:** Use Spite to generate the Zip file of specifications.
3. **Audit Specs:** Manually review the `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md`. Verify that they contain *no copied source code* or implementation-specific logic from the original library, only interface descriptions and behavioral requirements.
4. **Run Option 2:** Use Spite (with a real local Ollama model) to fully recreate the library.
5. **Audit Code:** Manually review the generated codebase. Compare it to the original library. Ensure it is functionally equivalent (write a quick script to test both libraries against the same inputs) but structurally distinct.
6. **Verify Git History:** Check the generated Git repository to ensure only the newly created code is present in the history, with no traces of the original target's repository.
7. **Run Option 3:** Run the system using Option 3 and perform the same audit, ensuring that the generated `IMPROVEMENTS.md` have been effectively implemented into the new codebase and history accurately reflects these enhancement commits.