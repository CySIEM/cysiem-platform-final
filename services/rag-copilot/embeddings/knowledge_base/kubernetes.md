# Kubernetes Security

## Description
Kubernetes is a container orchestration platform used to automate deployment, scaling, and management of containerized applications.

## Common Indicators
- Anonymous API access
- Privileged containers
- Exposed Kubernetes Dashboard
- Suspicious pod creation
- Unauthorized RBAC changes

## Severity
High

## MITRE ATT&CK
- T1610 - Deploy Container
- T1611 - Escape to Host

## Prevention
- Enable Role-Based Access Control (RBAC)
- Disable anonymous authentication
- Secure the Kubernetes API Server
- Scan container images
- Enable audit logging

## Detection
Monitor Kubernetes audit logs, API activity, pod creation events, and container runtime alerts.

## Example
An attacker gains access to an exposed Kubernetes Dashboard and deploys a malicious cryptocurrency mining container.