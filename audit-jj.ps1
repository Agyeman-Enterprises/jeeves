# AUDIT 2: JJ health snapshot
# Read-only. No fixes, no writes. Safe to run.

Write-Host "`n=== JJ HEALTH SNAPSHOT ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

# 1. Repo + git state
Write-Host "--- REPO ---" -ForegroundColor Yellow
Write-Host "Path: $(Get-Location)"
try {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    $lastCommit = git log -1 --format='%h %s (%cr)' 2>$null
    Write-Host "Branch: $branch"
    Write-Host "Last commit: $lastCommit"
} catch { Write-Host "Not a git repo or git unavailable" }

# 2. Frontend env
Write-Host "`n--- FRONTEND ENV ---" -ForegroundColor Yellow
$envPath = "C:\DEV\jeeves\frontend\.env.local"
if (Test-Path $envPath) {
    $env = Get-Content $envPath -Raw
    if ($env -match "NEXT_PUBLIC_SUPABASE_URL=https://([a-z0-9]+)") {
        Write-Host "Supabase project ref: $($matches[1])"
    } else { Write-Host "SUPABASE_URL not found" }
    Write-Host ("ANON_KEY populated: " + [bool]($env -match "NEXT_PUBLIC_SUPABASE_ANON_KEY=ey"))
    Write-Host ("JARVIS_API_KEY populated: " + [bool]($env -match "JARVIS_API_KEY=iq-"))
} else { Write-Host "No .env.local at $envPath" }

# 3. Backend health
Write-Host "`n--- BACKEND (localhost:4004) ---" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:4004/health" -TimeoutSec 3
    Write-Host ("Status: " + $health.status)
    Write-Host ("cloud_available field: " + ($health.PSObject.Properties.Name -contains "cloud_available"))
    Write-Host ("Response: " + ($health | ConvertTo-Json -Compress))
} catch { Write-Host "BACKEND NOT RUNNING on :4004" -ForegroundColor Red }

# 4. Frontend health
Write-Host "`n--- FRONTEND (localhost:3000) ---" -ForegroundColor Yellow
try {
    $fe = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 3 -UseBasicParsing
    Write-Host "Status: $($fe.StatusCode) (UP)"
} catch { Write-Host "FRONTEND NOT RUNNING on :3000" -ForegroundColor Red }

# 5. Endpoint quick-hit
Write-Host "`n--- KEY ENDPOINTS ---" -ForegroundColor Yellow
$key = $null
if (Test-Path $envPath) {
    if ((Get-Content $envPath -Raw) -match "JARVIS_API_KEY=(iq-[a-zA-Z0-9_-]+)") {
        $key = $matches[1]
    }
}
if ($key) {
    $hdr = @{ "Authorization" = "Bearer $key" }
    foreach ($ep in @("/brain/status","/brain/goals","/brain/questions","/agents/status","/jang/status","/empire/agents","/api/jobs")) {
        try {
            $r = Invoke-RestMethod -Uri "http://localhost:4004$ep" -Headers $hdr -TimeoutSec 5
            Write-Host "OK  $ep"
        } catch {
            $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { "no_conn" }
            Write-Host "ERR $ep (status=$code)" -ForegroundColor Red
        }
    }
} else { Write-Host "No API key found, skipping endpoint checks" }

# 6. Agent count
Write-Host "`n--- AGENT COUNT ---" -ForegroundColor Yellow
$agentPath = "C:\DEV\jeeves\app\agents"
if (Test-Path $agentPath) {
    $count = (Get-ChildItem $agentPath -Filter "*.py" -Recurse | Measure-Object).Count
    Write-Host "Python agent files: $count"
} else { Write-Host "Agent path not found" }

# 7. gate7 recency
Write-Host "`n--- GATE7 ---" -ForegroundColor Yellow
$gatePath = "C:\DEV\jeeves\.claude\run-gate7.ps1"
if (Test-Path $gatePath) {
    $gate = Get-Item $gatePath
    Write-Host "run-gate7.ps1 last modified: $($gate.LastWriteTime)"
} else { Write-Host "run-gate7.ps1 not found" }

Write-Host "`n=== END SNAPSHOT ===`n" -ForegroundColor Cyan