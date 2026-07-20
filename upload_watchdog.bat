@echo off
REM Auto-resume watchdog for yt-dlp-downloader release upload + shutdown.
REM Retries the GitHub asset upload until it succeeds (GitHub was 502/503),
REM then shuts down the device. Runs detached so it survives the chat session.
setlocal
set "REPO=KajusMar/yt-dlp-downloader"
set "TAG=v1.0.0"
set "XPI1=C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
set "XPI2=C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader-v1.0.0.xpi"
set "LOG=C:\Users\Kay\yt-dlp-downloader\upload_watchdog.log"
set "PATH=C:\Program Files\GitHub CLI;%PATH%"

echo %DATE% %TIME% - watchdog started >> "%LOG%"

:loop
gh release view %TAG% --json assets >nul 2>&1
if errorlevel 1 (
    echo %DATE% %TIME% - release missing, recreating >> "%LOG%"
    gh release create %TAG% "%XPI1%" "%XPI2%" --title "%TAG%" --notes "yt-dlp Video Downloader - Firefox/Floorp extension. Fixes applied; native host verified end-to-end." >> "%LOG%" 2>&1
)
echo %DATE% %TIME% - attempting upload >> "%LOG%"
gh release upload %TAG% "%XPI1%" "%XPI2%" --clobber >> "%LOG%" 2>&1
if errorlevel 1 (
    echo %DATE% %TIME% - upload failed, retry in 60s >> "%LOG%"
    timeout /t 60 >nul
    goto loop
)
echo %DATE% %TIME% - UPLOAD SUCCESS >> "%LOG%"
echo %DATE% %TIME% - shutting down device >> "%LOG%"
REM Give a moment, then shut down
timeout /t 10 >nul
shutdown /s /t 0
endlocal
