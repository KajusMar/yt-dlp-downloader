@echo off
REM yt-dlp Downloader - Windows Installer
REM Installs native messaging host for Firefox / Floorp

echo ==========================================
echo yt-dlp Video Downloader - Installer
echo ==========================================
echo.

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
set "HOST_DIR=%SCRIPT_DIR%..\\native_host"
set "MANIFEST=%HOST_DIR%\\com.kajusmar.ytdlp_downloader.json"

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org or Microsoft Store
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] Checking yt-dlp installation...
python -m yt_dlp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo yt-dlp not found. Installing via pip...
    pip install -U yt-dlp
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install yt-dlp
        pause
        exit /b 1
    )
)
python -m yt_dlp --version

echo.
echo [3/4] Checking ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ffmpeg not found in PATH
    echo Video merging may not work without ffmpeg
    echo Install from https://ffmpeg.org/download.html
) else (
    echo ffmpeg found:
    ffmpeg -version | findstr /R /C:"ffmpeg version"
)

echo.
echo [4/4] Installing native messaging manifest...

REM Firefox/Floorp manifest file location (also written for non-Windows parity
REM and for the Linux/Mac lookup path which resolves ...Mozilla\NativeMessagingHosts).
set "FF_MANIFEST_DIR=%APPDATA%\Mozilla\NativeMessagingHosts"
if not exist "%FF_MANIFEST_DIR%" mkdir "%FF_MANIFEST_DIR%"

REM Firefox launches native hosts with the BROWSER's working directory
REM (e.g. C:\Program Files\Ablaze Floorp\), NOT the manifest's folder. So the
REM "path" MUST be absolute, or connectNative fails with "Native host not
REM available". We rewrite the manifest's path to the absolute host.exe here.
set "HOST_EXE_ABS=%~dp0..\native_host\host.exe"
REM Normalize to a clean absolute path
for %%I in ("%HOST_EXE_ABS%") do set "HOST_EXE_ABS=%%~fI"
set "MANIFEST_DST=%FF_MANIFEST_DIR%\com.kajusmar.ytdlp_downloader.json"

powershell -NoProfile -Command ^
  "$json=Get-Content '%MANIFEST%' -Raw | ConvertFrom-Json;" ^
  "$json.path='%HOST_EXE_ABS%';" ^
  "$out=$json | ConvertTo-Json -Compress;" ^
  "Set-Content -Encoding ASCII '%MANIFEST_DST%' $out"

REM === CRITICAL (Windows only) ===
REM On Windows, Firefox/Floorp does NOT scan the NativeMessagingHosts folder.
REM It reads the REGISTRY instead:
REM   HKCU\Software\Mozilla\NativeMessagingHosts\<name>  =  <path to manifest JSON>
REM (Hardcoded "Software\Mozilla" in modules/NativeManifests.sys.mjs, even for
REM Floorp.) Without this registry entry, connectNative can never find the host.
powershell -NoProfile -Command ^
  "New-Item -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Force | Out-Null;" ^
  "New-ItemProperty -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Name 'com.kajusmar.ytdlp_downloader' -Value '%MANIFEST_DST%' -PropertyType String -Force | Out-Null;" ^
  "Write-Host 'Registry key set: HKCU:\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader = %MANIFEST_DST%'"

if %errorlevel% neq 0 (
    echo ERROR: Failed to install manifest
    pause
    exit /b 1
)

echo Manifest installed:
echo   file : %MANIFEST_DST%
echo   host : %HOST_EXE_ABS%
echo   registry: HKCU\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Drag the yt-dlp-downloader.xpi into about:addons (or install from GitHub releases)
echo 2. Restart Firefox / Floorp
echo 3. Click the extension icon to test
echo.
echo Download directory: %USERPROFILE%\\Videos\\yt-dlp
echo.
pause
