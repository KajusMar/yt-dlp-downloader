powershell -NoProfile -Command "
Write-Host '=== HKCU Mozilla NativeMessagingHosts ==='
$key = 'HKCU:\Software\Mozilla\NativeMessagingHosts'
if (Test-Path $key) {
    Get-ChildItem $key | ForEach-Object {
        $val = (Get-ItemProperty $_.PSPath).'(default)'
        Write-Host \"$($_.PSChildName) -> $val\"
    }
} else {
    Write-Host 'KEY MISSING'
}
Write-Host '=== HKLM Mozilla NativeMessagingHosts ==='
$key2 = 'HKLM:\Software\Mozilla\NativeMessagingHosts'
if (Test-Path $key2) {
    Get-ChildItem $key2 | ForEach-Object {
        $val = (Get-ItemProperty $_.PSPath).'(default)'
        Write-Host \"$($_.PSChildName) -> $val\"
    }
} else {
    Write-Host 'KEY MISSING'
}
Write-Host '=== AppData file ==='
$f = 'C:\Users\Kay\AppData\Roaming\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader.json'
if (Test-Path $f) { Write-Host 'EXISTS'; Get-Content $f } else { Write-Host 'MISSING' }
"