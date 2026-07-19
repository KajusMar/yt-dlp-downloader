# Documentation

This folder contains additional documentation and assets.

## Screenshots

Add screenshots of the extension here:
- `popup-detected.png` — Detected videos tab
- `popup-manual.png` — Manual URL tab with format selection
- `popup-downloads.png` — Active downloads with progress
- `context-menu.png` — Right-click context menu
- `video-page-buttons.png` — Download buttons on video pages

## Architecture

```
extension/                    # Firefox WebExtension (MV2)
├── background/               # Native messaging client
├── content/                  # Video detection + download buttons
├── popup/                    # 3-tab UI (Detected/Manual/Downloads)
└── manifest.json

native_host/                  # Python native messaging host
├── host.py                   # Communicates with yt-dlp via stdin/stdout
└── com.kajusmar.ytdlp_downloader.json  # Firefox manifest

scripts/                      # Installers
├── install_windows.bat
└── install_linux.sh
```

## Native Messaging Protocol

**Extension → Host (stdin):**
```json
{"id": 1, "command": "health_check"}
{"id": 2, "command": "get_info", "url": "https://youtube.com/watch?v=..."}
{"id": 3, "command": "download", "url": "...", "options": {"format": "best[height<=1080]"}}
```

**Host → Extension (stdout):**
```json
{"id": 1, "result": {"status": "ok", "yt_dlp_version": "2026.07.04", "ffmpeg_available": true}}
{"id": 2, "result": {"title": "...", "duration": 213, "thumbnail": "...", ...}}
{"id": 3, "progress": {"percent": 45.2, "speed": "1.2MiB/s", "eta": "00:03", "status": "downloading"}}
{"id": 3, "result": {"status": "completed"}}
```

## Message Format

All messages are length-prefixed (4 bytes, little-endian uint32) + JSON.