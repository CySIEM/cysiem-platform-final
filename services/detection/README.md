# CySIEM Layer 4 - Detection Fabric

New service (no Team 3 code existed anywhere in the source repositories
audited for this integration - see `/docs/integration-report.md`). Consumes
a normalized event plus its entity/asset context (from `services/assets`),
classifies it using one of the three manager-mandated Hugging Face security
SLMs, and forwards the result to `services/correlation`.

## The three mandated models - exactly how each loads

Verified directly against each model's Hugging Face repo before writing any
code, per the project's explicit instruction not to assume `ollama pull
model-name` just works:

| Model | Format | How it's actually loaded here |
|---|---|---|
| `entrick/Security-SLM-Gemma-4-E2B-it-GGUF` (default) | GGUF (Q4_K_M, 3.43GB), ships its own Ollama Modelfile in the repo | `ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M` - Ollama's native "pull straight from a HF repo" support reads that Modelfile automatically. No manual Modelfile authoring needed. |
| `Nguuma/Security-SLM-Gemma-4-E2B-it-GGUF` (alternate) | Same - GGUF, Q4_K_M, embedded chat template, no separate model card | `ollama pull hf.co/Nguuma/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M` |
| `sathishphdai/cybersecurity-slm-5m` | **Not GGUF** - safetensors, ~34M param from-scratch LLaMA-style transformer | **Not Ollama-loadable.** Loaded directly via `transformers.AutoModelForCausalLM`/`AutoTokenizer`. Selected via `DETECTION_BACKEND=transformers`. Genuinely wired in (`backends/transformers_backend.py`), not just mentioned - this is how the third mandated model gets actually used, e.g. as a lightweight, Ollama-free fallback. Expect noticeably lower-quality output than the two Gemma models given its size. |

Switch between the two Gemma variants or the tiny transformers model purely
via `.env` (`DETECTION_BACKEND`, `DETECTION_MODEL` /
`TRANSFORMERS_DETECTION_MODEL`) - no code changes needed.

## Setup

```bash
# Ollama backend (default):
ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M
pip install -r requirements.txt

# Transformers backend (lightweight/offline alternative):
pip install -r requirements.txt torch transformers
# then set DETECTION_BACKEND=transformers in .env

cp .env.example .env
uvicorn app:app --reload --port 8000
```

Hardware: the Gemma GGUF model is a 4-bit quantized ~5B-parameter model -
runs on CPU but is meaningfully faster with a GPU Ollama can use; needs
~4GB free RAM/VRAM plus the 3.43GB download. The transformers model
(~34M params) runs comfortably on CPU with no GPU or large download needed.

## API

`POST /detect` - `{"event": {...NormalizedEvent...}, "entities": [...],
"assets": [...], "forward": true}`. Builds a JSON-classification prompt,
calls the configured model, parses `{prediction, confidence, severity,
mitre, reason}` out of its response (falling back to keyword heuristics if
the model doesn't return parseable JSON), and returns:

- `layer4_output` - the documented Layer 4 -> Layer 5 contract:
  `{detection, severity, confidence, entities, evidence}`
- `correlation_alert` - the same result mapped into the raw alert-dict
  shape `services/correlation`'s `POST /ingest` actually expects (there's
  no formal schema on that side - shape read directly from its
  `correlation/normalize.py` / `facts.py` / `severity.py`)
- `forward_result` - the correlation service's response, if `forward: true`
  (default) actually POSTed the alert there

`GET /health`

## Tests

```bash
pytest -v
```

Tests mock the model backend entirely (no live Ollama/transformers call),
covering prompt building, response parsing (including the malformed-output
fallback), and the Team 4 field-shape adapter.
