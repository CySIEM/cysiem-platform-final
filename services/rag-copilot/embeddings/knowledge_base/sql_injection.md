# SQL Injection

## Description
SQL Injection is a web application attack that allows attackers to execute malicious SQL queries on a database.

## Indicators
- ' OR 1=1 --
- UNION SELECT
- DROP TABLE
- Database error messages

## Severity
Critical

## MITRE ATT&CK
T1190

## Prevention
- Use Prepared Statements
- Parameterized Queries
- Input Validation
- Least Privilege Database Accounts

## Example
A login form accepts:
admin' OR '1'='1
which bypasses authentication.