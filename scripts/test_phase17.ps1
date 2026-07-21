# Phase 17: Automatizaciones - Endpoint Tests
$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "phase17_$(Get-Random)@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 17: AUTOMATIZACIONES =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`nREGISTER + LOGIN" -ForegroundColor Yellow
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "LOGIN OK" -ForegroundColor Green

# 1. List Rules (empty)
Write-Host "`n1. GET /automations" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations" -Headers $HEADERS
Write-Host "  OK: total=$($r.total)" -ForegroundColor Green

# 2. Get Templates
Write-Host "`n2. GET /automations/templates" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/templates" -Headers $HEADERS
Write-Host "  OK: triggers=$($r.triggers.Count) actions=$($r.actions.Count)" -ForegroundColor Green

# 3. Create Rule
Write-Host "`n3. POST /automations" -ForegroundColor Yellow
$body = @{
    name = "Ahorro automatico mensual"
    trigger_type = "date_scheduled"
    action_type = "create_transaction"
    trigger_conditions = @{ day_of_month = 1; months = @(1,2,3,4,5,6,7,8,9,10,11,12) }
    action_params = @{
        account_id = "00000000-0000-0000-0000-000000000001"
        amount = 5000
        description = "Ahorro mensual automatico"
        transaction_type = "expense"
    }
} | ConvertTo-Json -Depth 5
$r = Invoke-RestMethod -Uri "$BASE/automations" -Method Post -ContentType "application/json" -Body $body -Headers $HEADERS
$RULE_ID = $r.id
Write-Host "  OK: id=$($RULE_ID) name=$($r.name)" -ForegroundColor Green

# 4. Get Rule
Write-Host "`n4. GET /automations/$RULE_ID" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/$RULE_ID" -Headers $HEADERS
Write-Host "  OK: name=$($r.name) trigger=$($r.trigger_type)" -ForegroundColor Green

# 5. Toggle Rule
Write-Host "`n5. POST /automations/$RULE_ID/toggle" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/$RULE_ID/toggle" -Method Post -Headers $HEADERS
Write-Host "  OK: is_active=$($r.is_active)" -ForegroundColor Green

# 6. Evaluate All (dry run)
Write-Host "`n6. POST /automations/evaluate?dry_run=true" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/evaluate?dry_run=true" -Method Post -Headers $HEADERS
Write-Host "  OK: total=$($r.total_rules) executed=$($r.executed) skipped=$($r.skipped)" -ForegroundColor Green

# 7. Summary
Write-Host "`n7. GET /automations/summary" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/summary" -Headers $HEADERS
Write-Host "  OK: total=$($r.total_rules) active=$($r.active_rules) executions=$($r.total_executions)" -ForegroundColor Green

# 8. Execution Log
Write-Host "`n8. GET /automations/execution-log" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/execution-log" -Headers $HEADERS
Write-Host "  OK: total=$($r.total)" -ForegroundColor Green

# 9. Quick Savings Transfer
Write-Host "`n9. POST /automations/quick/savings-transfer" -ForegroundColor Yellow
$body = @{
    source_account_id = "00000000-0000-0000-0000-000000000001"
    target_account_id = "00000000-0000-0000-0000-000000000002"
    amount = 3000
    amount_type = "fixed"
} | ConvertTo-Json -Depth 5
$r = Invoke-RestMethod -Uri "$BASE/automations/quick/savings-transfer" -Method Post -ContentType "application/json" -Body $body -Headers $HEADERS
Write-Host "  OK: id=$($r.id) name=$($r.name)" -ForegroundColor Green

# 10. Delete Rule
Write-Host "`n10. DELETE /automations/$RULE_ID" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/automations/$RULE_ID" -Method Delete -Headers $HEADERS
Write-Host "  OK: $($r.message)" -ForegroundColor Green

Write-Host "`n===== PHASE 17 COMPLETE =====" -ForegroundColor Cyan
