# Secure Shell (SSH)

## Description
SSH is a secure protocol used to remotely access Linux and Unix systems over encrypted connections.

## Common Indicators
- Repeated failed login attempts
- Root login attempts
- Unknown SSH keys
- Brute-force attacks
- Logins from unusual IP addresses

## Severity
Medium

## MITRE ATT&CK
- T1110 - Brute Force
- T1021.004 - SSH

## Prevention
- Disable password authentication
- Use SSH key authentication
- Disable root login
- Change default SSH port (optional)
- Enable fail2ban

## Detection
Review authentication logs, SSH daemon logs, and SIEM alerts for abnormal login activity.

## Example
An attacker performs a brute-force attack against an organization's public SSH server until valid credentials are discovered.