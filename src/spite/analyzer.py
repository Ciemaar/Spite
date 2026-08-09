import logging
import re

import dspy  # type: ignore

from .llm import LLMInterface

logger = logging.getLogger(__name__)


class GenerateSpecs(dspy.Signature):
    """Generate specs from a clean-room repository.

    You are the 'Dirty' Agent in a clean-room software recreation system.
    Your job is to analyze public repositories and documentation, then write highly detailed specifications.
    You MUST output your response as 8 distinct Markdown files.
    Use the following format to delineate files:

    ```markdown
    # filepath: filename.md
    [file content here]
    ```

    You MUST generate EXACTLY these 8 files:
    1. REQUIREMENTS.md: Functional and non-functional requirements.
    2. TESTING.md: Testing strategy.
    3. IMPLEMENTATION_PLAN.md: Step-by-step plan.
    4. AGENTS.md: Agent Instructions / rules.
    5. IMPROVEMENTS.md: Opportunities for behavioral or API improvements.
    6. DIRTY_BIBLIOGRAPHY.md: Links and commentary on sources considered.
    7. SYSTEM_OVERVIEW.md: System overview and replacement name.
    8. SOURCE_EXCLUDES.txt: A plain list of URLs/domains to block.
    """

    context: str = dspy.InputField(
        desc="The repository files, documentation and search context to analyze."
    )
    feedback: str = dspy.InputField(
        desc="Any feedback on missing files to correct in this attempt. Can be empty."
    )
    markdown_files_output: str = dspy.OutputField(
        desc="The 8 generated markdown files delineated by the `# filepath:` markdown code block format."
    )


class AnswerQuestion(dspy.Signature):
    """Answer questions about public observable behavior.

    You are the 'Dirty' Agent in a clean-room recreation.
    You must answer questions from the Clean Agent ONLY about public, observable behavior.
    You MUST REJECT any questions about implementation details, variable names, or internal architecture of the original source.
    Use your context of the repository to provide an accurate answer.
    """

    context: str = dspy.InputField(
        desc="The repository files, documentation and search context."
    )
    specs: str = dspy.InputField(
        desc="The generated specifications, specifically SYSTEM_OVERVIEW.md."
    )
    question: str = dspy.InputField(desc="The question from the Clean Agent.")
    answer: str = dspy.OutputField(
        desc="The answer to the question based ONLY on observable behavior."
    )


class DirtyAgent:
    """The agent responsible for analyzing the dirty context and creating specs."""

    def __init__(self, llm: LLMInterface):
        """Initialize the dirty agent with an LLM interface."""
        self.llm = llm
        self.context_parts: list[str] = []

    async def analyze(
        self,
        repo_files: dict[str, str],
        supplemental_content: dict[str, str],
        search_context: str,
    ) -> dict[str, str]:
        """Analyze the context and generate 8 specification files."""
        # Ensure DSPy is configured globally for this execution
        if self.llm.dspy_lm:
            dspy.settings.configure(lm=self.llm.dspy_lm)

        # Truncate context to avoid blowing up context window
        self.context_parts = []
        for path, content in list(repo_files.items())[:10]:
            truncated = content[:2000]
            self.context_parts.append(f"--- File: {path} ---\n{truncated}")

        for url, content in list(supplemental_content.items())[:3]:
            truncated = content[:2000]
            self.context_parts.append(f"--- URL: {url} ---\n{truncated}")

        if search_context:
            self.context_parts.append(f"--- Web Search Context ---\n{search_context}")

        context_str = "Context to analyze:\n\n" + "\n\n".join(self.context_parts)

        required_files = {
            "REQUIREMENTS.md",
            "TESTING.md",
            "IMPLEMENTATION_PLAN.md",
            "AGENTS.md",
            "IMPROVEMENTS.md",
            "DIRTY_BIBLIOGRAPHY.md",
            "SYSTEM_OVERVIEW.md",
            "SOURCE_EXCLUDES.txt",
        }

        generate_specs = dspy.Predict(GenerateSpecs)

        # Try up to 3 times to get all 8 files
        max_retries = 3
        feedback = ""
        for attempt in range(max_retries):
            # Using synchronous DSPy prediction. LiteLLM under the hood handles async if we needed to await it,
            # but DSPy's standard Predict is sync.
            result = generate_specs(context=context_str, feedback=feedback)
            response = result.markdown_files_output
            files = self._parse_files(response)

            missing = required_files - set(files.keys())
            if not missing:
                return files

            logger.warning(
                f"Attempt {attempt + 1}: Missing {len(missing)} required files: {missing}. Retrying..."
            )

            # Append feedback to prompt to guide the LLM to provide the missing files
            feedback = f"ERROR: You failed to output the following required files: {missing}.\n"
            feedback += (
                "Please try again and ensure you output EXACTLY all 8 required files."
            )

        raise ValueError(
            f"Dirty agent failed to generate all required specifications after {max_retries} attempts."
        )

    async def answer_question(self, question: str, specs: dict[str, str]) -> str:
        """Answer a question from the Clean Agent about observable behavior."""
        if self.llm.dspy_lm:
            dspy.settings.configure(lm=self.llm.dspy_lm)

        context = "Context:\n\n" + "\n\n".join(self.context_parts)
        spec_overview = specs.get("SYSTEM_OVERVIEW.md", "")

        answer_question = dspy.Predict(AnswerQuestion)
        result = answer_question(
            context=context, specs=spec_overview, question=question
        )

        return result.answer

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
