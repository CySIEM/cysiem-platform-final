# Creates a fully isolated PostgreSQL instance dedicated to CySIEM local
# development/testing - a separate data directory and a separate port
# (5433), so it never touches or conflicts with any Postgres already
# installed on the machine (including a system-wide install on the
# default port 5432). Safe to run on a machine that already has Postgres.
#
# Usage: pwsh scripts/setup_isolated_postgres.ps1 [-PgBinDir "C:\Program Files\PostgreSQL\18\bin"] [-DataDir "E:\CysiemPgData"] [-Port 5433]
#
# Credentials created (test-only, already reflected in
# services/assets/.env.example): user "cysiem", password "cysiem_test_pw",
# database "cysiem_layer3".

param(
    [string]$PgBinDir = "C:\Program Files\PostgreSQL\18\bin",
    [string]$DataDir = "E:\CysiemPgData",
    [int]$Port = 5433,
    [string]$DbUser = "cysiem",
    [string]$DbPassword = "cysiem_test_pw",
    [string]$DbName = "cysiem_layer3"
)

$ErrorActionPreference = "Stop"
$initdb = Join-Path $PgBinDir "initdb.exe"
$pgctl = Join-Path $PgBinDir "pg_ctl.exe"
$createdb = Join-Path $PgBinDir "createdb.exe"
$pgisready = Join-Path $PgBinDir "pg_isready.exe"

if (Test-Path $DataDir) {
    Write-Host "Data directory already exists at $DataDir - checking if the server is running..."
    & $pgisready -h localhost -p $Port
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Already running on port $Port. Nothing to do."
        exit 0
    }
    Write-Host "Starting existing cluster..."
    & $pgctl -D $DataDir -o "-p $Port" -l (Join-Path $DataDir "server.log") start
    exit 0
}

$pwFile = New-TemporaryFile
Set-Content -Path $pwFile -Value $DbPassword -NoNewline
& $initdb -D $DataDir -U $DbUser --pwfile="$pwFile" --auth=md5 -E UTF8
Remove-Item $pwFile

& $pgctl -D $DataDir -o "-p $Port" -l (Join-Path $DataDir "server.log") start
Start-Sleep -Seconds 2

$env:PGPASSWORD = $DbPassword
& $createdb -h localhost -p $Port -U $DbUser $DbName

Write-Host ""
Write-Host "Isolated CySIEM Postgres instance ready on port $Port."
Write-Host "DATABASE_URL=postgresql+asyncpg://${DbUser}:${DbPassword}@localhost:${Port}/${DbName}"
Write-Host "Stop it with: & '$pgctl' -D '$DataDir' stop"
