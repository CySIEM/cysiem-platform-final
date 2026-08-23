# PowerShell Security

## Description
PowerShell is Microsoft's scripting language used for automation and system administration. Attackers often abuse it to execute malicious commands.

## Common Indicators
- Encoded PowerShell commands
- DownloadString usage
- Invoke-Expression execution
- Suspicious PowerShell processes
- Base64 encoded scripts

## Severity
Critical

## MITRE ATT&CK
- T1059.001 - PowerShell

## Prevention
- Disable PowerShell v2
- Enable PowerShell logging
- Restrict execution policies
- Use Microsoft Defender
- Monitor script execution

## Detection
Analyze PowerShell Operational Logs (Event ID 4104), Sysmon logs, and EDR alerts.

## Example
A phishing email executes an encoded PowerShell command that downloads ransomware from a remote server.