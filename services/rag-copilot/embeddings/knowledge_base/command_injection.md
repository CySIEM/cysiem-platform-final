# Command Injection

## Description
Command Injection is a vulnerability where an attacker executes arbitrary operating system commands through an application due to improper input validation.

## Common Indicators
- Unexpected shell commands
- Suspicious system processes
- Unauthorized file creation
- High CPU utilization
- Unknown scripts executing

## Severity
Critical

## MITRE ATT&CK
- T1059 - Command and Scripting Interpreter

## Prevention
- Validate all user input
- Avoid shell command execution
- Use parameterized APIs
- Restrict system permissions
- Apply least privilege

## Detection
Monitor process execution logs, command history, and endpoint security alerts.

## Example
A vulnerable web application allows an attacker to execute `whoami` and later download malware onto the server.