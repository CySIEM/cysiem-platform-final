# TCP/IP

## Description
TCP/IP (Transmission Control Protocol/Internet Protocol) is the standard networking protocol suite that enables communication between devices over the internet and private networks.

## Common Indicators
- Packet loss
- High network latency
- TCP SYN flood attacks
- Unexpected open ports
- Abnormal network traffic

## Severity
Medium

## MITRE ATT&CK
- T1046 - Network Service Discovery
- T1498 - Network Denial of Service

## Prevention
- Configure firewalls properly
- Close unused ports
- Enable network segmentation
- Monitor network traffic
- Keep network devices updated

## Detection
Analyze network traffic using Wireshark, IDS/IPS, firewall logs, and SIEM alerts.

## Example
An attacker performs a TCP SYN flood attack to exhaust server resources and deny service to legitimate users.