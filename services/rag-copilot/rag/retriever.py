"""Loads the FAISS security knowledge-base index and exposes similarity search.

Team 5's original version resolved "vector_db/security_index.faiss" relative
to the process's current working directory, which only worked when run from
inside ai-services/embeddings/. Paths here are resolved relative to this
file so the service works regardless of where it's launched from (uvicorn
from the service root, a test runner, Docker, etc).
"""
from pathlib import Path
import pickle

import faiss
from sentence_transformers import SentenceTransformer

_VECTOR_DB_DIR = Path(__file__).resolve().parent.parent / "embeddings" / "vector_db"

_model = None
_index = None
_documents = None


def _load():
    global _model, _index, _documents
    if _index is not None:
        return
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    _index = faiss.read_index(str(_VECTOR_DB_DIR / "security_index.faiss"))
    with open(_VECTOR_DB_DIR / "documents.pkl", "rb") as f:
        _documents = pickle.load(f)


def search(query: str, k: int = 3):
    """Return the top-k knowledge-base documents most similar to query."""
    _load()
    query_embedding = _model.encode([query])
    distances, indices = _index.search(query_embedding, k)

    results = []
    for i in indices[0]:
        if i != -1:
            results.append(_documents[i])
    return results
