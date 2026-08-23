# Domain Name System (DNS)

## Description
DNS translates human-readable domain names into IP addresses, enabling communication across the internet.

## Common Indicators
- DNS tunneling
- Suspicious DNS queries
- Requests to malicious domains
- High DNS traffic
- Unknown DNS servers

## Severity
Medium

## MITRE ATT&CK
- T1071.004 - DNS
- T1568 - Dynamic Resolution

## Prevention
- Use secure DNS providers
- Enable DNSSEC
- Block malicious domains
- Monitor DNS traffic
- Configure DNS filtering

## Detection
Analyze DNS logs for unusual queries, high-frequency lookups, and requests to newly registered domains.

## Example
Malware communicates with its command-and-control server using DNS tunneling.