# Docker Security

## Description
Docker is a containerization platform that packages applications and their dependencies into lightweight containers for consistent deployment.

## Common Indicators
- Privileged containers
- Containers running as root
- Untrusted Docker images
- Exposed Docker daemon
- Unauthorized container creation

## Severity
High

## MITRE ATT&CK
- T1611 - Escape to Host
- T1610 - Deploy Container

## Prevention
- Use official images
- Scan images for vulnerabilities
- Run containers as non-root users
- Limit container privileges
- Keep Docker updated

## Detection
Monitor Docker daemon logs, container activity, image integrity, and runtime security events.

## Example
An attacker exploits a vulnerable container and escapes to the host operating system.