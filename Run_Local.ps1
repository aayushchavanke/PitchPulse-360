param([ValidateSet('Pipeline','Dashboard','API','Tests')][string]$Mode='Pipeline')
$mappedAction = if ($Mode -eq 'Pipeline') { 'Run' } elseif ($Mode -eq 'Tests') { 'Test' } else { 'Start' }
& (Join-Path $PSScriptRoot 'Start.ps1') -Action $mappedAction
exit $LASTEXITCODE
