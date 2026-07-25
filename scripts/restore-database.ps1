#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Restore PostgreSQL database from a compressed backup file.
.PARAMETER BackupFile
    Path to the .sql.gz backup file to restore from
.PARAMETER DbName
    Target database name (default: fip)
.PARAMETER DbUser
    Database user (default: postgres)
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$DbName = "fip",
    [string]$DbUser = "postgres"
)

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

Write-Host "Restoring database $DbName from $BackupFile"

# Drop and recreate target db
psql -U $DbUser -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '$DbName' AND pid <> pg_backend_pid();"
psql -U $DbUser -d postgres -c "DROP DATABASE IF EXISTS $DbName;"
psql -U $DbUser -d postgres -c "CREATE DATABASE $DbName;"

# Restore
gunzip -c $BackupFile | psql -U $DbUser -d $DbName

if ($LASTEXITCODE -ne 0) {
    Write-Error "Restore failed!"
    exit 1
}

Write-Host "Database restore completed successfully"
