@echo off
REM ============================================================
REM yt-dlp Video Downloader - Windows Installer (robust)
REM Registers the native messaging host for Firefox / Floorp.
REM Safe to run from ANY working directory (double-click, Downloads, etc).
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion

echo ==========================================
echo yt-dlp Video Downloader - Installer
echo ==========================================
echo.

REM --- Resolve repo paths from THIS script's location (never the CWD) ---
set "SCRIPT_DIR=%~dp0"
REM Repo root is the parent of scripts\
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "HOST_DIR=%REPO_ROOT%\native_host"
set "MANIFEST_SRC=%HOST_DIR%\com.kajusmar.ytdlp_downloader.json"
set "HOST_EXE=%HOST_DIR%\host.exe"
set "HOST_PY=%HOST_DIR%\host.py"

echo Repo root : %REPO_ROOT%
echo Host dir  : %HOST_DIR%
echo.

REM --- Sanity: the source manifest MUST exist, or we abort (never wipe target) ---
if not exist "%MANIFEST_SRC%" (
    echo ERROR: Source manifest not found at:
    echo   %MANIFEST_SRC%
    echo.
    echo You are probably running this .bat outside the extracted project folder.
    echo Extract the full release zip and run scripts\install_windows.bat from there.
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org or the Microsoft Store
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
    echo WARNING: ffmpeg not found in PATH - video/audio merging may fail
    echo Install from https://ffmpeg.org/download.html
) else (
    echo ffmpeg found:
    ffmpeg -version | findstr /R /C:"ffmpeg version"
)

echo.
echo [4/4] Installing native messaging manifest...

REM --- Decide which host to launch: prefer bundled host.exe, else host.bat ---
if exist "%HOST_EXE%" (
    set "HOST_PATH=%HOST_EXE%"
) else (
    if exist "%HOST_DIR%\host.bat" (
        set "HOST_PATH=%HOST_DIR%\host.bat"
    ) else (
        echo ERROR: Neither host.exe nor host.bat found in %HOST_DIR%
        pause
        exit /b 1
    )
)
echo Native host binary: !HOST_PATH!

REM --- Manifest destination (Mozilla dir; Firefox/Floorp resolves here) ---
set "FF_MANIFEST_DIR=%APPDATA%\Mozilla\NativeMessagingHosts"
if not exist "%FF_MANIFEST_DIR%" mkdir "%FF_MANIFEST_DIR%"
set "MANIFEST_DST=%FF_MANIFEST_DIR%\com.kajusmar.ytdlp_downloader.json"

REM --- Write the manifest with an ABSOLUTE host path (guarded so a failed read
REM     can never truncate the destination). Pass values via env vars to avoid
REM     delayed-expansion / backslash issues inside PowerShell. ---
set "HOST_PATH_ENV=!HOST_PATH!"
set "MANIFEST_SRC_ENV=%MANIFEST_SRC%"
set "MANIFEST_DST_ENV=%MANIFEST_DST%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$src=$env:MANIFEST_SRC_ENV;" ^
  "if(-not (Test-Path $src)){Write-Error 'source manifest missing'; exit 1};" ^
  "$json=Get-Content $src -Raw | ConvertFrom-Json;" ^
  "$json.path=$env:HOST_PATH_ENV;" ^
  "$out=$json | ConvertTo-Json -Compress;" ^
  "if([string]::IsNullOrWhiteSpace($out)){Write-Error 'empty manifest, aborting'; exit 1};" ^
  "Set-Content -Encoding ASCII $env:MANIFEST_DST_ENV $out"
if %errorlevel% neq 0 (
    echo ERROR: Failed to write manifest
    pause
    exit /b 1
)

REM === CRITICAL (Windows) ===
REM On Windows, Firefox/Floorp does NOT scan the NativeMessagingHosts folder.
REM It reads the REGISTRY: HKCU\Software\Mozilla\NativeMessagingHosts\<name> = <manifest path>
REM (Hardcoded "Software\Mozilla" in modules\NativeManifests.sys.mjs, even on Floorp.)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "New-Item -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Force | Out-Null;" ^
  "New-ItemProperty -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Name 'com.kajusmar.ytdlp_downloader' -Value $env:MANIFEST_DST_ENV -PropertyType String -Force | Out-Null;" ^
  "Write-Host ('Registry set: HKCU\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader = ' + $env:MANIFEST_DST_ENV)"
if %errorlevel% neq 0 (
    echo ERROR: Failed to write registry key
    pause
    exit /b 1
)

echo.
echo Manifest installed:
echo   file    : %MANIFEST_DST%
echo   host    : !HOST_PATH!
echo   registry: HKCU\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Install yt-dlp-downloader.xpi (drag into about:addons, or from GitHub releases)
echo 2. Restart Firefox / Floorp
echo 3. Click the extension icon to test
echo.
echo Download directory: %USERPROFILE%\Videos\yt-dlp
echo.
pause
endlocal
