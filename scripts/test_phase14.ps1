$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "analyticstest_ps1_$(Get-Random)@test.com"
$PASS  = "Test1234!"
$HEADERS = @{}

Write-Host "===== PHASE 14: ANALITICA ====="

# Register + Login
Write-Host ""
Write-Host "REGISTER + LOGIN"
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method POST -Body (@{email=$EMAIL;password=$PASS}|ConvertTo-Json) -ContentType "application/json" -ErrorAction SilentlyContinue
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method POST -Body (@{email=$EMAIL;password=$PASS}|ConvertTo-Json) -ContentType "application/json"
$HEADERS["Authorization"] = "Bearer $($login.tokens.access_token)"
Write-Host "LOGIN OK"

# 1. GET /analytics/kpis/monthly
Write-Host ""
Write-Host "1. GET /analytics/kpis/monthly"
$kpis = Invoke-RestMethod -Uri "$BASE/analytics/kpis/monthly" -Method GET -Headers $HEADERS
Write-Host "  OK: income=$($kpis.total_income) expenses=$($kpis.total_expenses) savings=$($kpis.savings_rate)% net=$($kpis.net_flow)"

# 2. GET /analytics/kpis/portfolio
Write-Host ""
Write-Host "2. GET /analytics/kpis/portfolio"
$portfolio = Invoke-RestMethod -Uri "$BASE/analytics/kpis/portfolio" -Method GET -Headers $HEADERS
Write-Host "  OK: net_worth=$($portfolio.net_worth) assets=$($portfolio.total_assets) liabilities=$($portfolio.total_liabilities) dti=$($portfolio.debt_to_income)%"

# 3. GET /analytics/trends/spending
Write-Host ""
Write-Host "3. GET /analytics/trends/spending"
$spending = Invoke-RestMethod -Uri "$BASE/analytics/trends/spending" -Method GET -Headers $HEADERS
Write-Host "  OK: periods=$($spending.summary.periods) total=$($spending.summary.total_spent) avg=$($spending.summary.average)"

# 4. GET /analytics/trends/income
Write-Host ""
Write-Host "4. GET /analytics/trends/income"
$income = Invoke-RestMethod -Uri "$BASE/analytics/trends/income" -Method GET -Headers $HEADERS
Write-Host "  OK: periods=$($income.summary.periods) total=$($income.summary.total_income) avg=$($income.summary.average)"

# 5. GET /analytics/categories/breakdown
Write-Host ""
Write-Host "5. GET /analytics/categories/breakdown"
$breakdown = Invoke-RestMethod -Uri "$BASE/analytics/categories/breakdown" -Method GET -Headers $HEADERS
Write-Host "  OK: categories=$($breakdown.categories.Count) grand_total=$($breakdown.grand_total)"

# 6. GET /analytics/categories/top
Write-Host ""
Write-Host "6. GET /analytics/categories/top?limit=3"
$top = Invoke-RestMethod -Uri "$BASE/analytics/categories/top?limit=3" -Method GET -Headers $HEADERS
Write-Host "  OK: top=$($top.top_categories.Count) categories"

# 7. GET /analytics/cash-flow
Write-Host ""
Write-Host "7. GET /analytics/cash-flow"
$cf = Invoke-RestMethod -Uri "$BASE/analytics/cash-flow" -Method GET -Headers $HEADERS
Write-Host "  OK: months=$($cf.summary.months) income=$($cf.summary.total_income) expenses=$($cf.summary.total_expenses) net=$($cf.summary.net_flow)"

# 8. GET /analytics/cash-flow/by-account
Write-Host ""
Write-Host "8. GET /analytics/cash-flow/by-account"
$cfa = Invoke-RestMethod -Uri "$BASE/analytics/cash-flow/by-account" -Method GET -Headers $HEADERS
Write-Host "  OK: accounts=$($cfa.accounts.Count)"

# 9. GET /analytics/net-worth
Write-Host ""
Write-Host "9. GET /analytics/net-worth"
$nw = Invoke-RestMethod -Uri "$BASE/analytics/net-worth" -Method GET -Headers $HEADERS
Write-Host "  OK: net_worth=$($nw.net_worth) assets=$($nw.total_assets) liabilities=$($nw.total_liabilities) cc_debt=$($nw.credit_card_debt)"

# 10. GET /analytics/heatmaps/spending
Write-Host ""
Write-Host "10. GET /analytics/heatmaps/spending"
$heatmap = Invoke-RestMethod -Uri "$BASE/analytics/heatmaps/spending" -Method GET -Headers $HEADERS
Write-Host "  OK: granularity=$($heatmap.granularity) data_points=$($heatmap.data.Count) max=$($heatmap.max_value)"

# 11. GET /analytics/heatmaps/spending?granularity=category_month
Write-Host ""
Write-Host "11. GET /analytics/heatmaps/spending?granularity=category_month"
$heatmap2 = Invoke-RestMethod -Uri "$BASE/analytics/heatmaps/spending?granularity=category_month" -Method GET -Headers $HEADERS
Write-Host "  OK: granularity=$($heatmap2.granularity) data_points=$($heatmap2.data.Count) categories=$($heatmap2.categories.Count)"

# 12. GET /analytics/dashboard
Write-Host ""
Write-Host "12. GET /analytics/dashboard"
$dash = Invoke-RestMethod -Uri "$BASE/analytics/dashboard" -Method GET -Headers $HEADERS
Write-Host "  OK: kpis=$($null -ne $dash.kpis) net_worth=$($null -ne $dash.net_worth) cash_flow=$($null -ne $dash.cash_flow) goals=$($dash.goals.Count)"

Write-Host ""
Write-Host "===== PHASE 14 COMPLETE ====="
