import logging
from pathlib import Path
from typing import TYPE_CHECKING

import dspy  # type: ignore
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .analyzer import DirtyAgent

logger = logging.getLogger(__name__)


class CleanAgentBrainstorm(dspy.Signature):
    r"""Reason about the software specifications and implement the codebase.

    You are the 'Clean' Agent in a clean-room software recreation system.
    Your job is to implement the software exactly according to the provided specs.
    You MUST NOT access the internet or the original source code.
    You have the opportunity to ask the 'Dirty' Agent questions about public, observable behavior.

    If you do not have enough information, use the `ask_dirty_agent` tool.
    Once you have enough information, output the complete codebase in markdown format.
    """

    requirements: str = dspy.InputField(desc="The software requirements.")
    plan: str = dspy.InputField(desc="The implementation plan.")
    agent_instructions: str = dspy.InputField(desc="The agent instructions.")
    markdown_files_output: str = dspy.OutputField(
        desc="The complete codebase in markdown block format."
    )


class CodebaseOutput(BaseModel):
    """A dictionary mapping file paths to their string contents."""

    files: dict[str, str] = Field(
        description="A dictionary mapping the exact requested file paths to their code contents."
    )


class FinalCodeGeneration(dspy.Signature):
    """Output the final codebase using the structured files format.

    You are the 'Clean' Agent in a clean-room software recreation system.
    Please output the complete codebase now into the dictionary.
    """

    requirements: str = dspy.InputField(desc="The software requirements.")
    plan: str = dspy.InputField(desc="The implementation plan.")
    agent_instructions: str = dspy.InputField(desc="The agent instructions.")
    qa_history: str = dspy.InputField(
        desc="The history of questions asked and answers received so far."
    )
    generated_codebase: CodebaseOutput = dspy.OutputField(
        desc="The structured complete codebase files mapping."
    )


class ApplyImprovements(dspy.Signature):
    """Apply improvements to the codebase.

    You are the 'Clean' Agent.
    Your job is to apply the provided improvements to the existing codebase.
    Output the updated files into the structured dictionary format.
    """

    current_codebase: str = dspy.InputField(desc="The current codebase context.")
    improvements: str = dspy.InputField(desc="The improvements to apply.")
    updated_files: CodebaseOutput = dspy.OutputField(
        desc="The structured dictionary of updated files."
    )


class CleanAgent:
    """The agent responsible for implementing the clean-room codebase."""

    def __init__(self, dirty_agent: "DirtyAgent", max_turns: int = 3):
        """Initialize the clean agent with access to the dirty Agent."""
        self.dirty_agent = dirty_agent
        self.max_turns = max_turns
        self.qa_log: list[str] = []

    async def generate_codebase(self, specs: dict[str, str], repo_path: Path) -> None:
        """Generate the codebase via Q&A and write to the repo path."""
        implementation_plan = specs.get("IMPLEMENTATION_PLAN.md", "")
        requirements = specs.get("REQUIREMENTS.md", "")
        agents_instructions = specs.get("AGENTS.md", "")

        def ask_dirty_agent(question: str) -> str:
            """Ask the Dirty Agent a question about the repository's observable behavior."""
            logger.info(f"Clean Agent asks: {question}")
            self.qa_log.append(f"**Clean Agent:** {question}")

            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Since the tool is invoked synchronously by DSPy, but the agent method is async,
                # we run the coroutine in a new short-lived loop or nested event loop if necessary.
                # However, nest_asyncio isn't here. A simpler approach for DSPy tools that call async methods
                # is to use asyncio.run if we aren't already in a running loop thread,
                # but we ARE in a running loop (FastAPI).
                import nest_asyncio  # type: ignore

                nest_asyncio.apply()
                answer = asyncio.run(self.dirty_agent.answer_question(question, specs))
            else:
                answer = asyncio.run(self.dirty_agent.answer_question(question, specs))

            logger.info(f"Dirty Agent answers: {answer}")
            self.qa_log.append(f"**Dirty Agent:** {answer}")
            return answer

        # Create ReAct module with the tool
        agent = dspy.ReAct(
            CleanAgentBrainstorm, tools=[ask_dirty_agent], max_iters=self.max_turns
        )

        # Execute the agent loop
        logger.info("Starting Clean Agent ReAct loop.")
        agent(
            requirements=requirements,
            plan=implementation_plan,
            agent_instructions=agents_instructions,
        )

        # For the final code execution, we will still pass the history generated to the explicitly typed predictor
        generate_final_code = dspy.ChainOfThought(FinalCodeGeneration)
        final_result = generate_final_code(
            requirements=requirements,
            plan=implementation_plan,
            agent_instructions=agents_instructions,
            qa_history="\n".join(self.qa_log) if self.qa_log else "No questions asked.",
        )

        files = final_result.generated_codebase.files
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

        apply_improvements_pred = dspy.ChainOfThought(ApplyImprovements)
        result = apply_improvements_pred(
            current_codebase=current_files, improvements=improvements
        )

        files = result.updated_files.files
        self._write_files(files, repo_path)
