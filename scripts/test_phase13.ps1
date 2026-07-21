$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "loantest_ps1_$(Get-Random)@test.com"
$PASS  = "Test1234!"
$HEADERS = @{}

Write-Host "===== PHASE 13: PRESTAMOS ====="

# Register + Login
Write-Host ""
Write-Host "REGISTER + LOGIN"
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method POST -Body (@{email=$EMAIL;password=$PASS}|ConvertTo-Json) -ContentType "application/json" -ErrorAction SilentlyContinue
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST -Body (@{email=$EMAIL;password=$PASS}|ConvertTo-Json) -ContentType "application/json"
$HEADERS["Authorization"] = "Bearer $($login.tokens.access_token)"
Write-Host "LOGIN OK"

# 1. POST /loans (create)
Write-Host ""
Write-Host "1. POST /loans (create)"
$loan = Invoke-RestMethod -Uri "$BASE/loans" -Method POST -Body (@{
    name = "Prestamo Personal"
    principal_amount = 100000
    annual_interest_rate = 12
    term_months = 24
    loan_type = "personal"
    lender_name = "Banco Popular"
}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: $($loan.id) | $($loan.name) | monthly=$($loan.monthly_payment) | amortization_entries=$($loan.amortization_entries_count)"
$LOAN_ID = $loan.id

# 2. GET /loans (list)
Write-Host ""
Write-Host "2. GET /loans (list)"
$loans = Invoke-RestMethod -Uri "$BASE/loans" -Method GET -Headers $HEADERS
Write-Host "  OK: $($loans.total) loans"

# 3. GET /loans/{id} (detail)
Write-Host ""
Write-Host "3. GET /loans/{id} (detail)"
$detail = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID" -Method GET -Headers $HEADERS
Write-Host "  OK: $($detail.name) | balance=$($detail.current_balance) | progress=$($detail.progress_pct)% | status=$($detail.status)"

# 4. PATCH /loans/{id} (update)
Write-Host ""
Write-Host "4. PATCH /loans/{id} (update)"
$updated = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID" -Method PATCH -Body (@{
    name = "Prestamo Personal Premium"
    lender_name = "BanReservas"
}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: $($updated.name) | lender=$($updated.lender_name)"

# 5. GET /loans/summary
Write-Host ""
Write-Host "5. GET /loans/summary"
$summary = Invoke-RestMethod -Uri "$BASE/loans/summary" -Method GET -Headers $HEADERS
Write-Host "  OK: total_balance=$($summary.total_balance) | monthly=$($summary.total_monthly_payment) | loans=$($summary.total_loans)"

# 6. GET /loans/{id}/amortization
Write-Host ""
Write-Host "6. GET /loans/{id}/amortization"
$amort = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/amortization" -Method GET -Headers $HEADERS
Write-Host "  OK: entries=$($amort.total_entries) | first=$($amort.entries[0].due_date) balance=$($amort.entries[0].balance_after)"

# 7. GET /loans/{id}/amortization/summary
Write-Host ""
Write-Host "7. GET /loans/{id}/amortization/summary"
$asummary = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/amortization/summary" -Method GET -Headers $HEADERS
Write-Host "  OK: total=$($asummary.total_entries) | paid=$($asummary.entries_paid) | remaining=$($asummary.entries_remaining) | progress=$($asummary.progress_pct)%"

# 8. POST /loans/{id}/payments (make payment)
Write-Host ""
Write-Host "8. POST /loans/{id}/payments (make payment)"
$payment = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/payments" -Method POST -Body (@{
    amount = 6000
    payment_method = "bank_transfer"
}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: payment_id=$($payment.payment_id) | principal=$($payment.principal_portion) | interest=$($payment.interest_portion) | balance_after=$($payment.balance_after)"

# 9. GET /loans/{id}/payments (list payments)
Write-Host ""
Write-Host "9. GET /loans/{id}/payments (list payments)"
$payments = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/payments" -Method GET -Headers $HEADERS
Write-Host "  OK: total=$($payments.total) | paid=$($payments.summary.total_paid) | interest=$($payments.summary.total_interest)"

# 10. GET /loans/{id}/early-payoff
Write-Host ""
Write-Host "10. GET /loans/{id}/early-payoff"
$payoff = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/early-payoff" -Method GET -Headers $HEADERS
Write-Host "  OK: payoff=$($payoff.total_payoff_amount) | saved=$($payoff.interest_saved) | penalty=$($payoff.early_payoff_penalty)"

# 11. POST /loans/simulate
Write-Host ""
Write-Host "11. POST /loans/simulate"
$sim = Invoke-RestMethod -Uri "$BASE/loans/simulate" -Method POST -Body (@{
    principal_amount = 200000
    annual_interest_rate = 15
    term_months = 36
    extra_monthly_payment = 2000
}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: monthly=$($sim.monthly_payment) | total_interest=$($sim.total_interest) | saved_with_extra=$($sim.interest_saved_with_extra)"

# 12. PATCH /loans/{id}/status
Write-Host ""
Write-Host "12. PATCH /loans/{id}/status (suspended)"
$suspend = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/status" -Method PATCH -Body (@{status="suspended"}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: status=$($suspend.status)"

# 13. PATCH /loans/{id}/status (reactivate)
Write-Host ""
Write-Host "13. PATCH /loans/{id}/status (active)"
$reactivate = Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID/status" -Method PATCH -Body (@{status="active"}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: status=$($reactivate.status)"

# 14. Create second loan for deletion test
Write-Host ""
Write-Host "14. POST /loans (create for delete)"
$loan2 = Invoke-RestMethod -Uri "$BASE/loans" -Method POST -Body (@{
    name = "Loan to Delete"
    principal_amount = 30000
    annual_interest_rate = 20
    term_months = 6
}|ConvertTo-Json) -ContentType "application/json" -Headers $HEADERS
Write-Host "  OK: $($loan2.id) | $($loan2.name)"
$LOAN2_ID = $loan2.id

# 15. DELETE /loans/{id}
Write-Host ""
Write-Host "15. DELETE /loans/{id}"
$del = Invoke-RestMethod -Uri "$BASE/loans/$LOAN2_ID" -Method DELETE -Headers $HEADERS
Write-Host "  OK: $($del.message)"

# 16. Verify deletion (should not appear in list)
Write-Host ""
Write-Host "16. GET /loans (verify deletion)"
$afterDel = Invoke-RestMethod -Uri "$BASE/loans" -Method GET -Headers $HEADERS
$found = $afterDel.loans | Where-Object { $_.id -eq $LOAN2_ID }
if ($found) { Write-Host "  FAIL: deleted loan still in list" } else { Write-Host "  OK: loan not in list" }

# Cleanup: delete first loan
Write-Host ""
Write-Host "CLEANUP"
Invoke-RestMethod -Uri "$BASE/loans/$LOAN_ID" -Method DELETE -Headers $HEADERS | Out-Null
Write-Host "Loan deleted"

Write-Host ""
Write-Host "===== PHASE 13 COMPLETE ====="
