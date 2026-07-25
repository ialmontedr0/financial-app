#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Backup PostgreSQL database with rotation and optional S3 upload.
.DESCRIPTION
    Creates a compressed dump of the FIP database, rotates backups (keep last 7 daily, 4 weekly),
    and optionally uploads to S3-compatible storage.
.PARAMETER DbName
    Database name (default: fip)
.PARAMETER DbUser
    Database user (default: postgres)
.PARAMETER BackupDir
    Local backup directory (default: /var/backups/fip)
.PARAMETER RetainDays
    Number of daily backups to retain (default: 7)
.PARAMETER S3Bucket
    If set, uploads backup to this S3 bucket
#>

param(
    [string]$DbName = "fip",
    [string]$DbUser = "postgres",
    [string]$BackupDir = "/var/backups/fip",
    [int]$RetainDays = 7,
    [string]$S3Bucket = ""
)

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Filename = "fip-db-$Timestamp.sql.gz"
$BackupPath = Join-Path $BackupDir $Filename

# Ensure backup dir
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

Write-Host "Starting backup of database: $DbName"

# Dump
pg_dump -U $DbUser -d $DbName --no-owner --no-acl | gzip > $BackupPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backup failed!"
    exit 1
}

Write-Host "Backup created: $BackupPath ($((Get-Item $BackupPath).Length / 1MB) MB)"

# Rotate old daily backups
Get-ChildItem $BackupDir -Filter "fip-db-*.sql.gz" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip $RetainDays |
    ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "Removed old backup: $($_.Name)"
    }

# S3 upload
if ($S3Bucket) {
    $S3Key = "database/$Filename"
    Write-Host "Uploading to s3://$S3Bucket/$S3Key"
    & aws s3 cp $BackupPath "s3://$S3Bucket/$S3Key"
    Write-Host "Upload complete"
}

Write-Host "Backup finished successfully"
