# Agent Instructions

- The primary function of Spite is to enforce strict clean-room isolation.
- You MUST ensure the `IngestionManager` explicitly drops any implementation files (e.g. `*.py`, `*.js`) and only retains documentation or types (`*.d.ts`, `*.pyi`).
- You MUST follow the Composite Web App guidelines (e.g. use `uv`, no `print` logs).
- When working on an existing, previous branch (i.e., rebasing or merging), features must not be removed if they've been added to the main branch in the intermediate interval.
- All branches being merged in, as well as their matching PRs, must be referenced in the commit comments and any new PRs.
