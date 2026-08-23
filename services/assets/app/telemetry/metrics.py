"""Prometheus metrics for Layer 3 - request counts/latency and pipeline
throughput (entities/IOCs processed), scraped from /metrics.
"""
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "cysiem_layer3_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram(
    "cysiem_layer3_request_latency_seconds", "Request latency in seconds", ["path"]
)
ENTITIES_EXTRACTED = Counter(
    "cysiem_layer3_entities_extracted_total", "Entities extracted", ["entity_type"]
)
IOCS_MATCHED = Counter(
    "cysiem_layer3_iocs_matched_total", "Malicious IOC matches", ["source"]
)


def metrics_response() -> bytes:
    return generate_latest()
