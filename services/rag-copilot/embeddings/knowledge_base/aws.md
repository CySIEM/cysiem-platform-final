# Amazon Web Services (AWS) Security

## Description
AWS is a cloud computing platform that provides services such as EC2, S3, IAM, Lambda, and RDS. Proper security configuration is essential to protect cloud resources.

## Common Indicators
- Publicly exposed S3 buckets
- Unauthorized IAM users
- Excessive permissions
- Suspicious EC2 activity
- Unusual API calls

## Severity
High

## MITRE ATT&CK
- T1530 - Data from Cloud Storage
- T1078 - Valid Accounts

## Prevention
- Enable IAM least privilege
- Use MFA
- Enable CloudTrail logging
- Encrypt S3 buckets
- Rotate access keys

## Detection
Monitor AWS CloudTrail logs, GuardDuty findings, IAM changes, and unusual network traffic.

## Example
A public S3 bucket accidentally exposes confidential customer data.