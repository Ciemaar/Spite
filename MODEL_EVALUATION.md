# AI Model Evaluation for Spite

This document outlines the various AI models supported for use within the Spite agentic cleanroom environment. It details the pros and cons of each model, particularly concerning their suitability for the different phases of the system (Phase 1: Specification Generation, Phase 2: Code Implementation, Phase 3: Enhancement).

## 1. Local Models (Ollama)

Spite primarily relies on local LLMs orchestrated via Ollama to maintain a true "cleanroom" environment without external data leakage.

### 1.1 Llama 3 (`llama3`) - **Default**

Llama 3 is the default and a strong, general-purpose instruction-following model used by Spite.

*   **Pros:**
    *   **Versatility:** Good at general reasoning, summarization, and formatting (e.g., Markdown generation).
    *   **Resource Efficiency:** Smaller parameter versions (e.g., 8B) run very efficiently on consumer hardware.
    *   **Agentic Orchestration:** Sufficiently capable of managing the Q&A loop between Dirty and Clean agents.
*   **Cons:**
    *   **Coding Complexities:** May sometimes struggle with highly complex architectural decisions or strict, nuanced coding standards compared to specialized coding models.
*   **Best Used For:** All phases, but particularly effective in Phase 1 (Specification Generation) where general reasoning and document structuring are paramount.

### 1.2 Qwen 2.5 Coder (`qwen2.5-coder`)

Qwen 2.5 Coder is a specialized model focused heavily on code generation and understanding.

*   **Pros:**
    *   **Superior Syntax and Logic:** Often produces highly accurate code with fewer syntax errors in strict environments.
    *   **Efficiency:** Can be faster at generating code blocks compared to general-purpose models of similar size.
*   **Cons:**
    *   **Agentic Orchestration:** While great at coding, it may sometimes struggle with the high-level orchestration, planning, and conversational nuances required in the Clean/Dirty agent Q&A loop compared to a general-purpose instruction model.
*   **Best Used For:** Phase 2 (Code Implementation) and Phase 3 (Enhancement) where the primary task is translating well-defined specifications into working code or refactoring existing code.

## 2. Cloud Providers

While Spite focuses on local execution, it supports cloud providers via API keys as secondary options or for premium performance when local hardware is insufficient.

### 2.1 OpenAI (GPT-4o)

*   **Pros:** Industry-leading reasoning, coding, and context management. Nearly flawless execution of all Spite phases.
*   **Cons:** Breaks the strict "local" cleanroom paradigm. Incurs API costs. Requires an active internet connection.

### 2.2 Anthropic (Claude 3.5 Sonnet)

*   **Pros:** Exceptional at coding, architectural design, and following complex system prompts. Often outperforms GPT-4o in specific coding tasks.
*   **Cons:** Same as GPT-4o (privacy concerns, cost, requires internet).
