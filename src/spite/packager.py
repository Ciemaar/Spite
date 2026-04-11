import io
import logging
import subprocess
import tempfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

def create_zip_payload(specs: dict[str, str]) -> io.BytesIO:
    """Create an in-memory zip file from the specification files."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, content in specs.items():
            zip_file.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer

def init_local_repo() -> Path:
    """Initialize a local temporary Git repository."""
    temp_dir = tempfile.mkdtemp(prefix="spite_")
    repo_path = Path(temp_dir)

    try:
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        logger.info(f"Initialized Git repository at {repo_path}")
        return repo_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initialize Git repository: {e.stderr.decode()}")
        raise
