"""Primary detection backend: one of the two manager-mandated Gemma-based
security SLMs, served through Ollama.

Both entrick/Security-SLM-Gemma-4-E2B-it-GGUF and
Nguuma/Security-SLM-Gemma-4-E2B-it-GGUF ship as GGUF files WITH their own
Ollama Modelfile already in the HF repo, so - unlike a plain HF transformers
checkpoint - they don't need a hand-authored Modelfile here. Ollama's
native "pull straight from a Hugging Face repo" support handles it:

    ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M

DETECTION_MODEL selects which one this backend calls (see .env.example for
both model names). See services/detection/README.md for the full setup.
"""
import os

import ollama

from .errors import DetectionBackendError
from prompt import SYSTEM_PROMPT

DETECTION_MODEL = os.getenv(
    "DETECTION_MODEL", "hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M"
)


def infer(prompt: str) -> str:
    try:
        response = ollama.chat(
            model=DETECTION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]
    except Exception as exc:
        raise DetectionBackendError(
            f"Could not reach Ollama model '{DETECTION_MODEL}': {exc}"
        ) from exc
