# Spite Developer Guide

## Architecture

Spite is built with a strictly `src`-based layout using FastAPI and `uv`.

- `src/spite/ingest.py`: Handles fetching repository trees and strictly filtering for documentation/types.
- `src/spite/analyzer.py`: The "Dirty Agent" that reads context and creates specifications.
- `src/spite/generator.py`: The "Clean Agent" that reads specifications and writes code.
- `src/spite/packager.py`: Handles zip generation and temporary Git repo initialization.

## Unsupported Modules Evaluation

When upgrading or testing new unreleased Python versions (e.g., Python 3.15 release candidates), some modules encounter issues. The alternatives have been evaluated:

- **`pydantic-core` / `pydantic` / `fastapi`**: `pydantic-core` depends heavily on Rust extensions built using `pyo3`. Unreleased Python versions often lack binary wheels and stable PyO3 support (requiring `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`). Since `pydantic` depends on `pydantic-core`, and `fastapi` requires `pydantic`, they all fail if the core extension cannot compile against the new C API.
  - **Alternative**: Replacing `fastapi` would require a complete migration to another framework like Starlette (without Pydantic) or Litestar (which also relies on Pydantic or msgspec and has similar C-extension challenges). Therefore, sticking with `fastapi` and waiting for compatible wheels or building with forward compatibility is the preferred approach.
- **`lxml`**: Required by `duckduckgo-search`. `lxml` does not provide pre-built binary wheels for unreleased Python versions.
  - **Alternative**: Swap `duckduckgo-search` for another search library (like `beautifulsoup4` combined with `httpx`). However, a simpler workaround is to ensure system-level C libraries (`libxml2-dev` and `libxslt1-dev`) are installed in the build environment so `lxml` can compile from source.

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
