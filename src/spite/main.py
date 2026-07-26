import functools
import json
import logging
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from spite.stream import ProgressStream  # type: ignore

# Global dict to store active streams (in a real app, use Redis/pubsub)
global_streams: dict[str, ProgressStream] = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded via pydantic-settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ollama_host: str = "http://localhost:11434"
    max_qa_turns: int = 3
    models_config_path: str = "models.json"


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


class ModelOption(BaseModel):
    """Configuration for a single AI model."""

    id: str
    name: str
    description: str


class ModelsConfig(BaseModel):
    """Configuration schema for available AI models."""

    default_model: str
    models: list[ModelOption]


@functools.lru_cache(maxsize=1)
def load_models_config() -> ModelsConfig:
    """Load and cache the models configuration from the JSON file."""
    config_path = Path(settings.models_config_path)
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
                return ModelsConfig.model_validate(data)
        except Exception as e:
            logger.error(f"Error loading or validating models config: {e}")

    # Fallback default configuration
    return ModelsConfig(
        default_model="llama3",
        models=[ModelOption(id="llama3", name="Llama 3 (8B)", description="")]
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main index page."""
    models_config = load_models_config()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"models_config": models_config}
    )


@app.get("/stream/{client_id}")
async def stream_events(client_id: str):
    """SSE endpoint for streaming progress updates."""
    if client_id not in global_streams:
        global_streams[client_id] = ProgressStream()
    return StreamingResponse(global_streams[client_id].get_stream(), media_type="text/event-stream")



@app.get("/download/{download_id}")
async def download_specs(download_id: str):
    """Download the generated specs zip file."""
    base_dir = Path("data/downloads").resolve()
    download_path = (Path("data/downloads") / f"{download_id}.zip").resolve()
    if not download_path.is_relative_to(base_dir):
        return HTMLResponse("Invalid download ID", status_code=400)

    if not download_path.exists():
        return HTMLResponse("File not found", status_code=404)
    return FileResponse(
        path=download_path,
        media_type="application/x-zip-compressed",
        filename="spite_specs.zip"
    )

@app.post("/process", response_model=None)
async def process(
    github_url: Annotated[str, Form()],
    ai_provider: Annotated[str, Form()],
    ai_model: Annotated[str, Form()],
    target_phase: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    supplemental_urls: Annotated[str, Form()] = "",
    web_search: Annotated[bool, Form()] = False,
    additional_instructions: Annotated[str, Form()] = "",
) -> StreamingResponse | HTMLResponse:
    """Handle the main form submission via HTMX."""
    logger.info(
        f"Processing repo: {github_url}, phase: {target_phase}, model: {ai_model}, client: {client_id}"
    )
    if client_id not in global_streams:
        global_streams[client_id] = ProgressStream()
    stream = global_streams[client_id]

    from .analyzer import DirtyAgent
    from .ingest import IngestionManager
    from .llm import LLMInterface
    from .packager import create_zip_payload

    # Setup
    ingestor = IngestionManager()
    llm = LLMInterface(host=settings.ollama_host, model=ai_model)
    dirty_agent = DirtyAgent(llm=llm)

    try:
        await stream.add_message("<div>Starting ingestion...</div>")
        # Ingestion
        repo_files = await ingestor.ingest_github_repo(github_url)

        urls_to_fetch = [u.strip() for u in supplemental_urls.split(",") if u.strip()]
        supplemental_content = await ingestor.fetch_urls(urls_to_fetch)

        search_context = ""
        if web_search:
            search_context = ingestor.search_web(f"{github_url} documentation")

        await stream.add_message(
            "<div>Analyzing codebase and generating specifications...</div>"
        )
        # Analysis
        specs = await dirty_agent.analyze(
            repo_files, supplemental_content, search_context
        )

        # Inject additional instructions
        if additional_instructions.strip():
            if "AGENTS.md" in specs:
                specs["AGENTS.md"] += (
                    "\n\n## Additional Instructions\n\n"
                    + additional_instructions.strip()
                )
            else:
                specs["AGENTS.md"] = (
                    "# Agent Instructions\n\n## Additional Instructions\n\n"
                    + additional_instructions.strip()
                )

        # Packaging
        if target_phase == "1":
            zip_buffer = create_zip_payload(specs)
            import uuid
            download_id = str(uuid.uuid4())
            download_dir = Path("data/downloads")
            download_dir.mkdir(parents=True, exist_ok=True)
            download_path = download_dir / f"{download_id}.zip"
            with open(download_path, "wb") as f:
                f.write(zip_buffer.getvalue())

            return HTMLResponse(f"""
            <article>
                <header>Phase 1 Complete</header>
                <p>Specifications have been generated.</p>
                <a href="/download/{download_id}" role="button" class="secondary" download="spite_specs.zip">Download .zip</a>

                <hr>
                <form hx-post="/process_phase2" hx-target="#result" hx-indicator="#spinner" hx-disabled-elt="button[type='submit']">
                    <input type="hidden" name="github_url" value="{github_url}">
                    <input type="hidden" name="ai_provider" value="{ai_provider}">
                    <input type="hidden" name="ai_model" value="{ai_model}">
                    <input type="hidden" name="download_id" value="{download_id}">
                    <button type="submit">Proceed to Phase 2 (Local Implementation)</button>
                </form>
            </article>
            """)

        # Phase 2 implementation
        await stream.add_message(
            "<div>Starting clean-room implementation...</div>"
        )
        import subprocess

        from .generator import CleanAgent
        from .packager import init_local_repo

        repo_path = init_local_repo()
        clean_agent = CleanAgent(
            llm=llm, dirty_agent=dirty_agent, max_turns=settings.max_qa_turns
        )

        await clean_agent.generate_codebase(specs, repo_path)

        # Commit Phase 2
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Spite",
                "-c",
                "user.email=spite@localhost",
                "commit",
                "-m",
                "Initial clean-room implementation",
            ],
            cwd=repo_path,
            check=True,
        )

        if target_phase == "2":
            return HTMLResponse(f"""
            <article>
                <header>Phase 2 Complete</header>
                <p>Repository implemented at: <code>{repo_path}</code></p>
                <form hx-post="/process_phase3" hx-target="#result" hx-indicator="#spinner" hx-disabled-elt="button[type='submit']">
                    <input type="hidden" name="repo_path" value="{repo_path}">
                    <input type="hidden" name="ai_provider" value="{ai_provider}">
                    <input type="hidden" name="ai_model" value="{ai_model}">
                    <button type="submit">Proceed to Phase 3 (AI Enhancements)</button>
                </form>
            </article>
            """)

        # Phase 3 implementation
        await stream.add_message("<div>Applying AI enhancements...</div>")
        await clean_agent.apply_improvements(specs, repo_path)

        # Commit Phase 3
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Spite",
                "-c",
                "user.email=spite@localhost",
                "commit",
                "-m",
                "Applied AI enhancements",
            ],
            cwd=repo_path,
            check=True,
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

@app.post("/process_phase2", response_model=None)
async def process_phase2(
    github_url: Annotated[str, Form()],
    ai_provider: Annotated[str, Form()],
    ai_model: Annotated[str, Form()],
    download_id: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
) -> HTMLResponse:
    """Handle continuation from phase 1 to phase 2."""
    import subprocess
    import zipfile

    from .analyzer import DirtyAgent
    from .generator import CleanAgent
    from .llm import LLMInterface
    from .packager import init_local_repo

    if client_id not in global_streams:
        global_streams[client_id] = ProgressStream()
    stream = global_streams[client_id]

    llm = LLMInterface(host=settings.ollama_host, model=ai_model)
    dirty_agent = DirtyAgent(llm=llm)

    try:
        base_dir = Path("data/downloads").resolve()
        download_path = (Path("data/downloads") / f"{download_id}.zip").resolve()
        if not download_path.is_relative_to(base_dir):
            return HTMLResponse("Invalid download ID.", status_code=400)

        if not download_path.exists():
             return HTMLResponse("Specifications zip not found.", status_code=404)

        specs: dict[str, str] = {}
        with zipfile.ZipFile(download_path, "r") as zip_file:
            for item in zip_file.namelist():
                specs[item] = zip_file.read(item).decode('utf-8')

        await stream.add_message("<div>Starting clean-room implementation...</div>")
        repo_path = init_local_repo()
        clean_agent = CleanAgent(
            llm=llm, dirty_agent=dirty_agent, max_turns=settings.max_qa_turns
        )

        await clean_agent.generate_codebase(specs, repo_path)

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Spite",
                "-c",
                "user.email=spite@localhost",
                "commit",
                "-m",
                "Initial clean-room implementation",
            ],
            cwd=repo_path,
            check=True,
        )

        return HTMLResponse(f"""
        <article>
            <header>Phase 2 Complete</header>
            <p>Repository implemented at: <code>{repo_path}</code></p>
            <form hx-post="/process_phase3" hx-target="#result" hx-indicator="#spinner" hx-disabled-elt="button[type='submit']">
                <input type="hidden" name="repo_path" value="{repo_path}">
                <input type="hidden" name="ai_provider" value="{ai_provider}">
                <input type="hidden" name="ai_model" value="{ai_model}">
                <input type="hidden" name="download_id" value="{download_id}">
                <input type="hidden" name="client_id" value="{client_id}">
                <button type="submit">Proceed to Phase 3 (AI Enhancements)</button>
            </form>
        </article>
        """)
    except Exception as e:
        logger.exception("Error processing phase 2 request")
        return HTMLResponse(f"<article>Error: {str(e)}</article>", status_code=500)

@app.post("/process_phase3", response_model=None)
async def process_phase3(
    repo_path: Annotated[str, Form()],
    ai_provider: Annotated[str, Form()],
    ai_model: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    download_id: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """Handle continuation from phase 2 to phase 3."""
    import subprocess
    import zipfile

    from .analyzer import DirtyAgent
    from .generator import CleanAgent
    from .llm import LLMInterface

    if client_id not in global_streams:
        global_streams[client_id] = ProgressStream()
    stream = global_streams[client_id]

    llm = LLMInterface(host=settings.ollama_host, model=ai_model)
    dirty_agent = DirtyAgent(llm=llm)

    try:
        import tempfile
        r_path = Path(repo_path).resolve()
        temp_dir = Path(tempfile.gettempdir()).resolve()
        if not r_path.is_relative_to(temp_dir):
            return HTMLResponse("Invalid repository path.", status_code=400)

        specs: dict[str, str] = {}
        if download_id:
            base_dir = Path("data/downloads").resolve()
            download_path = (Path("data/downloads") / f"{download_id}.zip").resolve()
            if not download_path.is_relative_to(base_dir):
                return HTMLResponse("Invalid download ID.", status_code=400)

            if download_path.exists():
                with zipfile.ZipFile(download_path, "r") as zip_file:
                    for item in zip_file.namelist():
                        specs[item] = zip_file.read(item).decode('utf-8')

        await stream.add_message("<div>Applying AI enhancements...</div>")
        clean_agent = CleanAgent(
            llm=llm, dirty_agent=dirty_agent, max_turns=settings.max_qa_turns
        )

        await clean_agent.apply_improvements(specs, Path(repo_path))

        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Spite",
                "-c",
                "user.email=spite@localhost",
                "commit",
                "-m",
                "Applied AI enhancements",
            ],
            cwd=repo_path,
            check=True,
        )

        return HTMLResponse(f"""
        <article>
            <header>Phase 3 Complete</header>
            <p>Enhanced repository available at: <code>{repo_path}</code></p>
        </article>
        """)
    except Exception as e:
        logger.exception("Error processing phase 3 request")
        return HTMLResponse(f"<article>Error: {str(e)}</article>", status_code=500)
