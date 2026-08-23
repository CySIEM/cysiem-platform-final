# Virtual Private Network (VPN)

## Description
A VPN creates an encrypted connection between a user's device and a remote network, protecting data from interception.

## Common Indicators
- Multiple failed VPN logins
- Login from unusual locations
- Simultaneous logins from different countries
- Unexpected VPN sessions
- Excessive authentication failures

## Severity
High

## MITRE ATT&CK
- T1078 - Valid Accounts

## Prevention
- Enable Multi-Factor Authentication
- Monitor VPN logs
- Restrict VPN access
- Rotate VPN credentials
- Disable inactive accounts

## Detection
Monitor VPN authentication logs, login locations, failed logins, and abnormal session durations.

## Example
A compromised employee account is used to access the corporate VPN from another country.