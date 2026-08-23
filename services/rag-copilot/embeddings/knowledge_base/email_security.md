# Email Security

## Description
Email security protects email systems against phishing, malware, spam, spoofing, and unauthorized access.

## Common Indicators
- Suspicious attachments
- Fake sender addresses
- Unexpected password reset emails
- Embedded malicious links
- Email spoofing

## Severity
High

## MITRE ATT&CK
- T1566 - Phishing

## Prevention
- Enable SPF
- Configure DKIM
- Implement DMARC
- Train employees against phishing
- Scan email attachments

## Detection
Monitor email gateway logs, phishing reports, attachment scanning results, and sender authentication failures.

## Example
An attacker sends a spoofed Microsoft 365 login page to steal employee credentials.