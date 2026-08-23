# Cross-Site Scripting (XSS)

## Description
Cross-Site Scripting allows attackers to inject malicious JavaScript into webpages viewed by other users.

## Types
- Stored XSS
- Reflected XSS
- DOM-based XSS

## Indicators
- Unexpected JavaScript execution
- Stolen cookies
- Redirects

## Severity
High

## Prevention
- Escape HTML
- Validate user input
- Use Content Security Policy (CSP)