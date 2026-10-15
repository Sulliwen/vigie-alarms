# Builds dist\Vigie-Setup-<version>.exe, an installer that needs no Python on the target PC.
# Requires Inno Setup 6 (winget install JRSoftware.InnoSetup).
$ErrorActionPreference = 'Stop'
$dir = $PSScriptRoot
$python = Join-Path $dir '.venv\Scripts\python.exe'
& $python -m pip install --quiet --disable-pip-version-check pyinstaller
$icon = Join-Path $dir 'build\Vigie.ico'
New-Item -ItemType Directory -Force (Join-Path $dir 'build') | Out-Null
Set-Location $dir
& $python -c "import vigie as c; c.make_icon().save(r'$icon', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 256)])"
& $python -m PyInstaller --noconfirm --onedir --windowed --name Vigie --icon $icon --add-data "$(Join-Path $dir 'assets\vigie.png');assets" `
    --collect-submodules caldav --collect-submodules icalendar --collect-submodules icalendar_searcher `
    --collect-submodules recurring_ical_events --collect-submodules x_wr_timezone --collect-submodules keyring --collect-submodules slack_sdk `
    --collect-data icalendar --collect-data tzdata `
    --distpath (Join-Path $dir 'dist') --workpath (Join-Path $dir 'build') --specpath (Join-Path $dir 'build') `
    (Join-Path $dir 'vigie.py')

$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw 'Inno Setup 6 not found.' }
$version = & $python -c "import vigie; print(vigie.__version__)"
& $iscc /Q "/DAppVersion=$version" (Join-Path $dir 'installer.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed.' }

Get-ChildItem (Join-Path $dir 'dist\Vigie-Setup-*.exe') | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    Set-Content -Path "$($_.FullName).sha256" -Value "$hash  $($_.Name)" -Encoding ascii
    Write-Host "$($_.Name)  SHA-256: $hash"
}
