# Agent Instructions

- The primary function of Spite is to enforce strict clean-room isolation.
- You MUST ensure the `IngestionManager` explicitly drops any implementation files (e.g. `*.py`, `*.js`) and only retains documentation or types (`*.d.ts`, `*.pyi`).
- You MUST follow the Composite Web App guidelines (e.g. use `uv`, no `print` logs).
