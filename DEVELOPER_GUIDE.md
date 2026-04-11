# Spite Developer Guide

## Architecture

Spite is built with a strictly `src`-based layout using FastAPI and `uv`.

- `src/spite/ingest.py`: Handles fetching repository trees and strictly filtering for documentation/types.
- `src/spite/analyzer.py`: The "Dirty Agent" that reads context and creates specifications.
- `src/spite/generator.py`: The "Clean Agent" that reads specifications and writes code.
- `src/spite/packager.py`: Handles zip generation and temporary Git repo initialization.

## Testing

Run tests using `uv run tox` or `uv run pytest`.
