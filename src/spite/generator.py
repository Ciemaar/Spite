import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

import dspy  # type: ignore
from pydantic import BaseModel, Field

from .llm import LLMInterface

if TYPE_CHECKING:
    from .analyzer import DirtyAgent

logger = logging.getLogger(__name__)


class CleanAgentActionOutput(BaseModel):
    """The action the Clean Agent wants to take."""

    question: str | None = Field(
        default=None,
        description="The question to ask the Dirty Agent. Null if you are ready to write code.",
    )
    code: str | None = Field(
        default=None,
        description="The complete codebase in markdown block format. Null if you need to ask a question.",
    )


class CleanAgentAction(dspy.Signature):
    r"""Ask a question or provide the codebase based on specs.

    You are the 'Clean' Agent in a clean-room software recreation system.
    Your job is to implement the software exactly according to the provided specs.
    You MUST NOT access the internet or the original source code.
    You have the opportunity to ask the 'Dirty' Agent questions about public, observable behavior.
    You must decide to either ask a question OR write the code.
    """

    requirements: str = dspy.InputField(desc="The software requirements.")
    plan: str = dspy.InputField(desc="The implementation plan.")
    agent_instructions: str = dspy.InputField(desc="The agent instructions.")
    qa_history: str = dspy.InputField(
        desc="The history of questions asked and answers received so far."
    )
    action: CleanAgentActionOutput = dspy.OutputField(
        desc="The structured action output."
    )


class FinalCodeGeneration(dspy.Signature):
    """Output the final codebase using markdown blocks.

    You are the 'Clean' Agent in a clean-room software recreation system.
    Please output the complete codebase now.
    Output the files using the standard markdown block format:
    ```markdown
    # filepath: filename.ext
    [code]
    ```.
    """

    requirements: str = dspy.InputField(desc="The software requirements.")
    plan: str = dspy.InputField(desc="The implementation plan.")
    agent_instructions: str = dspy.InputField(desc="The agent instructions.")
    qa_history: str = dspy.InputField(
        desc="The history of questions asked and answers received so far."
    )
    markdown_files_output: str = dspy.OutputField(
        desc="The complete codebase in markdown format."
    )


class ApplyImprovements(dspy.Signature):
    """Apply improvements to the codebase.

    You are the 'Clean' Agent.
    Your job is to apply the provided improvements to the existing codebase.
    Output the updated files using the standard markdown block format:
    ```markdown
    # filepath: filename.ext
    [code]
    ```.
    """

    current_codebase: str = dspy.InputField(desc="The current codebase context.")
    improvements: str = dspy.InputField(desc="The improvements to apply.")
    updated_files_output: str = dspy.OutputField(
        desc="The updated files in markdown format."
    )


class CleanAgent:
    """The agent responsible for implementing the clean-room codebase."""

    def __init__(
        self, llm: LLMInterface, dirty_agent: "DirtyAgent", max_turns: int = 3
    ):
        """Initialize the clean agent with its own LLM and access to the dirty Agent."""
        self.llm = llm
        self.dirty_agent = dirty_agent
        self.max_turns = max_turns
        self.qa_log: list[str] = []

    async def generate_codebase(self, specs: dict[str, str], repo_path: Path) -> None:
        """Generate the codebase via Q&A and write to the repo path."""
        # Ensure DSPy is configured globally for this execution
        if self.llm.dspy_lm:
            dspy.settings.configure(lm=self.llm.dspy_lm)

        # Setup clean agent prompt
        implementation_plan = specs.get("IMPLEMENTATION_PLAN.md", "")
        requirements = specs.get("REQUIREMENTS.md", "")
        agents_instructions = specs.get("AGENTS.md", "")

        qa_history_str = ""
        # Using ChainOfThought. DSPy > 2.5 natively handles Pydantic OutputFields on predictors.
        determine_action = dspy.ChainOfThought(CleanAgentAction)
        # Final code generation should use ChainOfThought for better layout reasoning
        generate_final_code = dspy.ChainOfThought(FinalCodeGeneration)

        # Q&A Loop
        for turn in range(self.max_turns):
            logger.info(f"Clean Agent turn {turn + 1}")

            result = determine_action(
                requirements=requirements,
                plan=implementation_plan,
                agent_instructions=agents_instructions,
                qa_history=qa_history_str
                if qa_history_str
                else "No questions asked yet.",
            )

            action_output: CleanAgentActionOutput = result.action

            # Use structured Pydantic object
            if action_output.question and not action_output.code:
                question = action_output.question

                logger.info(f"Clean Agent asks: {question}")
                self.qa_log.append(f"**Clean Agent:** {question}")

                # Ask Dirty Agent
                dirty_answer = await self.dirty_agent.answer_question(question, specs)
                logger.info(f"Dirty Agent answers: {dirty_answer}")
                self.qa_log.append(f"**Dirty Agent:** {dirty_answer}")

                qa_history_str += f"\nQ: {question}\nA: {dirty_answer}\n"
            else:
                # Assume it's ready to output code or already did
                logger.info("Clean Agent is ready to output code.")
                break

        # Final Generation
        final_result = generate_final_code(
            requirements=requirements,
            plan=implementation_plan,
            agent_instructions=agents_instructions,
            qa_history=qa_history_str if qa_history_str else "No questions asked.",
        )
        final_code_response = final_result.markdown_files_output

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

        # Ensure DSPy is configured globally for this execution
        if self.llm.dspy_lm:
            dspy.settings.configure(lm=self.llm.dspy_lm)

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

        apply_improvements_pred = dspy.Predict(ApplyImprovements)
        result = apply_improvements_pred(
            current_codebase=current_files, improvements=improvements
        )

        response = result.updated_files_output
        files = self._parse_files(response)
        self._write_files(files, repo_path)
