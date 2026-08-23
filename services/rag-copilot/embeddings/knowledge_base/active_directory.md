# Active Directory

## Description
Active Directory (AD) is Microsoft's directory service used to manage users, computers, groups, and security policies within an organization's network. It provides centralized authentication and authorization for Windows-based environments.

## Common Indicators
- Multiple failed login attempts
- Unusual privilege escalation
- Suspicious account creation
- Unauthorized Group Policy changes
- Kerberos authentication failures

## Severity
High

## MITRE ATT&CK
- T1078 - Valid Accounts
- T1484 - Domain Policy Modification

## Prevention
- Enable Multi-Factor Authentication (MFA)
- Apply least privilege access
- Monitor privileged accounts
- Regularly patch domain controllers
- Disable unused accounts

## Detection
Monitor Windows Event Logs, Kerberos authentication logs, Active Directory changes, and privileged account activities.

## Example
An attacker steals domain administrator credentials and gains complete control over the organization's Active Directory environment.