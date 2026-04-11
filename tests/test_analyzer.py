from spite.analyzer import DirtyAgent
from spite.llm import LLMInterface


def test_parse_files():
    agent = DirtyAgent(LLMInterface("fake", "fake"))
    llm_output = """
```markdown
# filepath: file1.md
content 1
```
Some other text
```
# filepath: file2.md
content 2
```
"""
    files = agent._parse_files(llm_output)
    assert "file1.md" in files
    assert files["file1.md"] == "content 1"
    assert "file2.md" in files
    assert files["file2.md"] == "content 2"
