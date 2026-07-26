# Database Schema

This document will be updated as the project progresses.

---

## Planned Tables

### Logs

Stores normalized security logs.

### Assets

Stores discovered assets.

### Users

Stores user information.

### Incidents

Stores correlated incidents.

### AI Results

Stores AI detection outputs.

### Knowledge Base

Stores indexed RAG documents.

---

## Relationships

```
Logs
 │
 ▼
Assets
 │
 ▼
Incidents
 │
 ▼
AI Recommendations
```

---

The final schema will be updated during implementation.
