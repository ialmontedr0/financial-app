# Phase 11 - Metas Financieras Test Script
$base = "http://localhost:8080/api/v1"

Write-Host "===== PHASE 11: METAS FINANCIERAS =====" -ForegroundColor Cyan

# Login
$r = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"income_tester_v8@fip.com","password":"TestPass123!"}' -TimeoutSec 15
$token = $r.tokens.access_token
$h = @{ Authorization = "Bearer $token" }
Write-Host "LOGIN OK"

# ===== GOALS =====
Write-Host "`n===== GOALS =====" -ForegroundColor Green

# 1. POST /goals - Create savings goal
Write-Host "`n1. POST /goals (savings)"
$goal = Invoke-RestMethod -Uri "$base/goals" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Fondo de Emergencia"; target_amount="500000"; goal_type="emergency_fund"
    monthly_contribution="25000"; interest_rate="6"; compound_frequency="monthly"
    priority=1; description="6 meses de gastos"
} | ConvertTo-Json)
$goalId = $goal.id
Write-Host "  OK: $goalId | $($goal.name) | target=$($goal.target_amount)"
Write-Host "  Prediction: prob=$($goal.prediction.predicted_probability) date=$($goal.prediction.predicted_completion_date)"

# 2. POST /goals - Create investment goal
Write-Host "`n2. POST /goals (investment)"
$goal2 = Invoke-RestMethod -Uri "$base/goals" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Fondo de Inversion"; target_amount="1000000"; goal_type="investment"
    monthly_contribution="50000"; interest_rate="10"
} | ConvertTo-Json)
$goal2Id = $goal2.id
Write-Host "  OK: $goal2Id | $($goal2.name) | target=$($goal2.target_amount)"

# 3. GET /goals
Write-Host "`n3. GET /goals"
$goals = Invoke-RestMethod -Uri "$base/goals" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($goals.total) goals"

# 4. GET /goals/summary
Write-Host "`n4. GET /goals/summary"
$sum = Invoke-RestMethod -Uri "$base/goals/summary" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: active=$($sum.active_goals) completed=$($sum.completed_goals) progress=$($sum.overall_progress_pct)%"

# 5. GET /goals/{id}
Write-Host "`n5. GET /goals/$goalId"
$detail = Invoke-RestMethod -Uri "$base/goals/$goalId" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($detail.name) | milestones=$($detail.milestones.Count)"
Write-Host "  Progress: $($detail.progress.pct_complete)% | behind=$($detail.progress.behind_schedule)"

# 6. PATCH /goals/{id}
Write-Host "`n6. PATCH /goals/$goalId"
$upd = Invoke-RestMethod -Uri "$base/goals/$goalId" -Method PATCH -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    target_amount="600000"; monthly_contribution="30000"
} | ConvertTo-Json)
Write-Host "  OK: target=$($upd.target_amount) monthly=$($upd.monthly_contribution)"

# 7. POST /goals/{id}/refresh
Write-Host "`n7. POST /goals/$goalId/refresh"
$ref = Invoke-RestMethod -Uri "$base/goals/$goalId/refresh" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body '{}'
Write-Host "  OK: pct=$($ref.progress.pct_complete)% remaining=$($ref.progress.remaining)"

# 8. POST /goals/{id}/predict
Write-Host "`n8. POST /goals/$goalId/predict"
$pred = Invoke-RestMethod -Uri "$base/goals/$goalId/predict" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body '{}'
Write-Host "  OK: prob=$($pred.prediction.predicted_probability) date=$($pred.prediction.predicted_completion_date)"

# ===== SIMULATIONS =====
Write-Host "`n===== SIMULATIONS =====" -ForegroundColor Green

# 9. POST /goals/{id}/simulations - Conservative
Write-Host "`n9. POST /goals/$goalId/simulations (conservative)"
$sim1 = Invoke-RestMethod -Uri "$base/goals/$goalId/simulations" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Conservador"; monthly_contribution="20000"; interest_rate="4"
} | ConvertTo-Json)
Write-Host "  OK: $($sim1.name) | months=$($sim1.months_to_complete) prob=$($sim1.predicted_probability)"

# 10. POST /goals/{id}/simulations - Aggressive with lump sum
Write-Host "`n10. POST /goals/$goalId/simulations (aggressive + lump sum)"
$sim2 = Invoke-RestMethod -Uri "$base/goals/$goalId/simulations" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Agresivo + Bono"; monthly_contribution="40000"; interest_rate="8"
    lump_sum="100000"; lump_sum_date="2026-12-31"
} | ConvertTo-Json)
Write-Host "  OK: $($sim2.name) | months=$($sim2.months_to_complete) total_contrib=$($sim2.total_contributions)"

# 11. GET /goals/{id}/simulations
Write-Host "`n11. GET /goals/$goalId/simulations"
$sims = Invoke-RestMethod -Uri "$base/goals/$goalId/simulations" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($sims.total) simulations"

# ===== CLEANUP =====
Write-Host "`n===== CLEANUP =====" -ForegroundColor Green

# 12. DELETE /goals/{id}
Write-Host "`n12. DELETE /goals/$goal2Id"
$del = Invoke-RestMethod -Uri "$base/goals/$goal2Id" -Method DELETE -Headers $h -TimeoutSec 10
Write-Host "  OK: $($del.message)"

Write-Host "`n===== PHASE 11 COMPLETE =====" -ForegroundColor Cyan
