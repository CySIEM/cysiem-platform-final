# RAG Design

## Overview

The Retrieval-Augmented Generation (RAG) system enhances AI responses by retrieving relevant cybersecurity knowledge before generating answers.

---

## Workflow

```
User Query
      │
      ▼
Embedding
      │
      ▼
Vector Search
      │
      ▼
Relevant Documents
      │
      ▼
LLM
      │
      ▼
Response
```

---

## Knowledge Sources

- MITRE ATT&CK
- CVE Database
- OWASP
- Internal Security Documentation
- Incident Reports

---

## Components

- Document Loader
- Chunking
- Embeddings
- Vector Database
- Retriever
- Generator

---

## Possible Vector Databases

- ChromaDB
- FAISS
- Qdrant

---

## Goal

Provide accurate and context-aware security recommendations.
