#!/usr/bin/env python3
"""
ollama_api_example.py — Query Ollama's REST API from Python.
Requires Ollama to be running:  ollama serve

Install dependency:
  pip install requests
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "tinyllama"
PROMPT     = "Explain GPIO pins like I'm 5 years old."

payload = {
    "model": MODEL,
    "prompt": PROMPT,
    "stream": False,
}

print(f"Asking {MODEL}: {PROMPT}\n")
response = requests.post(OLLAMA_URL, json=payload, timeout=120)
response.raise_for_status()

print(response.json()["response"])
