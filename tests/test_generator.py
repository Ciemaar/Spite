import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from spite.analyzer import DirtyAgent
from spite.generator import CleanAgent


def test_write_files():
    mock_dirty = MagicMock(spec=DirtyAgent)
    agent = CleanAgent(mock_dirty)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        files = {"src/code.py": "print('hello')"}
        agent._write_files(files, repo_path)
        assert (repo_path / "src/code.py").exists()
        with open(repo_path / "src/code.py") as f:
            assert f.read() == "print('hello')"
