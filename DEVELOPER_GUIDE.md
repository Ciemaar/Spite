# Spite Developer Guide

## Architecture

Spite is built with a strictly `src`-based layout using FastAPI and `uv`.

- `src/spite/ingest.py`: Handles fetching repository trees and strictly filtering for documentation/types.
- `src/spite/analyzer.py`: The "Dirty Agent" that reads context and creates specifications.
- `src/spite/generator.py`: The "Clean Agent" that reads specifications and writes code.
- `src/spite/packager.py`: Handles zip generation and temporary Git repo initialization.

## Testing

Spite relies on `pytest` for unit/integration testing and `tox` for automated environment isolation and testing.

To get started and run the test suite locally during development:

1. Install the development dependencies, which include the testing tools:
   ```bash
   uv sync --all-extras --dev
   ```
1. You can run the entire test suite, alongside `ruff` linting and `pyright` type-checking, by using `tox`:
   ```bash
   uv run tox
   ```
1. Alternatively, for a faster iterative loop, you can run `pytest` directly:
   ```bash
   uv run pytest
   ```

## Running E2E Tests (Unmocked)

To run a full end-to-end integration test against the real GitHub API and your local Ollama instance without any mocks, ensure Ollama is running and run the following command:

```bash
SPITE_RUN_REAL_E2E=1 uv run pytest tests/test_e2e_real.py -s -v
```

This will target `https://github.com/octocat/Hello-World` and attempt to do a complete Phase 2 code generation. Note that this test may take several minutes to run, depending on your hardware and LLM model size.

## Version Control Guidelines

When working with branches and pull requests, please adhere to the following rules:

- When working on an existing, previous branch (i.e., rebasing or merging), features must not be removed if they've been added to the main branch in the intermediate interval.
- All branches being merged in, as well as their matching PRs, must be referenced in the commit comments and any new PRs.
