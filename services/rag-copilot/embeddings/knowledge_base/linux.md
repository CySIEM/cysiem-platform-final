# Linux Security

## Description
Linux is one of the most widely used operating systems for servers, cloud infrastructure, and enterprise environments. Proper security hardening is essential to prevent unauthorized access.

## Common Indicators
- Unauthorized SSH logins
- Suspicious cron jobs
- Unknown user accounts
- Privilege escalation attempts
- Unexpected processes

## Severity
High

## MITRE ATT&CK
- T1059 - Command and Scripting Interpreter
- T1078 - Valid Accounts

## Prevention
- Disable root SSH login
- Enable SSH key authentication
- Keep packages updated
- Configure firewall rules
- Use SELinux or AppArmor

## Detection
Monitor authentication logs, sudo activity, process execution, and file integrity.

## Example
An attacker exploits a vulnerable web server and installs a reverse shell on a Linux machine.