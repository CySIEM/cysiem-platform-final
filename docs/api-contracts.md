# API Contracts

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
