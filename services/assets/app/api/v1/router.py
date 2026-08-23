"""Aggregates all v1 endpoint routers under one APIRouter, mounted in
app/main.py under settings.api_v1_prefix.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import assets, entities, graph, health, ingest, iocs, vulnerabilities

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingest.router)
api_router.include_router(entities.router)
api_router.include_router(assets.router)
api_router.include_router(iocs.router)
api_router.include_router(vulnerabilities.router)
api_router.include_router(graph.router)
