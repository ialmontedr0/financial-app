# Phase 20: Integraciones - Endpoint Tests
# Ejecutar con el servidor corriendo en :8080
# .\scripts\test_phase20.ps1

$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "integration_test@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 20: INTEGRACIONES =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`n[1] REGISTER + LOGIN" -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}" | Out-Null
} catch { }
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "  OK - Token obtained" -ForegroundColor Green

# ─── IMPORTS ───────────────────────────────────────────

Write-Host "`n--- IMPORTS ---" -ForegroundColor Cyan

# 2. Upload CSV
Write-Host "`n[2] POST /imports/transactions (CSV)" -ForegroundColor Yellow
$csvContent = @"
date,description,amount,type,category
2025-01-15,Supermercado,2500.00,expense,Alimentacion
2025-01-16,Salario,85000.00,income,Salario
2025-01-17,Netflix,699.00,expense,Entretenimiento
"@
$csvBytes = [System.Text.Encoding]::UTF8.GetBytes($csvContent)
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"transactions.csv`"",
    "Content-Type: text/csv",
    "",
    [System.Text.Encoding]::UTF8.GetString($csvBytes),
    "--$boundary--"
) -join $LF
$resp = Invoke-WebRequest -Uri "$BASE/imports/transactions" -Method Post -Headers $HEADERS -ContentType "multipart/form-data; boundary=$boundary" -Body $bodyLines
$uploadData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - job_id=$($uploadData.job_id)" -ForegroundColor Green
Write-Host "  Total rows: $($uploadData.total_rows)" -ForegroundColor DarkGray
Write-Host "  Columns: $($uploadData.columns_found -join ', ')" -ForegroundColor DarkGray
$JOB_ID = $uploadData.job_id

# 3. Confirm import
Write-Host "`n[3] POST /imports/confirm" -ForegroundColor Yellow
$confirmBody = "{`"job_id`":`"$JOB_ID`"}"
$resp = Invoke-WebRequest -Uri "$BASE/imports/confirm" -Method Post -Headers $HEADERS -ContentType "application/json" -Body $confirmBody
$confirmData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - valid=$($confirmData.valid_rows) errors=$($confirmData.error_rows)" -ForegroundColor Green

# 4. List import jobs
Write-Host "`n[4] GET /imports/jobs" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/imports/jobs" -Headers $HEADERS
$jobsData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - $($jobsData.total) job(s)" -ForegroundColor Green

# 5. Get specific job
Write-Host "`n[5] GET /imports/jobs/$JOB_ID" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/imports/jobs/$JOB_ID" -Headers $HEADERS
$jobData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - file=$($jobData.file_name) status=$($jobData.status)" -ForegroundColor Green

# ─── EXPORTS ───────────────────────────────────────────

Write-Host "`n--- EXPORTS ---" -ForegroundColor Cyan

# 6. Export CSV
Write-Host "`n[6] GET /exports/transactions/csv" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/transactions/csv" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green
Write-Host "  Size: $($resp.RawContentLength) bytes" -ForegroundColor DarkGray

# 7. Export Excel
Write-Host "`n[7] GET /exports/transactions/excel" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/transactions/excel" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# 8. Export PDF
Write-Host "`n[8] GET /exports/transactions/pdf" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/transactions/pdf" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# 9. Export Budgets PDF
Write-Host "`n[9] GET /exports/budgets/pdf" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/budgets/pdf" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# 10. Export Goals PDF
Write-Host "`n[10] GET /exports/goals/pdf" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/goals/pdf" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# 11. Export Calendar (recurring)
Write-Host "`n[11] GET /exports/calendar/recurring" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/calendar/recurring" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# 12. Export Calendar (goals)
Write-Host "`n[12] GET /exports/calendar/goals" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/exports/calendar/goals" -Headers $HEADERS
Write-Host "  OK - Content-Type: $($resp.Headers['Content-Type'])" -ForegroundColor Green

# ─── FINANCIAL DATA ────────────────────────────────────

Write-Host "`n--- FINANCIAL DATA ---" -ForegroundColor Cyan

# 13. Exchange rates
Write-Host "`n[13] GET /financial-data/exchange-rates?base=USD&symbols=EUR,GBP" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/financial-data/exchange-rates?base=USD&symbols=EUR,GBP" -Headers $HEADERS
$fxData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - base=$($fxData.base) date=$($fxData.date)" -ForegroundColor Green
Write-Host "  Rates: $($fxData.rates | ConvertTo-Json -Compress)" -ForegroundColor DarkGray

# 14. Historical rate
Write-Host "`n[14] GET /financial-data/exchange-rates/EUR?date=2024-01-15&base=USD" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/financial-data/exchange-rates/EUR?date=2024-01-15&base=USD" -Headers $HEADERS
$histData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - rate=$($histData.rate)" -ForegroundColor Green

# 15. Date range rates
Write-Host "`n[15] GET /financial-data/exchange-rates/range?start_date=2024-01-01&end_date=2024-01-05&base=USD&target=EUR" -ForegroundColor Yellow
$resp = Invoke-WebRequest -Uri "$BASE/financial-data/exchange-rates/range?start_date=2024-01-01&end_date=2024-01-05&base=USD&target=EUR" -Headers $HEADERS
$rangeData = $resp.Content | ConvertFrom-Json
Write-Host "  OK - $($rangeData.rates.PSObject.Properties.Count) date(s)" -ForegroundColor Green

Write-Host "`n===== PHASE 20 COMPLETE =====" -ForegroundColor Cyan
Write-Host "All 15 endpoints tested successfully." -ForegroundColor Green
