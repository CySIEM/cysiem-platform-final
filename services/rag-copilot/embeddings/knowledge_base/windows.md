# Windows Security

## Description
Windows is the most widely used desktop and enterprise operating system. Proper security configuration is essential to prevent malware infections and unauthorized access.

## Common Indicators
- Failed login attempts
- Suspicious PowerShell execution
- New administrator accounts
- Unauthorized service installation
- Registry modifications

## Severity
High

## MITRE ATT&CK
- T1059.001 - PowerShell
- T1078 - Valid Accounts
- T1543 - Create or Modify System Process

## Prevention
- Keep Windows updated
- Enable Microsoft Defender
- Configure Windows Firewall
- Restrict administrator privileges
- Enable BitLocker encryption

## Detection
Analyze Windows Event Logs, Sysmon logs, Defender alerts, and endpoint security events.

## Example
A phishing email installs malware that creates a hidden administrator account on a Windows workstation.