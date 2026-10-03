import ast
import os
from pathlib import Path

def process_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return

    # Find all module-level import nodes
    import_lines = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                pass # eager: from __future__
            elif isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                pass # eager: star import
            else:
                import_lines.add(node.lineno)

    # Re-read and write lines
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        lineno = idx + 1
        if lineno in import_lines:
            # check if it's already lazy
            if not line.lstrip().startswith("lazy "):
                spaces = len(line) - len(line.lstrip())
                lines[idx] = " " * spaces + "lazy " + line.lstrip()

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

for root, _, files in os.walk("tests"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
