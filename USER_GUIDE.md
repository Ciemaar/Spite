# Spite User Guide

1. Start the application by running `uv run uvicorn spite.main:app`.
1. Open your browser to `http://localhost:8000`.
1. Enter the target GitHub repository URL.
1. (Optional) Provide comma-separated supplementary URLs for context.
1. Select the local Ollama model to use (e.g., `llama3`).
1. Select your target phase:
   - **Phase 1:** Returns a `.zip` file containing specifications.
   - **Phase 2:** Returns a local path to a temporary Git repository containing the re-implemented code.
   - **Phase 3:** Returns a local path to a temporary Git repository containing the re-implemented code *with* AI improvements applied.
