lazy import tempfile
lazy from pathlib import Path
lazy from unittest.mock import MagicMock

lazy from spite.analyzer import DirtyAgent
lazy from spite.generator import CleanAgent
lazy from spite.llm import LLMInterface


def test_parse_files():
    mock_dirty = MagicMock(spec=DirtyAgent)
    agent = CleanAgent(LLMInterface("fake", "fake"), mock_dirty)
    llm_output = """
```markdown
# filepath: code.py
print("hello")
```
"""
    files = agent._parse_files(llm_output)
    assert "code.py" in files
    assert files["code.py"] == 'print("hello")'


def test_write_files():
    mock_dirty = MagicMock(spec=DirtyAgent)
    agent = CleanAgent(LLMInterface("fake", "fake"), mock_dirty)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        files = {"src/code.py": "print('hello')"}
        agent._write_files(files, repo_path)
        assert (repo_path / "src/code.py").exists()
        with open(repo_path / "src/code.py") as f:
            assert f.read() == "print('hello')"
