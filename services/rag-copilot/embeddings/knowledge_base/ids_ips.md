# Intrusion Detection and Prevention System (IDS/IPS)

## Description
IDS detects suspicious or malicious activities on a network, while IPS actively blocks or prevents those attacks in real time.

## Common Indicators
- Signature match alerts
- Port scanning detection
- Malware traffic
- Exploit attempts
- Unauthorized access attempts

## Severity
High

## MITRE ATT&CK
- T1046 - Network Service Discovery
- T1190 - Exploit Public-Facing Application

## Prevention
- Deploy IDS/IPS sensors
- Keep signatures updated
- Monitor alerts continuously
- Integrate with SIEM
- Tune detection rules

## Detection
Analyze IDS/IPS alerts, network traffic, and correlated SIEM events.

## Example
An IPS detects a SQL Injection attack against a web server and blocks the malicious request before it reaches the application.