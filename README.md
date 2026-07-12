# Spite

Spite is a clean-room software recreation tool. It takes a GitHub repository and public documentation, analyzes them using a "Dirty Agent" to produce clean-room specifications, and then uses a "Clean Agent" (blocked from original source) to re-implement the repository autonomously.

## Features

- **Phase 1:** Generates 8 distinct specification files from a target repository (REQUIREMENTS, IMPLEMENTATION_PLAN, TESTING, etc.).
- **Phase 2:** Automatically generates the codebase entirely from the specifications. The Clean Agent cannot see original source, but can ask the Dirty Agent questions about observable behavior.
- **Phase 3:** Enhances the generated codebase by applying an AI-generated improvements pass.

## Running Locally

1. Ensure `uv` is installed.
1. Install dependencies: `uv sync`
1. Run the development server: `uv run uvicorn spite.main:app --reload`
1. Make sure you have Ollama running locally.
