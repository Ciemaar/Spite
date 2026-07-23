#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Pulling recommended models into Ollama..."

echo "Pulling llama3..."
ollama pull llama3

echo "Pulling qwen2.5-coder..."
ollama pull qwen2.5-coder

echo "Successfully pulled recommended models."
