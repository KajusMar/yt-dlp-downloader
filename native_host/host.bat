@echo off
REM Native messaging wrapper for yt-dlp-downloader.
REM Firefox launches this .bat; it execs host.py with the system python.
REM stdin/stdout are inherited, so the native-messaging pipe works.
"%~dp0host.py" %*
