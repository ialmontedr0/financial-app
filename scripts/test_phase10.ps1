# Phase 10 - Presupuesto Inteligente Test Script
$base = "http://localhost:8080/api/v1"

Write-Host "===== PHASE 10: PRESUPUESTO INTELIGENTE =====" -ForegroundColor Cyan

# Login
$r = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"income_tester_v8@fip.com","password":"TestPass123!"}' -TimeoutSec 15
$token = $r.tokens.access_token
$h = @{ Authorization = "Bearer $token" }
Write-Host "LOGIN OK"

# ===== BUDGETS =====
Write-Host "`n===== BUDGETS =====" -ForegroundColor Green

# 1. POST /budgets - Total budget
Write-Host "`n1. POST /budgets (total)"
$bgt = Invoke-RestMethod -Uri "$base/budgets" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Presupuesto Total Mensual"; amount="80000"; budget_type="total"; period="monthly"
    alert_threshold=80; description="Mi presupuesto general"; auto_adjust=$true
} | ConvertTo-Json)
$bgtId = $bgt.id
Write-Host "  OK: $bgtId | $($bgt.name)"

# 2. GET /budgets
Write-Host "`n2. GET /budgets"
$bgts = Invoke-RestMethod -Uri "$base/budgets" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($bgts.total) budgets"

# 3. GET /budgets/summary
Write-Host "`n3. GET /budgets/summary"
$sum = Invoke-RestMethod -Uri "$base/budgets/summary" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: total=$($sum.total_budget_amount) spent=$($sum.total_spent) alerts=$($sum.unread_alerts)"

# 4. GET /budgets/{id}
Write-Host "`n4. GET /budgets/$bgtId"
$detail = Invoke-RestMethod -Uri "$base/budgets/$bgtId" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($detail.name) | pct=$($detail.pct_used)% | status=$($detail.status)"

# 5. PATCH /budgets/{id}
Write-Host "`n5. PATCH /budgets/$bgtId"
$upd = Invoke-RestMethod -Uri "$base/budgets/$bgtId" -Method PATCH -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    amount="90000"; alert_threshold=75
} | ConvertTo-Json)
Write-Host "  OK: $($upd.name) | threshold=$($upd.alert_threshold)%"

# 6. POST /budgets/{id}/refresh
Write-Host "`n6. POST /budgets/$bgtId/refresh"
$ref = Invoke-RestMethod -Uri "$base/budgets/$bgtId/refresh" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body '{}'
Write-Host "  OK: spent=$($ref.spent) remaining=$($ref.remaining) status=$($ref.status)"

# 7. POST /budgets (category budget with real category)
Write-Host "`n7. POST /budgets (category)"
$cats = Invoke-RestMethod -Uri "$base/categories" -Method GET -Headers $h -TimeoutSec 10
$catId = $cats.categories[0].id
$bgt2 = Invoke-RestMethod -Uri "$base/budgets" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Alimentacion"; amount="25000"; budget_type="category"; period="monthly"; category_id=$catId
} | ConvertTo-Json)
$bgt2Id = $bgt2.id
Write-Host "  OK: $bgt2Id | $($bgt2.name)"

# 8. POST /budgets/{id}/auto-adjust
Write-Host "`n8. POST /budgets/$bgtId/auto-adjust"
$adj = Invoke-RestMethod -Uri "$base/budgets/$bgtId/auto-adjust" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    buffer_pct=15; apply=$false
} | ConvertTo-Json)
Write-Host "  OK: current=$($adj.current_amount) avg=$($adj.average_spending) suggested=$($adj.suggested_amount)"

# ===== ALERTS =====
Write-Host "`n===== ALERTS =====" -ForegroundColor Green

# 9. GET /budgets/alerts/all
Write-Host "`n9. GET /budgets/alerts/all"
$alerts = Invoke-RestMethod -Uri "$base/budgets/alerts/all" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($alerts.total) alerts"

# 10. POST /budgets/alerts/read (mark all)
Write-Host "`n10. POST /budgets/alerts/read (mark_all)"
$mread = Invoke-RestMethod -Uri "$base/budgets/alerts/read" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{mark_all=$true} | ConvertTo-Json)
Write-Host "  OK: $($mread.message)"

# 11. DELETE /budgets/{id}
Write-Host "`n11. DELETE /budgets/$bgt2Id"
$del = Invoke-RestMethod -Uri "$base/budgets/$bgt2Id" -Method DELETE -Headers $h -TimeoutSec 10
Write-Host "  OK: $($del.message)"

Write-Host "`n===== PHASE 10 COMPLETE =====" -ForegroundColor Cyan
