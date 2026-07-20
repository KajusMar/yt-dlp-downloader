@echo off
REM ============================================================
REM yt-dlp Video Downloader - Windows Installer (robust v2)
REM Registers the native messaging host for Firefox / Floorp.
REM Safe to run from ANY working directory.
REM ============================================================
setlocal EnableExtensions EnableDelayedExpansion

REM Always keep the window open on error so the user can read it.
if not "%~1"=="/nokeep" (
    REM Re-launch self so that any early failure pauses instead of closing.
    cmd /k "%~f0" /nokeep %*
    exit /b
)

echo ==========================================
echo yt-dlp Video Downloader - Installer
echo ==========================================
echo.

REM --- Resolve repo paths from THIS script's location ---
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "HOST_DIR=%REPO_ROOT%\native_host"
set "MANIFEST_SRC=%HOST_DIR%\com.kajusmar.ytdlp_downloader.json"
set "HOST_EXE=%HOST_DIR%\host.exe"

echo Repo root : %REPO_ROOT%
echo Host dir  : %HOST_DIR%
echo.

REM --- Sanity: source manifest must exist ---
if not exist "%MANIFEST_SRC%" (
    echo ERROR: Source manifest not found at:
    echo   %MANIFEST_SRC%
    echo.
    echo Make sure you extracted the FULL release zip and are running
    echo scripts\install_windows.bat from inside it.
    goto :done
)

REM --- Pick the host binary (prefer bundled host.exe) ---
if exist "%HOST_EXE%" (
    set "HOST_PATH=%HOST_EXE%"
) else (
    echo ERROR: host.exe not found in %HOST_DIR%
    echo The release zip must contain native_host\host.exe
    goto :done
)
echo Native host binary: !HOST_PATH!
echo.

REM --- Write manifest (absolute host path) ---
set "FF_MANIFEST_DIR=%APPDATA%\Mozilla\NativeMessagingHosts"
if not exist "%FF_MANIFEST_DIR%" mkdir "%FF_MANIFEST_DIR%"
set "MANIFEST_DST=%FF_MANIFEST_DIR%\com.kajusmar.ytdlp_downloader.json"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$src='%MANIFEST_SRC%';" ^
  "if(-not (Test-Path $src)){Write-Error 'source manifest missing'; exit 1};" ^
  "$json=Get-Content $src -Raw | ConvertFrom-Json;" ^
  "$json.path='%HOST_PATH%';" ^
  "$out=$json | ConvertTo-Json -Compress;" ^
  "if([string]::IsNullOrWhiteSpace($out)){Write-Error 'empty manifest'; exit 1};" ^
  "Set-Content -Encoding ASCII '%MANIFEST_DST%' $out"
if errorlevel 1 (
    echo ERROR: Failed to write manifest to %MANIFEST_DST%
    goto :done
)
echo Manifest written: %MANIFEST_DST%

REM --- Registry SUBKEY (Firefox requires a subkey, not a flat value) ---
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "New-Item -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts' -Force | Out-Null;" ^
  "New-Item -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader' -Force | Out-Null;" ^
  "Set-ItemProperty -Path 'HKCU:\Software\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader' -Name '(default)' -Value '%MANIFEST_DST%' -Force | Out-Null;" ^
  "Write-Host ('Registry set: ' + '%MANIFEST_DST%')"
if errorlevel 1 (
    echo ERROR: Failed to write registry key
    goto :done
)

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Install yt-dlp-downloader.xpi in Firefox/Floorp (about:addons - install from file)
echo 2. Restart the browser
echo 3. Click the extension icon - it should show "Connected"
echo.

:done
echo.
echo Press any key to close...
pause >nul
endlocal
