# Next Steps for DSPy Integration in Spite

The initial proof-of-concept (PoC) for integrating DSPy into the Spite project successfully demonstrated that DSPy can replace raw string prompts with declarative, object-oriented Signatures and Predictors. While the basic functionality (generating specs, Q&A loops, generating code) works as expected, the true power of DSPy lies in its optimization capabilities.

To fully leverage DSPy and improve the reliability and quality of the generated codebase, the following next steps are recommended:

## 1. Implement Typed Predictors (Pydantic Integration)

*(Partially Completed)*

We have successfully migrated the `CleanAgentAction` signature to use a Pydantic model (`CleanAgentActionOutput`) for its output, removing the messy `try/except json.loads` regex parsing in `generator.py`. DSPy forces structured JSON outputs via `dspy.TypedPredictor`.

**Remaining Action Item:**

- Refactor the `GenerateSpecs` signature to output a Pydantic model containing a dictionary mapping file paths to file contents, rather than relying on the LLM to format markdown code blocks exactly right.
- Refactor `FinalCodeGeneration` and `ApplyImprovements` to similarly use a Pydantic model mapping file paths to strings, removing the need for `_parse_files(llm_output)` entirely.

## 2. Develop Evaluation Metrics

To use DSPy's optimizers (Teleprompters), Spite needs automated ways to score the quality of an LLM's output.

**Action Item:**

- Create a metric function for `GenerateSpecs` that verifies all 8 required files are present, properly formatted, and do not contain obvious hallucinations.
- Create a metric function for `CleanAgent` that verifies the final generated codebase. This metric could actually run a linting tool (like `ruff` or `eslint`) or run a compiler against the generated output to see if it is syntactically valid.
- The metric should return a float (0.0 to 1.0) indicating the quality of the response.

## 3. Implement Prompt Optimization (Compilation)

Once metrics are defined, we can compile the DSPy pipelines. This involves using DSPy's optimizers (like `BootstrapFewShot` or `MIPROv2`) to automatically generate few-shot examples and optimize the internal prompts sent to Ollama.

**Action Item:**

- Create a training dataset (a list of `dspy.Example` objects) containing various repository inputs (e.g., small, well-known open-source projects).
- Write a compilation script (e.g., `scripts/compile_dspy.py`) that runs the `DirtyAgent` and `CleanAgent` modules through an optimizer using the training dataset and the defined metrics.
- Save the compiled, optimized prompts to a JSON file (using `module.save()`) and load them during runtime in `main.py` (using `module.load()`). This will give the system highly optimized few-shot prompts without manual prompt engineering.

## 4. Refine the Q&A Loop (Multi-hop Reasoning)

The current `CleanAgent` Q&A loop uses a simple `for` loop in Python to decide whether to ask a question or generate code. DSPy provides modules like `dspy.ReAct` (Reasoning and Acting) or `dspy.ChainOfThought` which are specifically designed for multi-hop reasoning.

**Action Item:**

- Evaluate replacing the Python `for` loop in `generate_codebase` with a `dspy.ReAct` module, giving it a tool to query the `DirtyAgent`. This would allow the LLM to autonomously decide when it has enough information to write the code, utilizing DSPy's built-in reasoning traces.

## 5. Handle Async Workloads Better

Currently, DSPy's standard `dspy.Predict` operates synchronously. While it wraps async calls under the hood in some cases, it can block the FastAPI event loop during long generation cycles.

**Action Item:**

- Investigate `dspy.asyncify` or migrating to the explicitly asynchronous prediction methods within DSPy to ensure the Spite API remains highly responsive during the hours-long clean-room generation phases.

## 6. Configure Caching and Rate Limits

DSPy caches responses by default in a local sqlite database. While this is extremely helpful for rapid testing and compilation, in a long-running generation script it can sometimes cause unexpected stale responses if not managed properly.

**Action Item:**

- Configure `dspy.settings.configure(cache=False)` for production runs where we want fresh outputs, or configure a specific cache directory inside the Spite working directory (e.g., `.spite_cache/`).
- Configure retry and timeout parameters in the `dspy.LM` initialization within `llm.py` to ensure local Ollama instances don't throw connection errors on extremely long code generation tasks.

## Summary

The current integration is a successful implementation of Prompt Replacement and initial Structured Outputs (via Pydantic and ChainOfThought). Moving fully to Level 2 (Strict Output Validation) and Level 3 (Automated Optimization) will transform Spite from a standard LLM wrapper into a self-improving, robust clean-room agent framework.
