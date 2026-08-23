"""Secondary detection backend: sathishphdai/cybersecurity-slm-5m.

Unlike the two Gemma models, this one is NOT GGUF and is not Ollama-loadable
- it's a from-scratch ~34M parameter LLaMA-style transformer distributed as
safetensors, so it has to be loaded directly via the `transformers` library.
It's wired in as a genuine, selectable backend (DETECTION_BACKEND=transformers)
rather than just documented and ignored, so the third mandated model is
actually usable - e.g. as an offline/no-Ollama-dependency fallback, at the
cost of a much smaller model's analysis quality.
"""
import os

from .errors import DetectionBackendError
from prompt import SYSTEM_PROMPT

MODEL_NAME = os.getenv("TRANSFORMERS_DETECTION_MODEL", "sathishphdai/cybersecurity-slm-5m")

_tokenizer = None
_model = None


def _load():
    global _tokenizer, _model
    if _model is not None:
        return
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    except Exception as exc:
        raise DetectionBackendError(
            f"Could not load transformers model '{MODEL_NAME}': {exc}"
        ) from exc


def infer(prompt: str) -> str:
    _load()
    try:
        import torch

        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        inputs = _tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=1024)
        with torch.no_grad():
            output_ids = _model.generate(
                **inputs,
                max_new_tokens=200,
                do_sample=False,
                pad_token_id=_tokenizer.eos_token_id,
            )
        generated = _tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return generated
    except Exception as exc:
        raise DetectionBackendError(f"Inference with '{MODEL_NAME}' failed: {exc}") from exc
