Write-Host "===== PHASE 12: TARJETAS AVANZADAS =====" -ForegroundColor Cyan

$body = @{email="phase12_test@fip.com"; password="TestPass123!"} | ConvertTo-Json
$reg = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/auth/register" -Method POST -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue
$login = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/auth/login" -Method POST -Body $body -ContentType "application/json"
$token = $login.tokens.access_token
$headers = @{Authorization="Bearer $token"}

Write-Host "`nLOGIN OK" -ForegroundColor Green

$acctBody = @{name="Card Test Account"; account_type="checking"; initial_balance=0} | ConvertTo-Json
$acct = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/accounts" -Method POST -Body $acctBody -ContentType "application/json" -Headers $headers
$accountId = $acct.id

# 1. Create card
Write-Host "`n1. POST /cards (create)" -ForegroundColor Yellow
$cardBody = @{name="Visa Platinum"; account_id=$accountId; last_four_digits="4532"; card_network="visa"; credit_limit="150000"; available_credit="120000"; statement_day=15; payment_due_day=5; interest_rate="0.0240"} | ConvertTo-Json
$card = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards" -Method POST -Body $cardBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: $($card.id) | $($card.name)" -ForegroundColor Green
$cardId = $card.id

# 2. List cards
Write-Host "`n2. GET /cards (list)" -ForegroundColor Yellow
$cards = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards" -Method GET -Headers $headers
Write-Host "  OK: $($cards.total) cards" -ForegroundColor Green

# 3. Get card detail
Write-Host "`n3. GET /cards/{id} (detail)" -ForegroundColor Yellow
$detail = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId" -Method GET -Headers $headers
Write-Host "  OK: $($detail.name) | utilization=$($detail.utilization.status)" -ForegroundColor Green

# 4. Update card
Write-Host "`n4. PATCH /cards/{id} (update)" -ForegroundColor Yellow
$updateBody = @{name="Visa Platinum Black"; credit_limit="200000"} | ConvertTo-Json
$updated = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId" -Method PATCH -Body $updateBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: $($updated.name) | limit=$($updated.credit_limit)" -ForegroundColor Green

# 5. Cards summary
Write-Host "`n5. GET /cards/summary" -ForegroundColor Yellow
$summary = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/summary" -Method GET -Headers $headers
Write-Host "  OK: total=$($summary.total_cards) limit=$($summary.total_credit_limit)" -ForegroundColor Green

# 6. Utilization
Write-Host "`n6. GET /cards/{id}/utilization" -ForegroundColor Yellow
$util = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/utilization" -Method GET -Headers $headers
Write-Host "  OK: pct=$($util.utilization_percentage) status=$($util.status)" -ForegroundColor Green

# 7. Utilization history
Write-Host "`n7. GET /cards/{id}/utilization/history" -ForegroundColor Yellow
$hist = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/utilization/history?months=3" -Method GET -Headers $headers
Write-Host "  OK: months=$($hist.months) history=$($hist.history.Count) entries" -ForegroundColor Green

# 8. Create bill
Write-Host "`n8. POST /cards/{id}/bills (create)" -ForegroundColor Yellow
$billBody = @{statement_date="2026-07-01"; due_date="2026-07-25"; total_amount="35000"; minimum_payment="1750"} | ConvertTo-Json
$bill = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/bills" -Method POST -Body $billBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: $($bill.id) | status=$($bill.payment_status)" -ForegroundColor Green
$billId = $bill.id

# 9. List bills
Write-Host "`n9. GET /cards/{id}/bills (list)" -ForegroundColor Yellow
$bills = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/bills" -Method GET -Headers $headers
Write-Host "  OK: $($bills.total) bills" -ForegroundColor Green

# 10. Pay bill
Write-Host "`n10. POST /cards/{id}/bills/{billId}/pay" -ForegroundColor Yellow
$payBody = @{amount=35000; payment_method="manual"} | ConvertTo-Json
$paid = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/bills/$billId/pay" -Method POST -Body $payBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: status=$($paid.payment_status)" -ForegroundColor Green

# 11. Generate statement
Write-Host "`n11. POST /cards/{id}/statements/generate" -ForegroundColor Yellow
$gen = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/statements/generate" -Method POST -Headers $headers
Write-Host "  OK: total=$($gen.total_amount) tx_count=$($gen.transaction_count)" -ForegroundColor Green

# 12. Create spending limit
Write-Host "`n12. POST /cards/{id}/limits (create)" -ForegroundColor Yellow
$limitBody = @{limit_type="monthly"; limit_amount="50000"; alert_threshold=80} | ConvertTo-Json
$limit = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/limits" -Method POST -Body $limitBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: $($limit.id) | type=$($limit.limit_type) limit=$($limit.limit_amount)" -ForegroundColor Green
$limitId = $limit.id

# 13. List limits
Write-Host "`n13. GET /cards/{id}/limits (list)" -ForegroundColor Yellow
$limits = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/limits" -Method GET -Headers $headers
Write-Host "  OK: $($limits.total) limits" -ForegroundColor Green

# 14. Delete limit
Write-Host "`n14. DELETE /cards/{id}/limits/{limitId}" -ForegroundColor Yellow
$delLimit = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId/limits/$limitId" -Method DELETE -Headers $headers
Write-Host "  OK: $($delLimit.message)" -ForegroundColor Green

# 15. Card alerts
Write-Host "`n15. GET /cards/alerts/all" -ForegroundColor Yellow
$alerts = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/alerts/all" -Method GET -Headers $headers
Write-Host "  OK: $($alerts.total) alerts" -ForegroundColor Green

# 16. Check alerts
Write-Host "`n16. POST /cards/alerts/check" -ForegroundColor Yellow
$check = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/alerts/check" -Method POST -Headers $headers
Write-Host "  OK: new=$($check.new_alerts) unread=$($check.unread_alerts)" -ForegroundColor Green

# 17. Mark alerts read
Write-Host "`n17. POST /cards/alerts/read" -ForegroundColor Yellow
$markBody = @{mark_all=$true} | ConvertTo-Json
$mark = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/alerts/read" -Method POST -Body $markBody -ContentType "application/json" -Headers $headers
Write-Host "  OK: $($mark.message)" -ForegroundColor Green

# Cleanup
Write-Host "`n===== CLEANUP =====" -ForegroundColor Magenta
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/v1/cards/$cardId" -Method DELETE -Headers $headers | Out-Null
Write-Host "Card deleted" -ForegroundColor Gray

Write-Host "`n===== PHASE 12 COMPLETE =====" -ForegroundColor Cyan
