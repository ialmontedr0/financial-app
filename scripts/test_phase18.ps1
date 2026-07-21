# Phase 18: Notificaciones - Endpoint Tests
$BASE = "http://127.0.0.1:8080/api/v1"
$EMAIL = "phase18_$(Get-Random)@test.com"
$PASS = "TestPass123!"

Write-Host "===== PHASE 18: NOTIFICACIONES =====" -ForegroundColor Cyan

# Register + Login
Write-Host "`nREGISTER + LOGIN" -ForegroundColor Yellow
$reg = Invoke-RestMethod -Uri "$BASE/auth/register" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$login = Invoke-RestMethod -Uri "$BASE/auth/login" -Method Post -ContentType "application/json" -Body "{`"email`":`"$EMAIL`",`"password`":`"$PASS`"}"
$TOKEN = $login.tokens.access_token
$HEADERS = @{ Authorization = "Bearer $TOKEN" }
Write-Host "LOGIN OK ($EMAIL)" -ForegroundColor Green

# 1. Create Notification
Write-Host "`n1. POST /notifications/ (create)" -ForegroundColor Yellow
$body = @{
    type = "transaction_alert"
    title = "Nueva transaccion detectada"
    body = "Se detecto una transaccion de $1,500.00 DOP en Supermercado"
    channels = @("push")
    data = @{ amount = -1500; currency = "DOP"; category = "Alimentacion" }
} | ConvertTo-Json -Depth 5
$r = Invoke-RestMethod -Uri "$BASE/notifications/" -Method Post -ContentType "application/json" -Body $body -Headers $HEADERS
Write-Host "  OK: success=$($r.success) results=$($r.results.Count)" -ForegroundColor Green

# 2. List Notifications
Write-Host "`n2. GET /notifications/ (list)" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/notifications/" -Headers $HEADERS
Write-Host "  OK: total=$($r.total) items=$($r.notifications.Count)" -ForegroundColor Green

# 3. List with Filters
Write-Host "`n3. GET /notifications/?channel=push&is_read=false (filters)" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/notifications/?channel=push&is_read=false" -Headers $HEADERS
Write-Host "  OK: total=$($r.total)" -ForegroundColor Green

# 4. Get Notification Detail (use first from list)
Write-Host "`n4. GET /notifications/{id} (detail)" -ForegroundColor Yellow
if ($r.notifications.Count -gt 0) {
    $NOTIF_ID = $r.notifications[0].id
    $detail = Invoke-RestMethod -Uri "$BASE/notifications/$NOTIF_ID" -Headers $HEADERS
    Write-Host "  OK: id=$($detail.id) type=$($detail.type) title=$($detail.title)" -ForegroundColor Green
} else {
    Write-Host "  SKIP: no notifications to detail" -ForegroundColor DarkYellow
    $NOTIF_ID = $null
}

# 5. Mark as Read
Write-Host "`n5. PATCH /notifications/{id}/read (mark read)" -ForegroundColor Yellow
if ($NOTIF_ID) {
    $r = Invoke-RestMethod -Uri "$BASE/notifications/$NOTIF_ID/read" -Method Patch -Headers $HEADERS
    Write-Host "  OK: success=$($r.success)" -ForegroundColor Green
} else {
    Write-Host "  SKIP: no notification to mark" -ForegroundColor DarkYellow
}

# 6. Get Preferences
Write-Host "`n6. GET /notifications/preferences/ (get prefs)" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/notifications/preferences/" -Headers $HEADERS
Write-Host "  OK: email=$($r.email_enabled) push=$($r.push_enabled) telegram=$($r.telegram_enabled) discord=$($r.discord_enabled) webhook=$($r.webhook_enabled)" -ForegroundColor Green

# 7. Update Preferences
Write-Host "`n7. PUT /notifications/preferences/ (update prefs)" -ForegroundColor Yellow
$body = @{
    email_enabled = $true
    push_enabled = $true
    telegram_enabled = $false
    discord_enabled = $false
    webhook_enabled = $false
} | ConvertTo-Json
$r = Invoke-RestMethod -Uri "$BASE/notifications/preferences/" -Method Put -ContentType "application/json" -Body $body -Headers $HEADERS
Write-Host "  OK: email=$($r.email_enabled) push=$($r.push_enabled)" -ForegroundColor Green

# 8. Send Test Notification
Write-Host "`n8. POST /notifications/test (send test)" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/notifications/test" -Method Post -Headers $HEADERS
Write-Host "  OK: success=$($r.success) results=$($r.results.Count)" -ForegroundColor Green

# 9. Get Stats
Write-Host "`n9. GET /notifications/stats/ (stats)" -ForegroundColor Yellow
$r = Invoke-RestMethod -Uri "$BASE/notifications/stats/" -Headers $HEADERS
Write-Host "  OK: total=$($r.total) unread=$($r.unread) channels=$($r.by_channel.Count) types=$($r.by_type.Count)" -ForegroundColor Green

# 10. Bulk Mark Read
Write-Host "`n10. POST /notifications/bulk-read (bulk)" -ForegroundColor Yellow
$allIds = @()
if ($rNotifications = Invoke-RestMethod -Uri "$BASE/notifications/" -Headers $HEADERS) {
    foreach ($n in $rNotifications.notifications) {
        if (-not $n.is_read) { $allIds += $n.id }
    }
}
if ($allIds.Count -gt 0) {
    $body = @{ notification_ids = $allIds } | ConvertTo-Json -Depth 3
    $r = Invoke-RestMethod -Uri "$BASE/notifications/bulk-read" -Method Post -ContentType "application/json" -Body $body -Headers $HEADERS
    Write-Host "  OK: success=$($r.success) marked=$($r.count)" -ForegroundColor Green
} else {
    Write-Host "  SKIP: no unread notifications" -ForegroundColor DarkYellow
}

# 11. Delete Notification (create one first)
Write-Host "`n11. DELETE /notifications/{id} (delete)" -ForegroundColor Yellow
$body = @{
    type = "system"
    title = "Test para borrar"
    body = "Esta notificacion sera eliminada"
    channels = @("push")
} | ConvertTo-Json -Depth 5
$created = Invoke-RestMethod -Uri "$BASE/notifications/" -Method Post -ContentType "application/json" -Body $body -Headers $HEADERS
if ($created.results.Count -gt 0) {
    $listAfter = Invoke-RestMethod -Uri "$BASE/notifications/" -Headers $HEADERS
    $toDelete = $listAfter.notifications | Where-Object { $_.title -eq "Test para borrar" } | Select-Object -First 1
    if ($toDelete) {
        $r = Invoke-RestMethod -Uri "$BASE/notifications/$($toDelete.id)" -Method Delete -Headers $HEADERS
        Write-Host "  OK: deleted" -ForegroundColor Green
    } else {
        Write-Host "  SKIP: could not find notification to delete" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "  SKIP: could not create notification to delete" -ForegroundColor DarkYellow
}

Write-Host "`n===== PHASE 18 COMPLETE =====" -ForegroundColor Cyan
