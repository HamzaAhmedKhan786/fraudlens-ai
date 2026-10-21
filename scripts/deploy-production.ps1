[CmdletBinding()]
param([switch]$SkipBuild)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env.production"
if (-not (Test-Path -LiteralPath $envFile)) { throw "Create .env.production from .env.production.example first." }
$required = @("API_KEY","DATABASE_URL","POSTGRES_PASSWORD","OBJECT_STORAGE_ACCESS_KEY","OBJECT_STORAGE_SECRET_KEY","FRAUDLENS_API_KEY")
$values = @{}
Get-Content -LiteralPath $envFile | ForEach-Object { if ($_ -match '^([^#=]+)=(.*)$') { $values[$matches[1].Trim()] = $matches[2].Trim() } }
foreach ($name in $required) { if (-not $values[$name] -or $values[$name] -match 'CHANGE_ME|replace-with') { throw "$name is missing or unsafe." } }
if ($values.API_KEY -ne $values.FRAUDLENS_API_KEY) { throw "API_KEY and FRAUDLENS_API_KEY must match." }
$args = @("compose","--env-file",$envFile,"-f","compose.production.yaml")
if (-not $SkipBuild) { & docker @args build --pull; if ($LASTEXITCODE) { throw "Image build failed." } }
& docker @args run --rm api alembic upgrade head; if ($LASTEXITCODE) { throw "Database migration failed." }
& docker @args up -d --remove-orphans; if ($LASTEXITCODE) { throw "Deployment failed." }
& (Join-Path $PSScriptRoot "verify-deployment.ps1")
