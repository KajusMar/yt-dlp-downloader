@echo off
REM Native messaging wrapper for yt-dlp-downloader.
REM Firefox launches this .bat from an unknown CWD, so first cd to the
REM directory the .bat lives in, then exec host.py with the system python.
REM stdin/stdout are inherited, so the native-messaging pipe works.
cd /d "%~dp0"
"%~dp0host.py" %*
