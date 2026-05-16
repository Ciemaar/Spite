# Spite Implementation Plan

1. Setup `uv` project, add dependencies (`fastapi`, `ollama`, `duckduckgo-search`).
1. Implement FastAPI backend with Jinja2/HTMX templates for the UI.
1. Implement `IngestionManager` to fetch/filter GitHub repos.
1. Implement `DirtyAgent` to analyze docs and output 8 spec files.
1. Implement `CleanAgent` to parse specs, ask behavioral questions, and write code.
1. Package phase 1 outputs into zip, phase 2/3 into local git repos.
