# CySIEM Architecture

## Overview

CySIEM is an AI-powered Security Information and Event Management (SIEM) platform designed to collect, process, analyze, correlate, and visualize security events.

The platform follows a modular architecture where each team is responsible for a specific layer of the workflow.

## Architecture

```
Security Data Sources
        │
        ▼
Layer 1 - Data Collection
        │
        ▼
Layer 2 - Data Processing
        │
        ▼
Layer 3 - Asset Intelligence
        │
        ▼
Layer 4 - AI Detection
        │
        ▼
Layer 5 - Correlation
        │
        ▼
Layer 6 - Investigation
        │
        ▼
Layer 7 - Knowledge Fabric (RAG)
        │
        ▼
Layer 8 - AI Security Copilot
        │
        ▼
Layer 9 - Dashboard
        │
        ▼
Layer 10 - Response & Learning
```

## Technologies

- Python
- FastAPI
- Ollama
- Hugging Face Models
- ChromaDB / FAISS
- React
- Docker

## Design Principles

- Modular
- Scalable
- AI-first
- Easy integration
- Reusable APIs
