# Development: stops any running Vigie and starts the one of these sources, which restarts by itself
# whenever vigie.py or texts.py change. No build, no installation.
$ErrorActionPreference = 'Stop'
$dir = $PSScriptRoot
$pythonw = Join-Path $dir '.venv\Scripts\pythonw.exe'

if (-not (Test-Path $pythonw)) {
    py -3 -m venv (Join-Path $dir '.venv')
    & (Join-Path $dir '.venv\Scripts\python.exe') -m pip install --quiet --disable-pip-version-check -r (Join-Path $dir 'requirements.txt')
}

Get-CimInstance Win32_Process |
    Where-Object { $_.Name -eq 'Vigie.exe' -or ($_.Name -eq 'pythonw.exe' -and $_.CommandLine -like '*vigie.py*') } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

Start-Process -FilePath $pythonw -ArgumentList ('"{0}" --dev' -f (Join-Path $dir 'vigie.py')) -WorkingDirectory $dir
Write-Host 'Vigie (dev) started from the sources.'
