# Installing yt-dlp Video Downloader (Windows + Floorp/Firefox)

Downloads need **two** parts: the browser extension (`.xpi`) **and** the native
host (a small local program that runs yt-dlp). Installing only the extension will
let it *detect* videos but **not download** them.

## Easiest: full bundle

1. Download **`yt-dlp-downloader-windows.zip`** from the
   [latest release](https://github.com/KajusMar/yt-dlp-downloader/releases/latest).
2. **Extract the whole zip** to a permanent folder (e.g. `C:\Tools\yt-dlp-downloader`).
   Do **not** run the installer straight from inside the zip / Downloads — extract first.
3. Run `scripts\install_windows.bat` (double-click). It:
   - checks Python / yt-dlp / ffmpeg,
   - registers the native host in the registry
     (`HKCU\Software\Mozilla\NativeMessagingHosts`),
   - points it at the bundled `native_host\host.exe`.
4. In Floorp/Firefox, open `about:addons` → gear → **Install Add-on From File** →
   pick `yt-dlp-downloader.xpi` (or drag it onto the page).
5. **Restart Floorp/Firefox.**
6. Click the extension icon → it should show `yt-dlp <version> • ffmpeg`.

## Requirements

- **Python 3.9+** on PATH (the host launches `python -m yt_dlp`). If you use the
  bundled `host.exe`, it still calls your system Python for yt-dlp, so Python +
  yt-dlp must be installed.
- **ffmpeg** on PATH (for merging video+audio and MP3 extraction).

## Troubleshooting

- **"Not connected" in the popup** → the native host isn't registered. Re-run
  `scripts\install_windows.bat` from the *extracted* folder, then restart the browser.
- **Detects videos but download does nothing** → same cause: native host missing
  or the manifest path is wrong. Re-run the installer.
- **Moved the folder?** The registry points at the old `host.exe` path. Re-run the
  installer from the new location.

## Uninstall

Run `scripts\uninstall_windows.bat`, then remove the extension from `about:addons`.
