#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Upload a local backup file to S3-compatible storage.
.PARAMETER LocalPath
    Path to the backup file to upload
.PARAMETER S3Bucket
    S3 bucket name
.PARAMETER S3Key
    S3 object key (optional — defaults to filename with date prefix)
.PARAMETER EndpointUrl
    S3-compatible endpoint URL (for MinIO, DigitalOcean Spaces, etc.)
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$LocalPath,
    [Parameter(Mandatory=$true)]
    [string]$S3Bucket,
    [string]$S3Key = "",
    [string]$EndpointUrl = ""
)

if (-not (Test-Path $LocalPath)) {
    Write-Error "File not found: $LocalPath"
    exit 1
}

if (-not $S3Key) {
    $Filename = Split-Path $LocalPath -Leaf
    $DatePrefix = Get-Date -Format "yyyy/MM/dd"
    $S3Key = "backups/$DatePrefix/$Filename"
}

$S3Uri = "s3://$S3Bucket/$S3Key"
Write-Host "Uploading $LocalPath to $S3Uri"

$awsArgs = @("s3", "cp", $LocalPath, $S3Uri)
if ($EndpointUrl) {
    $awsArgs += @("--endpoint-url", $EndpointUrl)
}

& aws $awsArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload completed successfully"
}
else {
    Write-Error "Upload failed"
    exit 1
}
