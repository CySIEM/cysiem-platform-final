# Web Shell

## Description
A Web Shell is a malicious script uploaded to a web server that allows attackers to remotely execute commands through a web browser.

## Common Indicators
- Unknown PHP, ASPX, or JSP files
- Suspicious POST requests
- Unexpected file uploads
- Remote command execution
- High outbound traffic

## Severity
Critical

## MITRE ATT&CK
- T1505.003 - Web Shell

## Prevention
- Validate file uploads
- Restrict executable permissions
- Keep web applications updated
- Deploy Web Application Firewall (WAF)
- Perform file integrity monitoring

## Detection
Monitor web server logs, file changes, suspicious HTTP POST requests, and EDR alerts.

## Example
An attacker uploads a malicious PHP shell after exploiting a vulnerable file upload feature.