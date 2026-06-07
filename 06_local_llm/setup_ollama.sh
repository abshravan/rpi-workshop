#!/usr/bin/env bash
# setup_ollama.sh — Install Ollama and pull a small LLM that fits on a Pi.
# Run on the Raspberry Pi (requires internet for initial download).

set -e

echo "=== Installing Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo ""
echo "=== Pulling TinyLlama (1.1 B params — fastest on Pi) ==="
ollama pull tinyllama

echo ""
echo "=== Ollama is ready! ==="
echo "Start an interactive chat:   ollama run tinyllama"
echo "Or start the API server:     ollama serve"
