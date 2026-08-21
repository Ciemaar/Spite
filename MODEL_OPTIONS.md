# Model Options and Evaluation for Spite

This document outlines the recommended local and cloud AI models for the Spite project. It is specifically tailored considering hardware constraints (e.g., desktops equipped with an **EVGA GeForce GTX 1060 GAMING ACX 2.0 (Single Fan) with 6GB GDDR5 VRAM**) and evaluates their suitability for the different phases of the system (Phase 1: Specification Generation, Phase 2: Code Implementation, Phase 3: Enhancement).

Based on hardware constraints and recent benchmarks, running models locally is primarily a hardware optimization problem. The core principle is: *Pick the highest-quality model that still hits a usable tokens-per-second on the hardware you own.*

## Hardware Constraints (6GB VRAM)

The 6GB VRAM ceiling places your system in the lower end of **Tier 2 (8GB to 12GB VRAM)**, verging on **Tier 1 (CPU-only / Entry)** limits when accounting for the KV cache.

- **Weights:** A 7B model at 4-bit quantization (Q4_K_M) requires about 4GB of VRAM just for the weights.
- **KV Cache:** The Context Window uses VRAM. A larger context window quickly consumes the remaining 2GB of VRAM.
- **Offloading:** If the model + KV cache exceeds 6GB, the system spills to system RAM over PCIe, causing a massive collapse in throughput (speed).

## 1. Local Models (Ollama)

Spite primarily relies on local LLMs orchestrated via Ollama to maintain a true "cleanroom" environment without external data leakage.

### 1.1 The Safe Bets (High Speed, Fits Comfortably)

These models will comfortably fit within your 6GB VRAM limit, leaving plenty of headroom for the KV cache (allowing for larger context windows, useful for coding and RAG).

- **Phi-4-mini-instruct (3.8B)**

  - **Why:** Microsoft built this specifically to run on constrained hardware (even CPU-only). At Q4, it only needs a couple of gigabytes of RAM.
  - **Use Case:** Everyday coding help, drafting, and general assistance. It is extremely fast and won't crash your GPU.

- **Qwopus-3.5-Coder-4B**

  - **Why:** The Qwen family is excellent for coding. This 4B model will easily fit in 6GB and provide a solid context window for agentic tasks.
  - **Use Case:** Agentic coding and tasks requiring longer context windows without hitting OOM (Out Of Memory) errors.

- **Minimax-m2.7 (2.7B)**

  - **Why:** A highly compact model that uses even less VRAM, leaving near-maximal headroom for the KV cache.
  - **Pros:** Exceptional token-per-second performance. Highly efficient for rapid iteration in constrained environments.
  - **Cons:** Struggles with complex reasoning, high-level architectural orchestration, and strict, nuanced coding standards compared to 7B/8B class models.
  - **Use Case:** Very focused single-file changes or environments where larger models constantly OOM.

### 1.2 The Limit Pushers (Best Quality, Tight Fit)

These models represent the absolute ceiling of what a 6GB card can run. You *must* use aggressive quantization (Q4_K_M) and strictly limit your context window to prevent spilling to system RAM.

- **Llama 3 (8B) / Llama 3.3 8B at Q4_K_M - **Default****

  - Llama 3 is the default and a strong, general-purpose instruction-following model used by Spite.
  - **Pros:** Good at general reasoning, summarization, and formatting (e.g., Markdown generation). Sufficiently capable of managing the Q&A loop between Dirty and Clean agents.
  - **Cons:** May sometimes struggle with highly complex architectural decisions or strict, nuanced coding standards compared to specialized coding models. Very tight fit on 6GB VRAM.
  - **Best Used For:** All phases, but particularly effective in Phase 1 (Specification Generation) where general reasoning and document structuring are paramount.

- **Qwen 2.5-Coder 7B (or Qwen3 7B) at Q4_K_M**

  - Qwen 2.5 Coder is a specialized model focused heavily on code generation and understanding.
  - **Pros:** Often produces highly accurate code with fewer syntax errors in strict environments. Can be faster at generating code blocks compared to general-purpose models of similar size.
  - **Cons:** While great at coding, it may sometimes struggle with the high-level orchestration, planning, and conversational nuances required in the Clean/Dirty agent Q&A loop.
  - **Best Used For:** Phase 2 (Code Implementation) and Phase 3 (Enhancement) where the primary task is translating well-defined specifications into working code or refactoring existing code.
  - **Warning:** You will need to carefully monitor your context size. If you feed it too large of a document, it will exceed 6GB and drastically slow down.

### 1.3 CPU-Only Alternatives

If you encounter tasks that require a massive context window (e.g., analyzing an entire codebase), you might need to run the model purely on your CPU.

- **Performance:** Expect roughly 5 to 15 tokens per second (batch-like speed, not interactive).
- **When to use:** When the required memory exceeds your 6GB GPU limit, but fits within your system RAM.

## 2. Cloud Providers

While Spite focuses on local execution, it supports cloud providers via API keys as secondary options or for premium performance when local hardware is insufficient.

### 2.1 OpenAI (GPT-4o)

- **Pros:** Industry-leading reasoning, coding, and context management. Nearly flawless execution of all Spite phases.
- **Cons:** Breaks the strict "local" cleanroom paradigm. Incurs API costs. Requires an active internet connection.

### 2.2 Anthropic (Claude 3.5 Sonnet)

- **Pros:** Exceptional at coding, architectural design, and following complex system prompts. Often outperforms GPT-4o in specific coding tasks.
- **Cons:** Same as GPT-4o (privacy concerns, cost, requires internet).

## Configuration

Spite now supports selecting these models via the UI, powered by a local configuration file (`models.json`). You can customize the models available in the dropdown by editing this file.

For the best experience, ensure you have pulled the respective models using Ollama (e.g., `ollama pull phi-4-mini-instruct`).
