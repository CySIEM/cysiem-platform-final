"""Regex-based entity extraction from raw or normalized log text.

Detects the entity types Team 2 / Layer 3 is responsible for: IPs, hostnames,
MAC addresses, usernames, domains, URLs, file hashes, CVEs, ports, and emails.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from app.core.constants import EntityType

_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
# Matches both colon-separated (00:0c:29:c1:57:a5, Linux/most tools) and
# dash-separated (00-0C-29-83-62-83, Windows ipconfig/eventlog style) MACs -
# both forms showed up in real asset inventory data during validation.
_MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_HOSTNAME = re.compile(r"\b(?:HOST|DESKTOP|SRV|WIN|DC|SVR)-[A-Za-z0-9\-]{2,20}\b", re.IGNORECASE)
_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
_DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"(?:com|net|org|io|ru|cn|biz|info|xyz|top|gov|edu)\b"
)
_URL = re.compile(r"\bhttps?://[^\s\"'<>]+")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
_SHA1 = re.compile(r"\b[a-fA-F0-9]{40}\b")
_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")
_PORT = re.compile(r"(?:port|dport|sport)[=:\s]+(\d{1,5})", re.IGNORECASE)
_USERNAME = re.compile(r"(?:user|username|acct|account)[=:\s]+([A-Za-z0-9._\-]{2,32})", re.IGNORECASE)


@dataclass
class ExtractedEntity:
    entity_type: EntityType
    value: str
    confidence: float = 1.0
    context: str = field(default="")


class EntityExtractor:
    """Extracts typed entities out of a single log line / normalized record."""

    def extract(self, text: str) -> List[ExtractedEntity]:
        """Full extraction, including the contextual key=value patterns
        (PORT, USERNAME). Best suited to key=value-style log text
        (firewall/IDS lines: `SRC=`, `port=`, `user=`) where those keywords
        reliably mean what they say.
        """
        if not text:
            return []
        results = self._value_pattern_matches(text)
        results += self._group_match(_PORT, EntityType.PORT, text, confidence=0.7)
        results += self._group_match(_USERNAME, EntityType.USERNAME, text, confidence=0.8)
        return self._dedupe(results)

    def extract_narrative(self, text: str) -> List[ExtractedEntity]:
        """Extraction for free-text/prose fields (Windows event descriptions,
        auditd human-readable messages) where PORT/USERNAME's keyword+value
        pattern produces false positives - narrative English sentences like
        "a user performs a read operation" or "Account Name: WIN11-01$"
        trip `user=`/`account=`-style matching even though nothing there is
        actually a key=value pair. Only the unambiguous value-pattern
        entities (IP, MAC, hostname, CVE, URL, email, domain, hash) are
        extracted here - structured fields should supply user/port instead.
        """
        if not text:
            return []
        return self._dedupe(self._value_pattern_matches(text))

    @staticmethod
    def _value_pattern_matches(text: str) -> List[ExtractedEntity]:
        results: List[ExtractedEntity] = []
        results += EntityExtractor._match(_IPV4, EntityType.IP_ADDRESS, text)
        results += EntityExtractor._match(_MAC, EntityType.MAC_ADDRESS, text)
        results += EntityExtractor._match(_HOSTNAME, EntityType.HOSTNAME, text)
        results += EntityExtractor._match(_CVE, EntityType.CVE, text, confidence=0.95)
        results += EntityExtractor._match(_URL, EntityType.URL, text, confidence=0.9)
        results += EntityExtractor._match(_EMAIL, EntityType.EMAIL, text, confidence=0.9)
        results += EntityExtractor._match(_DOMAIN, EntityType.DOMAIN, text, confidence=0.8)
        results += EntityExtractor._match(_SHA256, EntityType.FILE_HASH, text, confidence=0.99)
        results += EntityExtractor._match(_SHA1, EntityType.FILE_HASH, text, confidence=0.9)
        results += EntityExtractor._match(_MD5, EntityType.FILE_HASH, text, confidence=0.85)
        return results

    @staticmethod
    def _match(pattern: re.Pattern, entity_type: EntityType, text: str, confidence: float = 1.0) -> List[ExtractedEntity]:
        return [
            ExtractedEntity(entity_type=entity_type, value=m.group(0), confidence=confidence, context=text[:200])
            for m in pattern.finditer(text)
        ]

    @staticmethod
    def _group_match(pattern: re.Pattern, entity_type: EntityType, text: str, confidence: float = 1.0) -> List[ExtractedEntity]:
        return [
            ExtractedEntity(entity_type=entity_type, value=m.group(1), confidence=confidence, context=text[:200])
            for m in pattern.finditer(text)
        ]

    @staticmethod
    def _dedupe(entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        seen = set()
        unique: List[ExtractedEntity] = []
        for e in entities:
            key = (e.entity_type, e.value.lower())
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique


entity_extractor = EntityExtractor()
