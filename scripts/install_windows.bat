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

REM Firefox / Floorp manifest location
set "FF_MANIFEST_DIR=%APPDATA%\\Mozilla\\NativeMessagingHosts"
if not exist "%FF_MANIFEST_DIR%" mkdir "%FF_MANIFEST_DIR%"

REM Copy manifest verbatim (path is relative host.bat, resolved next to the manifest file)
copy /Y "%MANIFEST%" "%FF_MANIFEST_DIR%\\com.kajusmar.ytdlp_downloader.json" >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to install manifest
    pause
    exit /b 1
)

echo Manifest installed to: %FF_MANIFEST_DIR%\\com.kajusmar.ytdlp_downloader.json

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
