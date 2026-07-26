# AI Architecture

## Overview

The AI layer is responsible for analyzing security events, detecting threats, generating explanations, and assisting analysts using Retrieval-Augmented Generation (RAG).

---

## AI Pipeline

```
Normalized Logs
        │
        ▼
Entity Extraction
        │
        ▼
Security LLM
        │
        ▼
Threat Detection
        │
        ▼
Incident Correlation
        │
        ▼
RAG
        │
        ▼
AI Security Copilot
```

---

## Components

### Detection Model

Responsible for identifying malicious activities.

### RAG Pipeline

Retrieves cybersecurity knowledge before generating responses.

### AI Security Copilot

Provides:

- Threat explanations
- Security recommendations
- MITRE ATT&CK mapping
- CVE references
- OWASP references

---

## Models

- Ollama
- Hugging Face Security SLM
- Embedding Model

---

## Future Improvements

- Multiple LLM support
- Model evaluation
- Fine-tuning
