@echo off
REM DISABLED. This watchdog previously auto-shut-down the device after upload.
REM Neutralized on 2026-07-20 so it can never fire a surprise shutdown.
REM The GitHub release upload is already complete; no action needed.
echo watchdog disabled - no-op
exit /b 0
