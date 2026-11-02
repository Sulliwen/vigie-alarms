# Stops the alarm and removes it from logon. The folder, the settings and the saved password are left in place.
$dir = $PSScriptRoot
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'Vigie' -ErrorAction SilentlyContinue
# The watchdog first, or it would start Vigie again after it is stopped below.
schtasks /Delete /TN 'Vigie Watchdog' /F 2>$null | Out-Null
Get-CimInstance Win32_Process |
    Where-Object { ($_.Name -eq 'pythonw.exe' -and $_.CommandLine -like "*$dir*") -or $_.Name -eq 'Vigie.exe' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Write-Host 'Vigie stopped and removed from logon.'
Write-Host 'Saved password: Credential Manager > Windows Credentials > vigie:<id>.'
