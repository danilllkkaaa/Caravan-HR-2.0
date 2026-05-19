$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$env:NEXT_PUBLIC_API_URL = "http://localhost:8001"
corepack pnpm --filter @corp-portal/web dev
