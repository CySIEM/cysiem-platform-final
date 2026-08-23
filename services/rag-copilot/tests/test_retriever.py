"""Verifies the FAISS index loads correctly regardless of the process's
working directory - this is exactly the bug the original
ai-services/rag/retriever.py had (it hardcoded a cwd-relative path)."""
import os

from rag.retriever import search


def test_search_returns_relevant_document_from_any_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = search("brute force ssh login attack", k=2)

    assert len(results) > 0
    assert all("filename" in doc and "content" in doc for doc in results)


def test_search_finds_brute_force_doc():
    results = search("repeated failed password attempts brute force", k=3)
    filenames = [doc["filename"] for doc in results]
    assert "brute_force.md" in filenames
