# Security Information and Event Management (SIEM)

## Description
SIEM is a cybersecurity platform that collects, correlates, and analyzes security logs from multiple sources to detect threats and support incident response.

## Common Indicators
- Multiple failed login attempts
- Privilege escalation
- Malware alerts
- Suspicious network connections
- Correlated security events

## Severity
High

## MITRE ATT&CK
Varies depending on detected attack.

## Prevention
- Collect logs from all critical systems
- Create correlation rules
- Monitor alerts continuously
- Integrate threat intelligence
- Regularly tune detection rules

## Detection
SIEM automatically correlates logs from endpoints, firewalls, IDS/IPS, Active Directory, and cloud services.

## Example
The SIEM correlates failed VPN logins, suspicious PowerShell activity, and endpoint alerts to identify a credential compromise.