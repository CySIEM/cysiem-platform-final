# Indicators of Compromise (IOC)

## Description
Indicators of Compromise (IOCs) are pieces of forensic evidence that suggest a system, network, or endpoint may have been compromised by malicious activity.

## Common Indicators
- Malicious IP addresses
- Suspicious domain names
- File hashes (MD5, SHA1, SHA256)
- Unexpected processes
- Registry modifications

## Severity
High

## MITRE ATT&CK
- T1071 - Application Layer Protocol
- T1105 - Ingress Tool Transfer

## Prevention
- Continuously monitor network traffic
- Update threat intelligence feeds
- Block known malicious IPs and domains
- Perform regular endpoint scans
- Deploy EDR solutions

## Detection
Use SIEM, EDR, IDS/IPS, and threat intelligence platforms to detect IOCs.

## Example
A workstation repeatedly communicates with a known malicious IP address listed in a threat intelligence feed.