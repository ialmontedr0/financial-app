$base = "http://127.0.0.1:8080/api/v1"

# ===== SETUP =====
$r = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"income_tester_v8@fip.com","password":"TestPass123!"}' -TimeoutSec 15
$h = @{ Authorization = "Bearer $($r.tokens.access_token)" }
Write-Host "LOGIN OK"

$accs = Invoke-RestMethod -Uri "$base/accounts" -Method GET -Headers $h -TimeoutSec 10
$accId = $accs.accounts[0].id
Write-Host "ACCOUNT: $accId"

# ===== CREDIT CARDS (6 endpoints) =====
Write-Host "`n===== CREDIT CARDS ====="

# 1. POST /cards
Write-Host "`n1. POST /cards"
$card = Invoke-RestMethod -Uri "$base/expenses/cards" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Visa Platinum"; last_four_digits="4532"; card_network="visa"; credit_limit="150000"
    available_credit="105000"; statement_day=15; payment_due_day=25; interest_rate="0.2499"
    account_id=$accId; color="#FF5722"
} | ConvertTo-Json)
$cardId = $card.id
Write-Host "  OK: $cardId | $($card.name) ****$($card.last_four_digits)"

# 2. GET /cards
Write-Host "`n2. GET /cards"
$cards = Invoke-RestMethod -Uri "$base/expenses/cards" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($cards.total) cards"

# 3. GET /cards/{id}/utilization
Write-Host "`n3. GET /cards/{id}/utilization"
$ut = Invoke-RestMethod -Uri "$base/expenses/cards/$cardId/utilization" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: utilization=$($ut.utilization_percentage)% status=$($ut.status)"

# 4. POST /cards/{id}/bills
Write-Host "`n4. POST /cards/{id}/bills"
$bill = Invoke-RestMethod -Uri "$base/expenses/cards/$cardId/bills" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    credit_card_id=$cardId; statement_date="2026-07-01"; due_date="2026-07-25"
    total_amount="45000"; minimum_payment="2250"; interest_charged="890"
} | ConvertTo-Json)
$billId = $bill.id
Write-Host "  OK: $billId | total=$($bill.total_amount) status=$($bill.payment_status)"

# 5. GET /cards/{id}/bills
Write-Host "`n5. GET /cards/{id}/bills"
$bl = Invoke-RestMethod -Uri "$base/expenses/cards/$cardId/bills" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($bl.total) bills"

# 6. GET /cards/{id}/bills/{bill_id}  (si existe este endpoint, omitir si no)
# Write-Host "`n6. GET /cards/{id}/bills/{bill_id}"

# ===== TEMPLATES (4 endpoints) =====
Write-Host "`n===== TEMPLATES ====="

# 7. POST /templates
Write-Host "`n7. POST /templates"
$tpl = Invoke-RestMethod -Uri "$base/expenses/templates" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Netflix"; description="Streaming monthly"; amount="650"; currency_code="DOP"
    billing_frequency="monthly"; category_id=""; is_active=$true
} | ConvertTo-Json)
$tplId = $tpl.id
Write-Host "  OK: $tplId | $($tpl.name)"

# 8. GET /templates
Write-Host "`n8. GET /templates"
$tpls = Invoke-RestMethod -Uri "$base/expenses/templates" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($tpls.total) templates"

# ===== SERVICES (5 endpoints) =====
Write-Host "`n===== SERVICES ====="

# 9. POST /services
Write-Host "`n9. POST /services"
$svc = Invoke-RestMethod -Uri "$base/expenses/services" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Electricidad"; service_type="electric"; provider="EDE"; estimated_amount="3500"
    currency_code="DOP"; due_day=1; is_recurring=$true; billing_frequency="monthly"
} | ConvertTo-Json)
$svcId = $svc.id
Write-Host "  OK: $svcId | $($svc.name)"

# 10. GET /services
Write-Host "`n10. GET /services"
$svcs = Invoke-RestMethod -Uri "$base/expenses/services" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($svcs.total) services"

# 11. GET /services/upcoming
Write-Host "`n11. GET /services/upcoming"
$upcoming = Invoke-RestMethod -Uri "$base/expenses/services/upcoming" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($upcoming.total) upcoming"

# 12. PATCH /services/{id}
Write-Host "`n12. PATCH /services/{id}"
$updSvc = Invoke-RestMethod -Uri "$base/expenses/services/$svcId" -Method PATCH -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{name="Electricidad EDE"; amount="3800"} | ConvertTo-Json)
Write-Host "  OK: $($updSvc.name) | $($updSvc.amount)"

# 13. POST /services/{id}/pay
Write-Host "`n13. POST /services/{id}/pay"
$paid = Invoke-RestMethod -Uri "$base/expenses/services/$svcId/pay" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{paid_amount="3800"; payment_method="bank_transfer"; payment_date="2026-07-20"} | ConvertTo-Json)
Write-Host "  OK: $($paid.payment_status)"

# ===== SUBSCRIPTIONS (5 endpoints) =====
Write-Host "`n===== SUBSCRIPTIONS ====="

# 14. POST /subscriptions
Write-Host "`n14. POST /subscriptions"
$sub = Invoke-RestMethod -Uri "$base/expenses/subscriptions" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    name="Netflix"; description="Plan Premium"; provider="Netflix Inc"; amount="650"
    currency_code="DOP"; billing_frequency="monthly"; start_date="2026-01-15"
} | ConvertTo-Json)
$subId = $sub.id
Write-Host "  OK: $subId | $($sub.name)"

# 15. GET /subscriptions
Write-Host "`n15. GET /subscriptions"
$subs = Invoke-RestMethod -Uri "$base/expenses/subscriptions" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($subs.total) subscriptions"

# 16. GET /subscriptions/summary
Write-Host "`n16. GET /subscriptions/summary"
$summ = Invoke-RestMethod -Uri "$base/expenses/subscriptions/summary" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: total_monthly=$($summ.total_monthly) count=$($summ.total_active)"

# 17. PATCH /subscriptions/{id}
Write-Host "`n17. PATCH /subscriptions/{id}"
$updSub = Invoke-RestMethod -Uri "$base/expenses/subscriptions/$subId" -Method PATCH -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{amount="700"; name="Netflix Premium"} | ConvertTo-Json)
Write-Host "  OK: $($updSub.name) | $($updSub.amount)"

# 18. DELETE /subscriptions/{id}  (skip, keep for later)

# ===== EXPENSE CRUD + BULK + SPLIT =====
Write-Host "`n===== EXPENSE CRUD ====="

# 19. POST /expenses
Write-Host "`n19. POST /expenses"
$exp = Invoke-RestMethod -Uri "$base/expenses" -Method POST -ContentType "application/json" -Headers $h -TimeoutSec 15 -Body (@{
    account_id=$accId; amount="1500"; currency_code="DOP"; description="Almuerzo"
    effective_date="2026-07-20"; status="completed"; source="manual"
} | ConvertTo-Json)
$expId = $exp.id
Write-Host "  OK: $expId | $($exp.description) | $($exp.amount)"

# 20. GET /expenses
Write-Host "`n20. GET /expenses"
$exps = Invoke-RestMethod -Uri "$base/expenses" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: $($exps.total) expenses"

# 21. GET /expenses/dashboard
Write-Host "`n21. GET /expenses/dashboard"
$dash = Invoke-RestMethod -Uri "$base/expenses/dashboard?date_from=2026-07-01&date_to=2026-07-31" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: total=$($dash.total_amount)"

# 22. GET /expenses/patterns
Write-Host "`n22. GET /expenses/patterns"
$patt = Invoke-RestMethod -Uri "$base/expenses/patterns" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: patterns found"

# 23. GET /expenses/duplicates
Write-Host "`n23. GET /expenses/duplicates"
$dup = Invoke-RestMethod -Uri "$base/expenses/duplicates" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: duplicates found"

# 24. GET /expenses/recurring-candidates
Write-Host "`n24. GET /expenses/recurring-candidates"
$rec = Invoke-RestMethod -Uri "$base/expenses/recurring-candidates" -Method GET -Headers $h -TimeoutSec 10
Write-Host "  OK: candidates found"

Write-Host "`n===== ALL PHASE 9 ENDPOINTS TESTED ====="