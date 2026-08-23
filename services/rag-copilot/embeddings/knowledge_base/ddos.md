# Distributed Denial of Service (DDoS)

## Description
A Distributed Denial of Service (DDoS) attack is a cyberattack where multiple compromised systems flood a target server, website, or network with massive traffic, making it unavailable to legitimate users.

## Common Indicators
- Extremely high network traffic
- Slow website performance
- Frequent service outages
- Large number of requests from multiple IPs
- Increased bandwidth consumption

## Severity
Critical

## MITRE ATT&CK
- T1498 - Network Denial of Service

## Prevention
- Use DDoS protection services
- Configure Web Application Firewalls (WAF)
- Implement rate limiting
- Enable CDN protection
- Monitor traffic continuously

## Detection
Monitor abnormal spikes in traffic, bandwidth usage, firewall logs, and IDS/IPS alerts.

## Example
Attackers use a botnet of thousands of infected devices to overwhelm an e-commerce website during a sale.