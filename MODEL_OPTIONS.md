# Model Options for EVGA GeForce GTX 1060 (6GB VRAM)

This document outlines the recommended local AI models for the Spite project, specifically tailored for a desktop equipped with an **EVGA GeForce GTX 1060 GAMING ACX 2.0 (Single Fan) with 6GB GDDR5 VRAM**.

Based on hardware constraints and recent benchmarks, running models locally is primarily a hardware optimization problem. The core principle is: *Pick the highest-quality model that still hits a usable tokens-per-second on the hardware you own.*

## Hardware Constraints (6GB VRAM)

The 6GB VRAM ceiling places your system in the lower end of **Tier 2 (8GB to 12GB VRAM)**, verging on **Tier 1 (CPU-only / Entry)** limits when accounting for the KV cache.

- **Weights:** A 7B model at 4-bit quantization (Q4_K_M) requires about 4GB of VRAM just for the weights.
- **KV Cache:** The Context Window uses VRAM. A larger context window quickly consumes the remaining 2GB of VRAM.
- **Offloading:** If the model + KV cache exceeds 6GB, the system spills to system RAM over PCIe, causing a massive collapse in throughput (speed).

## Recommended Models

### 1. The Safe Bets (High Speed, Fits Comfortably)

These models will comfortably fit within your 6GB VRAM limit, leaving plenty of headroom for the KV cache (allowing for larger context windows, useful for coding and RAG).

- **Phi-4-mini-instruct (3.8B)**

  - **Why:** Microsoft built this specifically to run on constrained hardware (even CPU-only). At Q4, it only needs a couple of gigabytes of RAM.
  - **Use Case:** Everyday coding help, drafting, and general assistance. It is extremely fast and won't crash your GPU.

- **Qwopus-3.5-Coder-4B**

  - **Why:** The Qwen family is excellent for coding. This 4B model will easily fit in 6GB and provide a solid context window for agentic tasks.
  - **Use Case:** Agentic coding and tasks requiring longer context windows without hitting OOM (Out Of Memory) errors.

### 2. The Limit Pushers (Best Quality, Tight Fit)

These models represent the absolute ceiling of what a 6GB card can run. You *must* use aggressive quantization (Q4_K_M) and strictly limit your context window to prevent spilling to system RAM.

- **Qwen 2.5-Coder 7B (or Qwen3 7B) at Q4_K_M**

  - **Why:** The 7B Qwen coder models are incredibly capable for their size.
  - **Use Case:** Focused, concise coding tasks.
  - **Warning:** You will need to carefully monitor your context size. If you feed it too large of a document, it will exceed 6GB and drastically slow down.

- **Llama 3.3 8B at Q4_K_M**

  - **Why:** The standard for 8B models.
  - **Use Case:** General reasoning and instruction following.
  - **Warning:** Similar to the 7B models, 8B is a very tight fit on 6GB VRAM.

### 3. CPU-Only Alternatives

If you encounter tasks that require a massive context window (e.g., analyzing an entire codebase), you might need to run the model purely on your CPU.

- **Performance:** Expect roughly 5 to 15 tokens per second (batch-like speed, not interactive).
- **When to use:** When the required memory exceeds your 6GB GPU limit, but fits within your system RAM.

## Configuration

Spite now supports selecting these models via the UI, powered by a local configuration file (`models.json`). You can customize the models available in the dropdown by editing this file.

For the best experience, ensure you have pulled the respective models using Ollama (e.g., `ollama pull phi-4-mini-instruct`).
