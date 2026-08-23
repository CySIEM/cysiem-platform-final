# Brute Force Attack

## Description
A brute force attack is an attempt to gain unauthorized access by repeatedly trying different username and password combinations until the correct credentials are found.

## Common Indicators
- Multiple failed login attempts
- Login attempts from different IP addresses
- Account lockouts
- High authentication traffic
- Repeated password failures

## Severity
High

## MITRE ATT&CK
- T1110 - Brute Force

## Prevention
- Enable Multi-Factor Authentication
- Configure account lockout policies
- Use strong passwords
- Rate-limit login attempts
- Monitor authentication logs

## Detection
Analyze authentication logs for repeated failed logins and abnormal login behavior.

## Example
An attacker uses an automated script to test thousands of passwords against an organization's VPN portal.