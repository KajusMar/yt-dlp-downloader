@echo off
REM Native messaging wrapper for yt-dlp-downloader.
REM
REM Firefox/Floorp launches this .bat from an unknown CWD with stdio wired to
REM the native-messaging pipe. We must NOT rely on the Windows .py file
REM association (it can fail / need a console when spawned by the browser),
REM so we invoke python EXPLICITLY with the absolute path to host.py.
REM
REM We also pick a python that actually has yt-dlp installed, preferring the
REM plain `python`/`py` on PATH (the user's real python) over sys.executable.

setlocal EnableExtensions

REM Directory this .bat lives in (native_host/)
set "HERE=%~dp0"
set "HOSTPY=%HERE%host.py"

REM Find a python that can import yt_dlp (prefer python, then py, then uv path)
set "PYTHON_EXE="
for %%P in (python py) do (
    if not defined PYTHON_EXE (
        "%%P" -c "import yt_dlp" >nul 2>&1 && set "PYTHON_EXE=%%P"
    )
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\uv\python\cpython-3.11-windows-x86_64-none\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\uv\python\cpython-3.11-windows-x86_64-none\python.exe"
    )
)
if not defined PYTHON_EXE (
    set "PYTHON_EXE=C:\Users\Kay\AppData\Roaming\uv\python\cpython-3.11-windows-x86_64-none\python.exe"
)

"%PYTHON_EXE%" "%HOSTPY%" %*
endlocal
