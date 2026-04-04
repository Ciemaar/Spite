# Spite Testing Strategy

This document outlines the testing approach for the Spite clean-room implementation tool. Testing is crucial to ensure that the "Dirty" and "Clean" agents remain isolated, that public interfaces are accurately extracted, and that the two delivery options function correctly.

## 1. Unit Tests

### 1.1 Ingestion & Filtering (`test_ingest.py`)
- **Target:** The module responsible for fetching from GitHub and filtering files.
- **Tests:**
  - Mock the GitHub API response to simulate a repository with a mix of source code (e.g., `main.py`, `utils.ts`), documentation (`README.md`, `CONTRIBUTING.md`), and type definitions (`index.d.ts`, `__init__.pyi`).
  - **Assert:** The filtering function strictly retains only documentation and type definitions, and entirely discards implementation source files.
  - Test rate limit handling and error reporting for non-existent repositories.

### 1.2 Analysis & Specification Generation (`test_analyze.py`)
- **Target:** The "Dirty" agent logic that generates the `REQUIREMENTS.md`, `TESTING.md`, etc.
- **Tests:**
  - Mock the LLM provider (Ollama/OpenAI/Anthropic) to return a predefined, well-formatted Markdown string containing the four required sections.
  - **Assert:** The parser correctly splits the LLM output into the four distinct specification files.
  - Test handling of malformed LLM responses (e.g., missing sections, invalid Markdown) with appropriate retries or error messages.

### 1.3 Zip Packaging (`test_package_zip.py`)
- **Target:** The logic for Delivery Option 1 (Zip generation).
- **Tests:**
  - Provide a dictionary of dummy Markdown strings (representing the specs).
  - **Assert:** The function creates a valid `.zip` file in memory or a temp directory containing exactly four files with the correct names (`REQUIREMENTS.md`, `TESTING.md`, `IMPLEMENTATION_PLAN.md`, `AGENT_INSTRUCTIONS.md`) and content.

### 1.4 Git Repository Initialization (`test_package_git.py`)
- **Target:** The setup phase for Delivery Option 2.
- **Tests:**
  - Provide a target directory path.
  - **Assert:** The function successfully calls `git init`, creates an initial empty commit (optional), and the directory is a valid Git repository.

## 2. Integration Tests

### 2.1 Full Delivery Option 1 Pipeline (Zip Generation)
- **Goal:** Verify the end-to-end flow from receiving a GitHub URL to producing the Zip file, *without* relying on a live LLM.
- **Setup:** Use a mocked GitHub client and a mocked LLM client.
- **Execution:** Trigger the main application core logic for Option 1, simulating UI signals.
- **Assert:** The core logic emits the expected completion signal and provides the valid `.zip` payload ready for saving.

### 2.2 Full Delivery Option 2 Pipeline (Git Generation)
- **Goal:** Verify the end-to-end flow of generating the code and committing it to a local Git repository, *without* relying on a live LLM.
- **Setup:** Use a mocked GitHub client and a mocked LLM client for *both* the "Dirty" and "Clean" agents.
- **Execution:** Trigger the main application core logic for Option 2, simulating UI signals.
- **Assert:**
  - The "Clean" agent mock is called with the output of the "Dirty" agent mock.
  - A new local directory is created.
  - The mocked generated code files are written to this directory.
  - The directory is a valid Git repository with a commit containing the new files.
  - The core logic emits the expected success signal containing the path to this directory.

## 3. Desktop UI Tests

### 3.1 GUI Component Validation (`test_ui.py`)
- **Target:** The GUI classes and layout logic.
- **Tests:**
  - **Instantiation:** Assert the main window initializes without errors and contains the expected widgets (URL input, AI provider select, Delivery toggle).
  - **Action Triggering:** Simulate clicking the submit button. Assert it emits the correct signal with the current values of the input fields and properly disables UI elements to prevent double submission.
  - **Signal Handling:** Test that the UI responds correctly to mocked signals from background threads (e.g., updating progress bars, showing error dialogs, or showing the file save dialog upon success).

## 4. Manual "Clean-Room" Verification (The Real Test)

Because Spite's core value is legal and architectural isolation, automated tests cannot fully prove the "clean room" guarantee. A manual verification process is required:

1. **Select a Target:** Choose a small, open-source library with clear documentation and a specific license (e.g., a simple string manipulation library in Python).
2. **Run Option 1:** Use Spite to generate the Zip file of specifications.
3. **Audit Specs:** Manually review the `REQUIREMENTS.md` and `IMPLEMENTATION_PLAN.md`. Verify that they contain *no copied source code* or implementation-specific logic from the original library, only interface descriptions and behavioral requirements.
4. **Run Option 2:** Use Spite (with a real local Ollama model) to fully recreate the library.
5. **Audit Code:** Manually review the generated codebase. Compare it to the original library. Ensure it is functionally equivalent (write a quick script to test both libraries against the same inputs) but structurally distinct.
6. **Verify Git History:** Check the generated Git repository to ensure only the newly created code is present in the history, with no traces of the original target's repository.