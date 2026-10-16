param([switch]$Rebuild, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$dockerExe = if ($dockerCommand) { $dockerCommand.Source } else { 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' }
$dashboardUrl = 'http://127.0.0.1:8502/'

function Docker-Ready {
    $probe = New-Object System.Diagnostics.Process
    try {
        $probe.StartInfo.FileName = $dockerExe
        $probe.StartInfo.Arguments = 'info --format {{.ServerVersion}}'
        $probe.StartInfo.UseShellExecute = $false
        $probe.StartInfo.CreateNoWindow = $true
        $probe.StartInfo.RedirectStandardOutput = $true
        $probe.StartInfo.RedirectStandardError = $true
        [void]$probe.Start()
        if (!$probe.WaitForExit(12000)) { $probe.Kill(); return $false }
        return ($probe.ExitCode -eq 0)
    } catch { return $false }
    finally { $probe.Dispose() }
}
function Compose {
    & $dockerExe compose @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed ($LASTEXITCODE). See the output above." }
}
function Warehouse-Ready {
    try {
        $rows = & $dockerExe compose exec -T postgres psql -U pitchpulse -d pitchpulse -Atqc 'SELECT COUNT(*) FROM football.matches' 2>$null
        return ($LASTEXITCODE -eq 0 -and "$rows" -match '^\s*[1-9][0-9]*\s*$')
    } catch { return $false }
}
function Web-Ready([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return ($response.StatusCode -eq 200)
    } catch { return $false }
}

try {
    Write-Host ''
    Write-Host 'Starting PitchPulse360 Football Analytics' -ForegroundColor Cyan
    Write-Host "Project: $PSScriptRoot"
    if (!(Test-Path -LiteralPath $dockerExe)) { throw 'Docker Desktop is not installed. Install it before starting this project.' }
    if (!(Docker-Ready)) {
        $desktopExe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
        if (!(Test-Path -LiteralPath $desktopExe)) { throw 'Docker is not ready. Open Docker Desktop, then try this launcher again.' }
        Write-Host 'Opening Docker Desktop and waiting for its engine...'
        Start-Process -FilePath $desktopExe -WindowStyle Hidden
        $deadline = (Get-Date).AddMinutes(4)
        while (!(Docker-Ready)) {
            if ((Get-Date) -gt $deadline) { throw 'Docker did not become ready within four minutes. Check Docker Desktop for an error and try again.' }
            Start-Sleep -Seconds 3
        }
    }
    $engineType = & $dockerExe info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0 -or "$engineType".Trim() -ne 'linux') { throw 'This project needs Docker Desktop in Linux containers mode.' }
    $imageIds = & $dockerExe image ls --quiet pitchpulse360:complete
    if ($LASTEXITCODE -ne 0) { throw 'Could not check the local Docker images.' }
    $imageMissing = [string]::IsNullOrWhiteSpace(($imageIds -join ''))
    if ($Rebuild -or $imageMissing) {
        Write-Host 'Building the application image. The first build can take several minutes.'
        Compose build
    }
    Write-Host 'Starting databases, message queue and Prefect...'
    Compose up -d --wait --wait-timeout 240 postgres mongo rabbitmq prefect
    $lakeReady = (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\lakehouse\silver_leagues\_delta_log')) -and
                 (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'data\lakehouse\gold_standings\_delta_log')) -and
                 (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'results\last_run.json'))
    if (!(Warehouse-Ready) -or !$lakeReady) {
        Write-Host 'Initializing the football dataset and running verification...'
        Compose run --rm pipeline run
        Compose run --rm pipeline verify
    } else {
        Write-Host 'The prepared football data is available. Using the existing dataset.'
    }
    Write-Host 'Starting the dashboard, API, event consumer and scheduler...'
    Compose up -d scheduler consumer api dashboard
    $deadline = (Get-Date).AddSeconds(120)
    while (!(Web-Ready ($dashboardUrl + '_stcore/health')) -or !(Web-Ready 'http://127.0.0.1:8002/')) {
        if ((Get-Date) -gt $deadline) { throw 'The dashboard or API did not become ready. Run .\Start.ps1 -Action Status to inspect the services.' }
        Start-Sleep -Seconds 2
    }
    Write-Host ''
    Write-Host 'PitchPulse360 is ready.' -ForegroundColor Green
    Write-Host "Dashboard: $dashboardUrl"
    Write-Host 'API docs: http://127.0.0.1:8002/docs'
    Write-Host 'Close this window normally. The services keep running in Docker.'
    Write-Host 'To stop the project: .\Start.ps1 -Action Stop'
    if (!$NoBrowser) { Start-Process $dashboardUrl }
    exit 0
} catch {
    Write-Host ''
    Write-Host ('Startup failed: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
