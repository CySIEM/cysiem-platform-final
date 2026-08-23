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
| `sathishphdai/cybersecurity-slm-5m` | **Not GGUF, and not `AutoModelForCausalLM`-compatible either** - safetensors, ~34M param from-scratch LLaMA-style transformer with a custom `model_type: "cybersecurity-slm"` that isn't a registered HF architecture | Confirmed by an actual failed load attempt (`KeyError: 'cybersecurity-slm'`), then by reading the repo's own `chat.py`: it loads via a raw PyTorch class (`model.py`'s `IndustrySLM`) with weights read directly, tokenized with the low-level `tokenizers` library - not `from_pretrained()` at all. `backends/transformers_backend.py` downloads `model.py`/`config.py`/`model.safetensors`/`tokenizer.json` from the hub and follows that same path. Verified with a real live run: loads correctly (33.89M params, matching the model card) and generates on-topic (if rough - expected for a 34M-param from-scratch model) cybersecurity text in ~5 minutes on CPU. Selected via `DETECTION_BACKEND=transformers`. |

Switch between the two Gemma variants or the small custom-architecture model
purely via `.env` (`DETECTION_BACKEND`, `DETECTION_MODEL` /
`TRANSFORMERS_DETECTION_MODEL`) - no code changes needed.

## Setup

```bash
# Ollama backend (default):
ollama pull hf.co/entrick/Security-SLM-Gemma-4-E2B-it-GGUF:Q4_K_M
pip install -r requirements.txt

# Third-model backend (lightweight/offline alternative - see table above,
# it does NOT use the `transformers` library's model classes):
pip install -r requirements.txt torch huggingface_hub safetensors tokenizers
# then set DETECTION_BACKEND=transformers in .env

cp .env.example .env
uvicorn app:app --reload --port 8000
```

Hardware: the Gemma GGUF model is a 4-bit quantized ~5B-parameter model -
runs on CPU but is meaningfully faster with a GPU Ollama can use; needs
~4GB free RAM/VRAM plus the 3.43GB download. The `sathishphdai` model
(~34M params) needs no GPU and only a ~135MB download, but its reference
`generate()` implementation has no KV-cache, so a 200-token CPU response
takes several minutes - verified in a real run at ~5.4 minutes. Fine as a
lightweight/offline fallback, not for interactive-latency use.

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
