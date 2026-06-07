#!/usr/bin/env bash
# chat.sh — Quick-start an interactive LLM chat session.
# Requires Ollama to be installed (run setup_ollama.sh first).
#
# Available small models for Pi:
#   tinyllama   — 1.1 B params, ~700 MB, fastest
#   phi3:mini   — 3.8 B params, ~2.4 GB, smarter
#   gemma2:2b   — 2 B params,   ~1.6 GB, Google's model

MODEL="${1:-tinyllama}"

echo "Starting chat with: $MODEL  (Ctrl-D or /bye to quit)"
ollama run "$MODEL"
