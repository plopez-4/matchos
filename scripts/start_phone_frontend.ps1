param([Parameter(Mandatory=$true)][string]$Address)
$ErrorActionPreference = 'Stop'
$phoneIp = $null
if (-not [System.Net.IPAddress]::TryParse($Address, [ref]$phoneIp) -or $phoneIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { throw 'Use your computer''s private IPv4 address from ipconfig.' }
$phoneBytes = $phoneIp.GetAddressBytes()
if (-not ($phoneBytes[0] -eq 10 -or ($phoneBytes[0] -eq 172 -and $phoneBytes[1] -ge 16 -and $phoneBytes[1] -le 31) -or ($phoneBytes[0] -eq 192 -and $phoneBytes[1] -eq 168))) { throw 'Use a private network address.' }
$previousPhoneAddress = $env:MATCHOS_PHONE_ADDRESS
try {
    $env:MATCHOS_PHONE_ADDRESS = $Address
    Push-Location -LiteralPath (Join-Path (Split-Path -Parent $PSScriptRoot) 'frontend')
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
        Write-Host "Open on your phone: http://${Address}:5176/testing.html"
        Write-Host 'Keep this window open. Use the same private network; eduroam may isolate devices.'
        & npm.cmd run preview -- --host $Address --port 5176 --strictPort
    } finally { Pop-Location }
} finally { $env:MATCHOS_PHONE_ADDRESS = $previousPhoneAddress }
