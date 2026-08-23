import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from adapter import build_correlation_alert, build_layer4_output
from backends import get_backend
from backends.errors import DetectionBackendError
from client import forward_alert
from prompt import build_prompt
from response_parser import parse_model_response

AUTO_FORWARD = os.getenv("AUTO_FORWARD", "true").lower() == "true"

app = FastAPI(
    title="CySIEM Detection Fabric",
    version="1.0.0",
    description="Layer 4 - AI-based threat detection using a Hugging Face security SLM",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DetectRequest(BaseModel):
    event: Dict[str, Any]
    entities: List[Any] = []
    assets: List[Any] = []
    forward: bool = AUTO_FORWARD


class DetectResponse(BaseModel):
    layer4_output: Dict[str, Any]
    correlation_alert: Dict[str, Any]
    forward_result: Dict[str, Any] | None = None


@app.get("/")
def home():
    return {"message": "CySIEM Detection Fabric running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/detect", response_model=DetectResponse)
def detect(request: DetectRequest):
    infer = get_backend()
    prompt = build_prompt(request.event, request.entities, request.assets)

    try:
        raw_response = infer(prompt)
    except DetectionBackendError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    detection = parse_model_response(raw_response)
    layer4_output = build_layer4_output(request.event, detection, request.entities, request.entities)
    correlation_alert = build_correlation_alert(request.event, detection)

    forward_result = None
    if request.forward:
        try:
            forward_result = forward_alert(correlation_alert)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Detection succeeded but forwarding to correlation service failed: {exc}",
            ) from exc

    return DetectResponse(
        layer4_output=layer4_output,
        correlation_alert=correlation_alert,
        forward_result=forward_result,
    )
