"""Offline validation harness: runs the Layer 3 entity-extraction +
asset-context mapping logic (app/core/*) against real Team 1 export files,
with NO database required. Use this to sanity-check the pipeline against a
fresh batch of exports before wiring it into the live ingest endpoint.

Usage:
    python -m scripts.validate_against_real_logs path/to/export1.json [more.json ...]
"""
from __future__ import annotations

import json
import sys
from collections import Counter

from app.core.normalized_event_mapper import build_asset_context, extract_entities, is_failed_event
from app.schemas.normalized_event import NormalizedEvent


def validate(paths: list[str]) -> None:
    total_events = 0
    entity_type_counts: Counter = Counter()
    action_counts: Counter = Counter()
    log_type_counts: Counter = Counter()
    hosts_seen: dict[str, dict] = {}
    failed_events = 0
    parse_errors: list[str] = []

    for path in paths:
        with open(path) as fh:
            raw_events = json.load(fh)

        for raw in raw_events:
            total_events += 1
            try:
                event = NormalizedEvent.model_validate(raw)
                entities = extract_entities(event)
                for e in entities:
                    entity_type_counts[e.entity_type.value] += 1
                action_counts[event.normalized.action] += 1
                log_type_counts[event.source.log_type] += 1
                if is_failed_event(event):
                    failed_events += 1
                if event.source.host:
                    ctx = build_asset_context(event)
                    existing = hosts_seen.setdefault(event.source.host, {
                        "ips": set(), "macs": set(), "users": set(), "tags": set()
                    })
                    existing["ips"] |= set(ctx["ip_addresses"])
                    existing["macs"] |= set(ctx["mac_addresses"])
                    existing["users"] |= set(ctx["usernames"])
                    existing["tags"] |= set(ctx["tags"])
            except Exception as exc:  # noqa: BLE001
                parse_errors.append(f"{path}: event_id={raw.get('event_id', '?')} -> {exc}")

    print("=" * 70)
    print("LAYER 3 VALIDATION REPORT — real log export sample")
    print("=" * 70)
    print(f"Files processed:      {len(paths)}")
    print(f"Total events:         {total_events}")
    print(f"Parse errors:         {len(parse_errors)}")
    print(f"Failed-outcome events: {failed_events}")
    print()
    print("-- Log types seen --")
    for lt, c in log_type_counts.most_common():
        print(f"  {lt or '(none)':<22} {c}")
    print()
    print("-- Top 15 actions seen --")
    for act, c in action_counts.most_common(15):
        print(f"  {act or '(none)':<28} {c}")
    print()
    print("-- Entities extracted, by type --")
    for et, c in entity_type_counts.most_common():
        print(f"  {et:<14} {c}")
    print()
    print(f"-- Assets (hosts) resolved: {len(hosts_seen)} --")
    for host, ctx in hosts_seen.items():
        print(f"  {host}")
        print(f"      ip_addresses: {sorted(ctx['ips'])}")
        print(f"      mac_addresses: {sorted(ctx['macs'])}")
        print(f"      usernames:    {sorted(ctx['users'])}")
        print(f"      tags:         {sorted(ctx['tags'])}")
    print()
    if parse_errors:
        print("-- Parse errors (first 10) --")
        for err in parse_errors[:10]:
            print(f"  {err}")
    else:
        print("No parse errors — every event in the sample mapped cleanly.")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.validate_against_real_logs <file1.json> [file2.json ...]")
        sys.exit(1)
    validate(sys.argv[1:])
