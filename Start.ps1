param([ValidateSet('Start','Stop','Run','Test','Stream','Status')][string]$Action='Start')
$ErrorActionPreference='Stop'
$dockerExe=(Get-Command docker -ErrorAction SilentlyContinue).Source
if (!$dockerExe) { $dockerExe='C:\Program Files\Docker\Docker\resources\bin\docker.exe' }
if (!(Test-Path -LiteralPath $dockerExe)) { throw 'Install Docker Desktop first.' }
Set-Location -LiteralPath $PSScriptRoot
function Compose {
    & $dockerExe compose @args
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed ($LASTEXITCODE). See the output above." }
}
switch($Action) {
    'Start' {
        Compose build
        Compose up -d --wait --wait-timeout 240 postgres mongo rabbitmq prefect
        Compose run --rm pipeline run
        Compose run --rm pipeline verify
        Compose up -d scheduler consumer api dashboard
        Write-Host 'Dashboard: http://127.0.0.1:8502'
        Write-Host 'API docs: http://127.0.0.1:8002/docs'
        Write-Host 'Prefect: http://127.0.0.1:4201'
        Write-Host 'RabbitMQ: http://127.0.0.1:15673 (pitchpulse / pitchpulse_local_demo)'
    }
    'Stop' { Compose down }
    'Run' { Compose run --rm pipeline run; Compose run --rm pipeline verify }
    'Test' { Compose run --rm --entrypoint python pipeline -m pytest tests/test_platform.py tests/test_pipeline.py tests/test_remaining_experiments.py -v }
    'Stream' { Compose run --rm pipeline stream }
    'Status' { Compose ps }
}
