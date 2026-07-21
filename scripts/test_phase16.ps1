# Phase 16: Motor de Recomendaciones - Endpoint Tests
$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "phase16_$(Get-Random)@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 16: MOTOR DE RECOMENDACIONES =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`nREGISTER + LOGIN" -ForegroundColor Yellow
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "LOGIN OK" -ForegroundColor Green

# 1. Habits Analysis
Write-Host "`n1. GET /ai/habits/analysis" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/habits/analysis" -Headers $HEADERS
Write-Host "  OK: score=$($r.overall_habit_score) recs=$($r.total_recommendations)" -ForegroundColor Green

# 2. Habits Trends
Write-Host "`n2. GET /ai/habits/trends" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/habits/trends" -Headers $HEADERS
Write-Host "  OK: months=$($r.months_analyzed)" -ForegroundColor Green

# 3. Risk Assessment
Write-Host "`n3. GET /ai/risks/assessment" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/risks/assessment" -Headers $HEADERS
Write-Host "  OK: health=$($r.financial_health_score) risks=$($r.risk_factors.Count)" -ForegroundColor Green

# 4. Health Score
Write-Host "`n4. GET /ai/risks/health-score" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/risks/health-score" -Headers $HEADERS
Write-Host "  OK: score=$($r.financial_health_score) top_risk=$($r.top_risk)" -ForegroundColor Green

# 5. Savings Optimize
Write-Host "`n5. POST /ai/savings/optimize" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/savings/optimize" -Method Post -Headers $HEADERS
Write-Host "  OK: total_savings=$($r.estimated_total_savings) recs=$($r.recommendations.Count)" -ForegroundColor Green

# 6. Savings Simulate
Write-Host "`n6. POST /ai/savings/simulate" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/savings/simulate?monthly_amount=5000&months=12&annual_return_pct=8" -Method Post -Headers $HEADERS
Write-Host "  OK: final=$($r.final_balance) interest=$($r.total_interest)" -ForegroundColor Green

# 7. Explain Recommendation
Write-Host "`n7. POST /ai/explain" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/explain?rec_type=reduce_spending&title=Test&priority=high&estimated_savings=5000&confidence=0.8" -Method Post -Headers $HEADERS
Write-Host "  OK: tone=$($r.tone) headline=$($r.headline)" -ForegroundColor Green

# 8. Dashboard
Write-Host "`n8. GET /ai/dashboard" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/dashboard" -Headers $HEADERS
Write-Host "  OK: habit=$($r.habits.score) risk=$($r.risks.health_score) recs=$($r.recommendations.total)" -ForegroundColor Green

Write-Host "`n===== PHASE 16 COMPLETE =====" -ForegroundColor Cyan