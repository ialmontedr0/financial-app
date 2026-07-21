# Phase 19: Administracion - Endpoint Tests
$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "admin@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 19: ADMINISTRACION =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`nREGISTER + LOGIN" -ForegroundColor Yellow
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "LOGIN OK ($EMAIL)" -ForegroundColor Green

# NOTE: This user is "user" role, not admin. Admin endpoints will return 403.
# For full e2e testing, you need to manually promote the user to admin in the DB first.
# Or create a separate admin user via seed.

Write-Host "`n--- Testing admin access (expect 403 for regular user) ---" -ForegroundColor Yellow

# 1. List Roles (expect 403)
Write-Host "`n1. GET /admin/roles" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/roles" -Headers $HEADERS
    Write-Host "  OK: roles=$($r.Content)" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code (expected 403 for non-admin)" -ForegroundColor DarkYellow
}

# 2. List Permissions
Write-Host "`n2. GET /admin/permissions" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/permissions" -Headers $HEADERS
    Write-Host "  OK" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code" -ForegroundColor DarkYellow
}

# 3. List Users
Write-Host "`n3. GET /admin/users" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/users" -Headers $HEADERS
    Write-Host "  OK" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code" -ForegroundColor DarkYellow
}

# 4. System Stats
Write-Host "`n4. GET /admin/stats" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/stats" -Headers $HEADERS
    Write-Host "  OK" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code" -ForegroundColor DarkYellow
}

# 5. Audit Logs
Write-Host "`n5. GET /admin/audit" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/audit" -Headers $HEADERS
    Write-Host "  OK" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code" -ForegroundColor DarkYellow
}

# 6. Audit Stats
Write-Host "`n6. GET /admin/audit/stats" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "$BASE/admin/audit/stats" -Headers $HEADERS
    Write-Host "  OK" -ForegroundColor Green
} catch {
    $code = $_.Exception.Response.StatusCode.value__
    Write-Host "  Status $code" -ForegroundColor DarkYellow
}

Write-Host "`n===== PHASE 19 COMPLETE =====" -ForegroundColor Cyan
Write-Host "NOTE: Admin endpoints require admin role. Promote user in DB to test fully." -ForegroundColor Yellow
