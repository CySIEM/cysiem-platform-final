import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from investigation.timeline import build_timeline


def test_build_timeline_orders_events_by_time():
    alerts = [
        {"id": "a2", "timestamp": "2026-08-01T10:10:00Z", "title": "Second"},
        {"id": "a1", "timestamp": "2026-08-01T10:00:00Z", "title": "First"},
    ]

    timeline = build_timeline(alerts)

    assert timeline[0]["id"] == "a1"
    assert timeline[1]["id"] == "a2"
