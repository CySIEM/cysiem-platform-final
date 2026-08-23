"""Secondary detection backend: sathishphdai/cybersecurity-slm-5m.

This model is NOT loadable through `transformers.AutoModelForCausalLM` -
verified directly against a live load attempt, which fails with
`KeyError: 'cybersecurity-slm'` because that model_type isn't a registered
HF architecture. The repo's own config.json declares
`"architectures": ["IndustrySLM"]`, and its own reference chat.py loads it
as a raw PyTorch nn.Module (`model.py`'s `IndustrySLM`, a from-scratch
LLaMA-style transformer with RoPE) via `torch.load()`, tokenized with the
low-level `tokenizers` library rather than `AutoTokenizer` - not the
standard `from_pretrained()` pattern at all.

This backend follows that same real loading path: download model.py,
config.py, the safetensors weights and tokenizer.json from the hub,
dynamically import the architecture, and load the published weights
directly into a fresh IndustrySLM instance. It's wired in as a genuine,
selectable backend (DETECTION_BACKEND=transformers) so the third mandated
model is actually usable - e.g. as a lightweight, Ollama-free fallback -
at the cost of a much smaller (~34M param) model's analysis quality.
"""
import importlib.util
import os
import sys

from huggingface_hub import hf_hub_download
from safetensors.torch import load_file as load_safetensors

from .errors import DetectionBackendError
from prompt import SYSTEM_PROMPT

MODEL_REPO = os.getenv("TRANSFORMERS_DETECTION_MODEL", "sathishphdai/cybersecurity-slm-5m")

_model = None
_tokenizer = None
_device = None


def _import_module_from_hub(repo_id: str, filename: str, module_name: str):
    """Downloads a .py file from the hub and imports it under module_name,
    so its own `from config import cfg` / `from model import IndustrySLM`
    style relative imports resolve against the sibling file also pulled
    from the same repo (both land in the same hub cache snapshot dir)."""
    path = hf_hub_download(repo_id=repo_id, filename=filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    # model.py does `from config import cfg` - the snapshot dir (path's
    # parent) has to be importable for that to resolve.
    snapshot_dir = os.path.dirname(path)
    if snapshot_dir not in sys.path:
        sys.path.insert(0, snapshot_dir)
    spec.loader.exec_module(module)
    return module


def _load():
    global _model, _tokenizer, _device
    if _model is not None:
        return

    try:
        import torch
        from tokenizers import Tokenizer

        # config.py must be importable as a bare "config" module before
        # model.py (which does `from config import cfg`) is exec'd.
        _import_module_from_hub(MODEL_REPO, "config.py", "config")
        model_module = _import_module_from_hub(MODEL_REPO, "model.py", "cysiem_slm5m_model")

        weights_path = hf_hub_download(repo_id=MODEL_REPO, filename="model.safetensors")
        state_dict = load_safetensors(weights_path)

        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = model_module.IndustrySLM()
        missing, unexpected = _model.load_state_dict(state_dict, strict=False)
        if missing:
            raise DetectionBackendError(
                f"'{MODEL_REPO}' weights are missing expected parameters: {missing[:5]}"
            )
        _model.to(_device).eval()

        tokenizer_path = hf_hub_download(repo_id=MODEL_REPO, filename="tokenizer.json")
        _tokenizer = Tokenizer.from_file(tokenizer_path)
    except DetectionBackendError:
        raise
    except Exception as exc:
        raise DetectionBackendError(f"Could not load '{MODEL_REPO}': {exc}") from exc


def infer(prompt: str) -> str:
    _load()
    try:
        import torch

        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        ids = _tokenizer.encode(full_prompt).ids
        input_ids = torch.tensor([ids], dtype=torch.long, device=_device)
        with torch.no_grad():
            output_ids = _model.generate(input_ids, max_new_tokens=200, temperature=0.7, top_k=50, top_p=0.9)
        generated_ids = output_ids[0][input_ids.shape[1]:].tolist()
        return _tokenizer.decode(generated_ids).replace("<eos>", "").replace("<pad>", "").strip()
    except Exception as exc:
        raise DetectionBackendError(f"Inference with '{MODEL_REPO}' failed: {exc}") from exc
