"""Regression test against a real (trimmed) Team 1 export sample -
tests/fixtures/sample_normalized_events.json is a 62-record slice of an
actual auditd + Windows eventlog export, covering 17 distinct event
actions. This is what caught the MAC-dash-format bug and the
narrative-text username false positives during development - keeping it
as a permanent test guards against regressing either.
"""
import json
from pathlib import Path

from app.core.normalized_event_mapper import build_asset_context, extract_entities, is_failed_event
from app.schemas.normalized_event import NormalizedEvent

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_normalized_events.json"

# Known-bad values a correct extractor must never produce, given this
# fixture - regression guard for the narrative-text false-positive bug.
_FORBIDDEN_USERNAMES = {"Name", "Domain", "Account", "performs", "reads", "user", "Security"}


def _load_fixture() -> list[dict]:
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


def test_fixture_file_exists_and_is_nonempty():
    events = _load_fixture()
    assert len(events) > 50


def test_every_fixture_event_parses_without_error():
    events = _load_fixture()
    errors = []
    for raw in events:
        try:
            event = NormalizedEvent.model_validate(raw)
            extract_entities(event)
            if event.source.host:
                build_asset_context(event)
            is_failed_event(event)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{raw.get('event_id')}: {exc}")
    assert errors == [], f"{len(errors)} fixture events failed to map: {errors[:5]}"


def test_no_narrative_false_positive_usernames_in_fixture():
    events = _load_fixture()
    all_usernames = set()
    for raw in events:
        event = NormalizedEvent.model_validate(raw)
        entities = extract_entities(event)
        all_usernames |= {e.value for e in entities if e.entity_type.value == "username"}
    assert not (all_usernames & _FORBIDDEN_USERNAMES), all_usernames & _FORBIDDEN_USERNAMES


def test_mac_addresses_extracted_from_fixture():
    events = _load_fixture()
    all_macs = set()
    for raw in events:
        event = NormalizedEvent.model_validate(raw)
        if event.source.host:
            ctx = build_asset_context(event)
            all_macs |= set(ctx["mac_addresses"])
    assert len(all_macs) > 0
