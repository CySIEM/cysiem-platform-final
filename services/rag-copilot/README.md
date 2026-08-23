# CySIEM Layer 7/8 - Knowledge Fabric (RAG) & AI Security Copilot

Team 5 deliverable, integrated. Retrieves security knowledge from a FAISS
index built over a hand-authored knowledge base (`embeddings/knowledge_base/`)
and uses it to ground an Ollama chat model's answers.

Only the RAG + Copilot pieces of Team 5's original submission are included
here. Their `backend/` also contained draft dashboard/alerts/threats/reports/
assets/investigation routers that duplicate Team 2/4/6's actual scope (Layer
7-8 is RAG + Copilot only) - those were left out of the integrated system as
unused exploratory work, not silently deleted (still present in the original
`cysiem-platform-team5-rag` folder).

## What changed from the original Team 5 code

- `backend/requirements.txt` was corrupted (UTF-16 encoded, unreadable by pip)
  and missing the packages the RAG code actually imports (`faiss`,
  `sentence-transformers`, `ollama`). Rewritten as `requirements.txt` here.
- `ai-services/rag/retriever.py` loaded the FAISS index via a path relative to
  the process's working directory, so it only worked when launched from
  inside `ai-services/embeddings/`. `rag/retriever.py` here resolves the
  index path relative to the file itself.
- `backend/services/team5_service.py` was a hardcoded keyword-matcher never
  actually connected to the RAG pipeline Team 5 had already built in
  `ai-services/copilot/app.py`. `services/copilot_service.py` here is that
  real pipeline, made reachable through `POST /ask/` instead of living as a
  disconnected standalone script.
- Added `POST /copilot/explain-incident`, which the correlation service's
  incident output can be fed into directly to get a narrative summary, risk
  score, and recommended actions (the Layer 8 -> Layer 9 contract).

## Run

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 8000
```

Requires a running Ollama instance (`ollama serve`) with `COPILOT_MODEL`
(default `llama3.2`) pulled: `ollama pull llama3.2`.

The prebuilt FAISS index at `embeddings/vector_db/` is checked in. To rebuild
it after editing `embeddings/knowledge_base/*.md`:

```bash
cd embeddings && python create_embeddings.py
```

## Endpoints

- `GET /health`
- `POST /ask/` - `{"question": "..."}` -> RAG-grounded answer + source files
- `POST /copilot/explain-incident` - takes the correlation service's incident
  dict (e.g. the output of `GET /report/{incident_id}`) -> `{incident_id,
  summary, severity, risk_score, recommended_actions, references}`

## Why not the mandated security SLMs here

The three Hugging Face security SLMs the project manager specified are
scoped to Team 3's Detection Fabric (Layer 4) per the project's own team
breakdown, not the Copilot. This service keeps Team 5's original model
choice (Ollama `llama3.2`) for general-purpose retrieval-grounded
explanation; see `services/detection/README.md` for where the mandated
models are actually loaded and used.
