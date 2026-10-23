param(
    [switch]$Speech,
    [switch]$AI,
    [int]$ReplaceServerPid = 0,
    [string]$ModelEndpoint = 'https://matchos-ai.services.ai.azure.com/openai/v1',
    [string]$ModelDeployment = 'matchos-explainer',
    [ValidatePattern('^[a-z][a-z0-9]{2,30}$')][string]$SpeechRegion = 'canadacentral'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create the MatchOS virtual environment first.' }
$previousMode = $env:MATCHOS_SPEECH_MODE
$previousRegion = $env:AZURE_SPEECH_REGION
$previousKey = $env:AZURE_SPEECH_KEY
$previousAiMode = $env:MATCHOS_AI_MODE
$previousModelEndpoint = $env:AZURE_OPENAI_BASE_URL
$previousDeployment = $env:AZURE_OPENAI_DEPLOYMENT
$previousModelKey = $env:AZURE_OPENAI_API_KEY

function Read-PrivateKey([string]$Prompt) {
    $secureValue = Read-Host $Prompt -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secureValue.Dispose() }
}

try {
    if ($AI) {
        $parsedEndpoint = [Uri]$ModelEndpoint
        if ($parsedEndpoint.Scheme -ne 'https' -or $parsedEndpoint.Host -notmatch '\.(openai|services\.ai)\.azure\.com$' -or $parsedEndpoint.AbsolutePath.TrimEnd('/') -ne '/openai/v1' -or $parsedEndpoint.Query -or $parsedEndpoint.Fragment -or $parsedEndpoint.UserInfo -or -not $parsedEndpoint.IsDefaultPort) {
            throw 'Use the Azure model resource endpoint ending in /openai/v1, not the project endpoint.'
        }
        $env:AZURE_OPENAI_API_KEY = Read-PrivateKey 'Paste the Foundry model resource key (hidden; not saved)'
        $env:AZURE_OPENAI_BASE_URL = $ModelEndpoint.TrimEnd('/')
        $env:AZURE_OPENAI_DEPLOYMENT = $ModelDeployment
        $env:MATCHOS_AI_MODE = 'azure'
    }
    if ($Speech) {
        $env:AZURE_SPEECH_KEY = Read-PrivateKey 'Paste the Azure Speech key (hidden; not saved)'
        $env:AZURE_SPEECH_REGION = $SpeechRegion
        $env:MATCHOS_SPEECH_MODE = 'azure'
    }
    # Keep an existing local demo available until private credential entry completes.
    if ($ReplaceServerPid -gt 0) {
        $existingServer = Get-CimInstance Win32_Process -Filter "ProcessId=$ReplaceServerPid" -ErrorAction SilentlyContinue
        if ($existingServer) {
            if (-not $existingServer.CommandLine.Contains($pythonPath) -or $existingServer.CommandLine -notmatch 'uvicorn\s+app\.main:app') {
                throw 'The requested process is not this checkout''s MatchOS backend. It has not been stopped.'
            }
            & taskkill.exe /PID $ReplaceServerPid /T /F | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'The previous MatchOS backend could not be stopped.' }
        }
    }
    # Import this checkout even if the virtual environment was installed from another folder.
    Push-Location -LiteralPath (Join-Path $projectRoot 'backend')
    try { & $pythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload }
    finally { Pop-Location }
}
finally {
    $env:MATCHOS_SPEECH_MODE = $previousMode
    $env:AZURE_SPEECH_REGION = $previousRegion
    $env:AZURE_SPEECH_KEY = $previousKey
    $env:MATCHOS_AI_MODE = $previousAiMode
    $env:AZURE_OPENAI_BASE_URL = $previousModelEndpoint
    $env:AZURE_OPENAI_DEPLOYMENT = $previousDeployment
    $env:AZURE_OPENAI_API_KEY = $previousModelKey
}
