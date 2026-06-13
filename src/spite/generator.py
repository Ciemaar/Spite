import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from .llm import LLMInterface

if TYPE_CHECKING:
    from .analyzer import DirtyAgent

logger = logging.getLogger(__name__)


class CleanAgent:
    """The agent responsible for implementing the clean-room codebase."""

    def __init__(self, llm: LLMInterface, dirty_agent: "DirtyAgent", max_turns: int = 3):
        """Initialize the clean agent with its own LLM and access to the dirty Agent."""
        self.llm = llm
        self.dirty_agent = dirty_agent
        self.max_turns = max_turns
        self.qa_log: list[str] = []

    async def generate_codebase(self, specs: dict[str, str], repo_path: Path) -> None:
        """Generate the codebase via Q&A and write to the repo path."""
        # Setup clean agent prompt
        implementation_plan = specs.get("IMPLEMENTATION_PLAN.md", "")
        requirements = specs.get("REQUIREMENTS.md", "")
        agents_instructions = specs.get("AGENTS.md", "")

        system_prompt = (
            "You are the 'Clean' Agent in a clean-room software recreation system.\n"
            "Your job is to implement the software exactly according to the provided specs.\n"
            "You MUST NOT access the internet or the original source code.\n"
            "You have the opportunity to ask the 'Dirty' Agent questions about public, observable behavior.\n"
            "You MUST format your output as a JSON object with either a 'question' key OR 'code' key.\n"
            'If you need clarification, output: {"question": "Your question here"}\n'
            'If you are ready to write code, output: {"code": "```markdown\\n# filepath: ...\\n...```"}\n'
        )

        user_prompt = f"Requirements:\n{requirements}\n\nPlan:\n{implementation_plan}\n\nInstructions:\n{agents_instructions}\n"

        # Q&A Loop
        for turn in range(self.max_turns):
            logger.info(f"Clean Agent turn {turn + 1}")
            response = await self.llm.generate_response(system_prompt, user_prompt)

            # Simple heuristic parsing since we asked for JSON but LLMs can be tricky
            if '"question"' in response.lower() and '"code"' not in response.lower():
                # Extract question
                try:
                    import json

                    # Try to extract JSON block if it's wrapped in markdown
                    json_str = response
                    if "```json" in response:
                        json_str = response.split("```json")[1].split("```")[0]
                    elif "```" in response:
                        json_str = response.split("```")[1].split("```")[0]

                    data = json.loads(json_str)
                    question = data.get("question", "No question found.")
                except Exception:
                    question = response  # Fallback

                logger.info(f"Clean Agent asks: {question}")
                self.qa_log.append(f"**Clean Agent:** {question}")

                # Ask Dirty Agent
                dirty_answer = await self.dirty_agent.answer_question(question, specs)
                logger.info(f"Dirty Agent answers: {dirty_answer}")
                self.qa_log.append(f"**Dirty Agent:** {dirty_answer}")

                user_prompt += f"\n\nDirty Agent Answer:\n{dirty_answer}\n\nNow, do you have another question or are you ready to write code?"
            else:
                # Assume it's ready to output code
                logger.info("Clean Agent is ready to output code.")
                break

        # Final Generation
        user_prompt += "\n\nPlease output the complete codebase now using the markdown format:\n```markdown\n# filepath: filename.ext\n[code]\n```"
        final_code_response = await self.llm.generate_response(
            system_prompt, user_prompt
        )

        # Parse and write files
        files = self._parse_files(final_code_response)
        self._write_files(files, repo_path)

        # Write QA Log
        qa_content = "# Clean-Dirty QA Log\n\n" + "\n\n".join(self.qa_log)
        self._write_files({"CLEAN_DIRTY_QA_LOG.md": qa_content}, repo_path)

        # Write Bibliography
        bib_content = (
            "# Clean Bibliography\n\nSources considered during implementation:\n"
        )
        bib_content += "1. Provided Markdown Specifications (REQUIREMENTS.md, IMPLEMENTATION_PLAN.md)\n"
        bib_content += "2. Answers from Dirty Agent\n"
        self._write_files({"CLEAN_BIBLIOGRAPHY.md": bib_content}, repo_path)

    def _parse_files(self, llm_output: str) -> dict[str, str]:
        """Parse the Markdown codeblocks with filepaths into a dictionary."""
        files: dict[str, str] = {}
        pattern = r"```(?:markdown)?\s*#\s*filepath:\s*(.*?)\s*\n(.*?)```"
        matches = re.finditer(pattern, llm_output, re.DOTALL)

        for match in matches:
            filepath = match.group(1).strip()
            content = match.group(2).strip()
            files[filepath] = content

        return files

    def _write_files(self, files: dict[str, str], repo_path: Path) -> None:
        """Write the files to the local repository directory securely."""
        repo_path = repo_path.resolve()
        # Ensure trailing slash for exact path prefix matching
        repo_path_str = str(repo_path)
        if not repo_path_str.endswith("/"):
            repo_path_str += "/"

        for filepath, content in files.items():
            # Prevent Path Traversal
            # Resolve removes '..' but we must ensure it's still inside repo_path
            try:
                full_path = (repo_path / filepath).resolve()
                if not str(full_path).startswith(repo_path_str):
                    logger.warning(f"Path traversal attempted: {filepath}")
                    continue
            except ValueError:
                logger.warning(f"Invalid path encountered: {filepath}")
                continue

            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Wrote file {filepath}")

    async def apply_improvements(self, specs: dict[str, str], repo_path: Path) -> None:
        """Apply the improvements from IMPROVEMENTS.md to the codebase."""
        improvements = specs.get("IMPROVEMENTS.md", "")
        if not improvements:
            return

        # Read current files
        current_files = ""
        for path in repo_path.rglob("*"):
            # Exclude files in .git directory
            if ".git" in path.parts:
                continue
            if path.is_file() and not path.name.startswith("."):
                try:
                    with open(path, encoding="utf-8") as f:
                        current_files += (
                            f"--- {path.relative_to(repo_path)} ---\n{f.read()}\n\n"
                        )
                except UnicodeDecodeError:
                    pass

        system_prompt = (
            "You are the 'Clean' Agent.\n"
            "Your job is to apply the provided improvements to the existing codebase.\n"
            "Output the updated files using the standard markdown block format.\n"
        )

        user_prompt = f"Current Codebase:\n{current_files}\n\nImprovements to Apply:\n{improvements}"

        response = await self.llm.generate_response(system_prompt, user_prompt)
        files = self._parse_files(response)
        self._write_files(files, repo_path)
