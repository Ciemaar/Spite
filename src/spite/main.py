import logging
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict
from spite.stream import ProgressStream  # pyright: ignore

# Global dict to store active streams (in a real app, use Redis/pubsub)
# For simplicity in this agentic implementation, we use a simple dict mapping to a stream.
# We'll just have a single global stream for the simple case.
global_stream = ProgressStream()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Application settings loaded via pydantic-settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ollama_host: str = "http://localhost:11434"

settings = Settings()

app = FastAPI(title="Spite")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Ensure static dir exists
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main index page."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/stream")
async def stream_events():
    """SSE endpoint for streaming progress updates."""
    return StreamingResponse(global_stream.get_stream(), media_type="text/event-stream")


@app.post("/process")
async def process(
    github_url: Annotated[str, Form()],
    ai_provider: Annotated[str, Form()],
    ai_model: Annotated[str, Form()],
    target_phase: Annotated[str, Form()],
    supplemental_urls: Annotated[str, Form()] = "",
    web_search: Annotated[bool, Form()] = False,
) -> StreamingResponse | HTMLResponse:
    """Handle the main form submission via HTMX."""
    logger.info(
        f"Processing repo: {github_url}, phase: {target_phase}, model: {ai_model}"
    )

    from .analyzer import DirtyAgent
    from .ingest import IngestionManager
    from .llm import LLMInterface
    from .packager import create_zip_payload

    # Setup
    ingestor = IngestionManager()
    llm = LLMInterface(host=settings.ollama_host, model=ai_model)
    dirty_agent = DirtyAgent(llm=llm)

    try:
        await global_stream.add_message("<div>Starting ingestion...</div>")
        # Ingestion
        repo_files = await ingestor.ingest_github_repo(github_url)

        urls_to_fetch = [u.strip() for u in supplemental_urls.split(",") if u.strip()]
        supplemental_content = await ingestor.fetch_urls(urls_to_fetch)

        search_context = ""
        if web_search:
            search_context = ingestor.search_web(f"{github_url} documentation")

        await global_stream.add_message("<div>Analyzing codebase and generating specifications...</div>")
        # Analysis
        specs = await dirty_agent.analyze(
            repo_files, supplemental_content, search_context
        )

        # Packaging
        if target_phase == "1":
            zip_buffer = create_zip_payload(specs)
            return StreamingResponse(
                zip_buffer,
                media_type="application/x-zip-compressed",
                headers={"Content-Disposition": "attachment; filename=spite_specs.zip"}
            )

        # Phase 2 implementation
        await global_stream.add_message("<div>Starting clean-room implementation...</div>")
        import subprocess

        from .generator import CleanAgent
        from .packager import init_local_repo

        repo_path = init_local_repo()
        clean_agent = CleanAgent(llm=llm, dirty_llm=llm)

        await clean_agent.generate_codebase(specs, repo_path)

        # Commit Phase 2
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Spite", "-c", "user.email=spite@localhost", "commit", "-m", "Initial clean-room implementation"],
            cwd=repo_path, check=True
        )

        if target_phase == "2":
            return HTMLResponse(f"""
            <article>
                <header>Phase 2 Complete</header>
                <p>Repository implemented at: <code>{repo_path}</code></p>
            </article>
            """)

        # Phase 3 implementation
        await global_stream.add_message("<div>Applying AI enhancements...</div>")
        await clean_agent.apply_improvements(specs, repo_path)

        # Commit Phase 3
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Spite", "-c", "user.email=spite@localhost", "commit", "-m", "Applied AI enhancements"],
            cwd=repo_path, check=True
        )

        return HTMLResponse(f"""
        <article>
            <header>Phase 3 Complete</header>
            <p>Enhanced repository available at: <code>{repo_path}</code></p>
        </article>
        """)

    except Exception as e:
        logger.exception("Error processing request")
        return HTMLResponse(f"<article>Error: {str(e)}</article>", status_code=500)
    finally:
        await ingestor.close()
