import tempfile
from pathlib import Path

from spite.generator import CleanAgent
from spite.llm import LLMInterface


def test_parse_files():
    agent = CleanAgent(LLMInterface("fake", "fake"), LLMInterface("fake", "fake"))
    llm_output = """
```markdown
# filepath: code.py
print("hello")
```
"""
    files = agent._parse_files(llm_output)
    assert "code.py" in files
    assert files["code.py"] == "print(\"hello\")"

def test_write_files():
    agent = CleanAgent(LLMInterface("fake", "fake"), LLMInterface("fake", "fake"))
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        files = {"src/code.py": "print('hello')"}
        agent._write_files(files, repo_path)
        assert (repo_path / "src/code.py").exists()
        with open(repo_path / "src/code.py") as f:
            assert f.read() == "print('hello')"
