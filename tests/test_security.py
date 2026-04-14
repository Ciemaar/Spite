import tempfile
from pathlib import Path

import pytest

from spite.generator import CleanAgent
from spite.ingest import IngestionManager
from spite.llm import LLMInterface


def test_path_traversal_prevention():
    agent = CleanAgent(LLMInterface("fake", "fake"), LLMInterface("fake", "fake"))
    files = {
        "../../../etc/passwd": "hacked",
        "/absolute/path/test.txt": "hacked again",
        "valid_file.txt": "safe"
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        agent._write_files(files, repo_path)

        # valid file should be created
        assert (repo_path / "valid_file.txt").exists()

        # traversal and absolute path should not write to those locations
        assert not Path("/absolute/path/test.txt").exists()

        # Ensure it didn't create a literal ../../../etc/passwd folder structure outside
        # The logic prevents `full_path.startswith(repo_path)`
        # so these files should have just been skipped/ignored
        assert len(list(repo_path.glob("**/*"))) == 1 # only valid_file.txt should exist


@pytest.mark.asyncio
async def test_ssrf_prevention():
    manager = IngestionManager()

    # Try to fetch local metadata endpoint
    results = await manager.fetch_urls(["http://169.254.169.254/latest/meta-data"])
    assert len(results) == 0

    # Try local host
    results = await manager.fetch_urls(["http://localhost:8000/admin"])
    assert len(results) == 0

    # Try file protocol
    results = await manager.fetch_urls(["file:///etc/passwd"])
    assert len(results) == 0
