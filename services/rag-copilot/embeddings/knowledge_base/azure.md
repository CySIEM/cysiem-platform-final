# Microsoft Azure Security

## Description
Microsoft Azure is a cloud platform offering virtual machines, storage, networking, identity management, and cloud security services.

## Common Indicators
- Suspicious Azure AD logins
- Public storage accounts
- Unauthorized role assignments
- Excessive permissions
- Unknown application registrations

## Severity
High

## MITRE ATT&CK
- T1078 - Valid Accounts
- T1098 - Account Manipulation

## Prevention
- Enable Azure MFA
- Apply Conditional Access Policies
- Enable Microsoft Defender for Cloud
- Monitor Azure Activity Logs
- Limit privileged roles

## Detection
Review Azure Activity Logs, Azure AD Sign-In Logs, Defender alerts, and identity risk reports.

## Example
An attacker compromises an Azure Global Administrator account and deploys malicious virtual machines.