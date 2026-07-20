@echo off
REM Uninstall the yt-dlp-downloader native messaging host.
setlocal EnableExtensions
echo Removing native messaging host registration...

set "MANIFEST_DST=%APPDATA%\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader.json"
if exist "%MANIFEST_DST%" del /f /q "%MANIFEST_DST%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Remove-ItemProperty -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Name 'com.kajusmar.ytdlp_downloader' -ErrorAction SilentlyContinue;" ^
  "Write-Host 'Registry key removed (if present).'"

echo Done. Also remove the extension from about:addons in Floorp/Firefox.
pause
endlocal
