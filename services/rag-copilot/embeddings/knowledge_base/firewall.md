# Firewall

## Description
A firewall is a security device or software that filters incoming and outgoing network traffic based on predefined security rules.

## Common Indicators
- Blocked unauthorized connections
- Port scanning attempts
- Excessive denied packets
- Firewall alerts
- Suspicious outbound traffic

## Severity
Medium

## MITRE ATT&CK
- T1046 - Network Service Discovery

## Prevention
- Configure firewall rules properly
- Block unused ports
- Regularly review firewall logs
- Restrict inbound access
- Update firewall firmware

## Detection
Review firewall logs for blocked IPs, repeated connection attempts, and unusual outbound communications.

## Example
A firewall blocks repeated SSH login attempts from an unknown external IP address.