$ErrorActionPreference = "Stop"
$deadline = (Get-Date).AddMinutes(3)
do { try { $health = Invoke-RestMethod http://127.0.0.1:8000/api/v1/health -TimeoutSec 5; if ($health.status -eq "ok") { break } } catch {} ; Start-Sleep -Seconds 3 } while ((Get-Date) -lt $deadline)
if ($health.status -ne "ok") { throw "API health check failed." }
$web = Invoke-WebRequest http://127.0.0.1:3000 -UseBasicParsing -TimeoutSec 10
if ($web.StatusCode -ne 200) { throw "Web health check failed." }
Write-Host "FraudLens API and web checks passed." -ForegroundColor Green
