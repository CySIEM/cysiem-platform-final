from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.copilot import router as copilot_router

app = FastAPI(
    title="CySIEM RAG & AI Security Copilot",
    version="1.0.0",
    description="Layer 7 (Knowledge Fabric / RAG) + Layer 8 (AI Security Copilot)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot_router)


@app.get("/")
def home():
    return {"message": "CySIEM RAG & AI Security Copilot running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
