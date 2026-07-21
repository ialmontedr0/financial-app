# Phase 15: AI/ML - Endpoint Tests
$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "phase15_$(Get-Random)@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 15: AI/ML =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`nREGISTER + LOGIN" -ForegroundColor Yellow
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "LOGIN OK" -ForegroundColor Green

# 1. Classifier Status
Write-Host "`n1. GET /ai/classifier/status" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/classifier/status" -Headers $HEADERS
Write-Host "  OK: trained=$($r.is_trained) version=$($r.model_version)" -ForegroundColor Green

# 2. Predict Expenses (not trained)
Write-Host "`n2. POST /ai/predict/expenses" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/predict/expenses" -Method Post -Headers $HEADERS
Write-Host "  OK: amount=$($r.predicted_amount) reason=$($r.reason)" -ForegroundColor Green

# 3. Predict Income (not trained)
Write-Host "`n3. POST /ai/predict/income" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/predict/income" -Method Post -Headers $HEADERS
Write-Host "  OK: amount=$($r.predicted_amount) reason=$($r.reason)" -ForegroundColor Green

# 4. Detect Anomalies (not trained)
Write-Host "`n4. POST /ai/anomalies/detect" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/anomalies/detect" -Method Post -Headers $HEADERS
Write-Host "  OK: anomalies=$($r.total_anomalies) model=$($r.model_version)" -ForegroundColor Green

# 5. Anomaly History
Write-Host "`n5. GET /ai/anomalies/history" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/anomalies/history" -Headers $HEADERS
Write-Host "  OK: total=$($r.total)" -ForegroundColor Green

# 6. Recommendations
Write-Host "`n6. POST /ai/recommendations" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/recommendations" -Method Post -Headers $HEADERS
Write-Host "  OK: count=$($r.recommendations.Count)" -ForegroundColor Green

# 7. Recommendation History
Write-Host "`n7. GET /ai/recommendations/history" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/recommendations/history" -Headers $HEADERS
Write-Host "  OK: total=$($r.total)" -ForegroundColor Green

# 8. List Models
Write-Host "`n8. GET /ai/models" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/models" -Headers $HEADERS
Write-Host "  OK: models=$($r.models.Count)" -ForegroundColor Green

# 9. Classify (not trained)
Write-Host "`n9. POST /ai/classify" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/ai/classify?transaction_id=00000000-0000-0000-0000-000000000001&description=Supermercado+Nacional" -Method Post -Headers $HEADERS
Write-Host "  OK: category=$($r.predicted_category) model=$($r.model_version)" -ForegroundColor Green

Write-Host "`n===== PHASE 15 COMPLETE =====" -ForegroundColor Cyan