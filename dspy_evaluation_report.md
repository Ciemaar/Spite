# DSPy Evaluation Report

## Overview
As part of an evaluation to determine the suitability of replacing raw LLM prompts with DSPy inside of the `spite` project, I refactored the primary language model interfaces (`DirtyAgent` and `CleanAgent`) to utilize DSPy signatures and predictors.

DSPy fundamentally shifts the paradigm from "prompt engineering" to "programming" by utilizing modules, signatures, and declarative inputs/outputs.

## Implementation Details

### Configuration
1. **Dependency:** Added `dspy` to `pyproject.toml`.
2. **Backend Context:** Refactored `LLMInterface` in `src/spite/llm.py`. Because `spite` utilizes an Ollama local model, DSPy's standard LiteLLM fallback mechanism works cleanly out of the box when using the `ollama_chat/` prefix for model names (`dspy.LM("ollama_chat/..."))`.
3. **Global Registration:** Updated agent methods (`analyze`, `answer_question`, `generate_codebase`, `apply_improvements`) to ensure DSPy is globally configured prior to execution.

### `DirtyAgent` Refactor (in `src/spite/analyzer.py`)
- Created two `dspy.Signature` classes: `GenerateSpecs` and `AnswerQuestion`.
- Replaced the string-concat raw prompts with input and output fields.
- Integrated the original requirements for exactly 8 markdown files directly into the signature's docstring instructions.
- Used `dspy.Predict` synchronously. The iterative check to retry the LLM (up to 3 times) for missing markdown files remains in Python code, which works harmoniously with DSPy predictors (providing `feedback` as an input field on subsequent loops).

### `CleanAgent` Refactor (in `src/spite/generator.py`)
- Created `dspy.Signature` classes: `CleanAgentAction`, `FinalCodeGeneration`, and `ApplyImprovements`.
- During implementation, a notable discovery was that using the property name `instructions` on a `dspy.Signature` causes an internal conflict with DSPy's own attributes. Renaming it to `agent_instructions` successfully resolved the issue.
- Replaced the complex Q&A turn generation logic with declarative `dspy.Predict` calls.

## Evaluation & Findings

1. **Integration Ease:**
   - Adding DSPy to a project using local Ollama models is extremely simple thanks to DSPy 2.x's built-in support for LiteLLM.
   - Refactoring basic prompt generation to basic `dspy.Predict` pipelines feels very natural and results in somewhat cleaner, class-based definitions (`Signature`s).
2. **Strict Structure Compatibility:**
   - The original architecture of `spite` attempts to parse specific text formats natively (like markdown code blocks containing `# filepath: ...` or raw JSON). DSPy handles the structuring of the *prompt* well, but without taking advantage of more advanced features (like DSPy's `TypedPredictor` with Pydantic for rigid JSON formatting), we still rely on fuzzy parsing heuristic loops natively in Python.
3. **Optimization Opportunity:**
   - Currently, we only utilize `dspy.Predict`. The real power of DSPy lies in its optimization algorithms (Teleprompters/Optimizers) such as `BootstrapFewShot` or `COPRO`. While we didn't implement metric-driven compilation in this proof-of-concept, `spite` is now positioned perfectly to add few-shot compilation phases. If `spite` can define a metric for evaluating if its output is "good" (e.g. testing whether the generated codebase correctly compiles), DSPy can train the prompts across epochs to drastically improve output stability.
4. **Performance Consideration:**
   - One minor tradeoff when replacing the raw `AsyncClient` from the `ollama` library with `dspy.Predict` is that DSPy standard predictors are currently primarily synchronous. The underlying network requests to Ollama operate correctly, but they may pause the asyncio event loop unless wrapped appropriately (or by using the less-documented async interfaces in DSPy).

## Conclusion
DSPy provides a cleaner and more maintainable abstraction for the LLM prompts in the `spite` architecture. The framework acts well as a drop-in replacement for raw string prompts via `dspy.Predict`. Given that `spite` is an agentic framework, utilizing DSPy positions the project to scale its reliability via prompt compilation (optimizers) in the future.
