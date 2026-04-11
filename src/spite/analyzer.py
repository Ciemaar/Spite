import logging
import re

from .llm import LLMInterface

logger = logging.getLogger(__name__)


class DirtyAgent:
    """The agent responsible for analyzing the dirty context and creating specs."""

    def __init__(self, llm: LLMInterface):
        """Initialize the dirty agent with an LLM interface."""
        self.llm = llm

    async def analyze(
        self,
        repo_files: dict[str, str],
        supplemental_content: dict[str, str],
        search_context: str,
    ) -> dict[str, str]:
        """Analyze the context and generate 8 specification files."""
        system_prompt = (
            "You are the 'Dirty' Agent in a clean-room software recreation system.\n"
            "Your job is to analyze public repositories and documentation, "
            "then write highly detailed specifications.\n"
            "You MUST output your response as 8 distinct Markdown files.\n"
            "Use the following format to delineate files:\n\n"
            "```markdown\n# filepath: filename.md\n[file content here]\n```\n\n"
            "You MUST generate EXACTLY these 8 files:\n"
            "1. REQUIREMENTS.md: Functional and non-functional requirements.\n"
            "2. TESTING.md: Testing strategy.\n"
            "3. IMPLEMENTATION_PLAN.md: Step-by-step plan.\n"
            "4. AGENTS.md: Agent Instructions / rules.\n"
            "5. IMPROVEMENTS.md: Opportunities for behavioral or API improvements.\n"
            "6. DIRTY_BIBLIOGRAPHY.md: Links and commentary on sources considered.\n"
            "7. SYSTEM_OVERVIEW.md: System overview and replacement name.\n"
            "8. SOURCE_EXCLUDES.txt: A plain list of URLs/domains to block.\n"
        )

        # Truncate context to avoid blowing up context window
        context_parts: list[str] = []
        for path, content in list(repo_files.items())[:10]:
            truncated = content[:2000]
            context_parts.append(f"--- File: {path} ---\n{truncated}")

        for url, content in list(supplemental_content.items())[:3]:
            truncated = content[:2000]
            context_parts.append(f"--- URL: {url} ---\n{truncated}")

        if search_context:
            context_parts.append(f"--- Web Search Context ---\n{search_context}")

        user_prompt = "Context to analyze:\n\n" + "\n\n".join(context_parts)

        response = await self.llm.generate_response(system_prompt, user_prompt)
        return self._parse_files(response)

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
