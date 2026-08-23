# API Contracts (original planning doc)

> **This document is the pre-implementation plan, written before any team
> had built anything.** It does not match what was actually implemented.
> See [../docs/integration-report.md](integration-report.md) for the real,
> as-built contracts between every service, and why they differ from what's
> below. Kept here for historical reference only.

This document defines how different teams communicate with each other.

---

## Team 1 → Team 2

Output

```json
{
  "timestamp": "",
  "source_ip": "",
  "destination_ip": "",
  "protocol": "",
  "event": ""
}
```

---

## Team 2 → Team 3

Output

```json
{
  "user": "",
  "device": "",
  "asset": "",
  "ip": "",
  "vulnerabilities": [],
  "ioc": []
}
```

---

## Team 3 → Team 4

Output

```json
{
  "prediction": "",
  "confidence": 0.95,
  "mitre": "",
  "reason": ""
}
```

---

## Team 4 → Team 5

Output

```json
{
  "incident_id": "",
  "severity": "",
  "timeline": [],
  "attack_chain": []
}
```

---

## Team 5 → Team 6

Output

```json
{
  "summary": "",
  "recommendation": "",
  "references": [],
  "cve": [],
  "mitre": []
}
```

---

All APIs should return JSON responses and use HTTP status codes properly.
