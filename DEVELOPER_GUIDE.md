# Spite Developer Guide

## Architecture

Spite is built with a strictly `src`-based layout using FastAPI and `uv`.

- `src/spite/ingest.py`: Handles fetching repository trees and strictly filtering for documentation/types.
- `src/spite/analyzer.py`: The "Dirty Agent" that reads context and creates specifications.
- `src/spite/generator.py`: The "Clean Agent" that reads specifications and writes code.
- `src/spite/packager.py`: Handles zip generation and temporary Git repo initialization.

## Testing

Run tests using `uv run tox` or `uv run pytest`.

## Running E2E Tests (Unmocked)

To run a full end-to-end integration test against the real GitHub API and your local Ollama instance without any mocks, ensure Ollama is running and run the following command:

```bash
SPITE_RUN_REAL_E2E=1 uv run pytest tests/test_e2e_real.py -s -v
```

This will target `https://github.com/octocat/Hello-World` and attempt to do a complete Phase 2 code generation. Note that this test may take several minutes to run, depending on your hardware and LLM model size.
