from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from client import forward_events
from normalize import normalize_batch

app = FastAPI(
    title="CySIEM Collection & Processing",
    version="1.0.0",
    description="Layer 1 (Data Collection) + Layer 2 (Data Processing/Normalization)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RawIngestRequest(BaseModel):
    source_type: Literal["linux", "windows", "network"]
    records: List[Any]
    tenant_id: str = "default"
    forward: bool = True


class RawIngestResult(BaseModel):
    records_received: int
    events_normalized: int
    events_dropped: int
    forward_result: Optional[Dict[str, Any]] = None


@app.get("/")
def home():
    return {"message": "CySIEM Collection & Processing running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ingest/raw", response_model=RawIngestResult)
def ingest_raw(payload: RawIngestRequest):
    try:
        events = normalize_batch(payload.records, payload.source_type, tenant_id=payload.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    forward_result = None
    if payload.forward and events:
        try:
            forward_result = forward_events(events)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Normalized {len(events)} events but forwarding to assets service failed: {exc}"
            ) from exc

    return RawIngestResult(
        records_received=len(payload.records),
        events_normalized=len(events),
        events_dropped=len(payload.records) - len(events),
        forward_result=forward_result,
    )


@app.post("/ingest/file", response_model=RawIngestResult)
async def ingest_file(
    file: UploadFile,
    source_type: Literal["linux", "windows", "network"] = "linux",
    tenant_id: str = "default",
    forward: bool = True,
):
    content = (await file.read()).decode("utf-8", errors="replace")
    lines = [line for line in content.splitlines() if line.strip()]

    try:
        events = normalize_batch(lines, source_type, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    forward_result = None
    if forward and events:
        try:
            forward_result = forward_events(events)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Normalized {len(events)} events but forwarding to assets service failed: {exc}"
            ) from exc

    return RawIngestResult(
        records_received=len(lines),
        events_normalized=len(events),
        events_dropped=len(lines) - len(events),
        forward_result=forward_result,
    )
