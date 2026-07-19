# yt-dlp Video Downloader

A Firefox WebExtension that lets you download videos from YouTube and 1000+ other sites using **yt-dlp** — no quality limits, no ads, completely open source.

## Features

- **Downloads from 1000+ sites** (YouTube, Vimeo, Twitch, Twitter/X, Reddit, TikTok, Instagram, Facebook, etc.)
- **No quality limits** — download up to 4K/8K where available
- **Audio extraction** — save as MP3, M4A, Opus, etc.
- **Auto-detects videos** on pages — adds download buttons to embedded videos
- **Context menu integration** — right-click any link/video to download
- **Keyboard shortcut** — `Alt+D` to download from current page
- **Progress tracking** — real-time download progress in popup
- **Open source** — MIT licensed, no tracking, no analytics

## Installation

### Quick Install (Windows)

1. **Install prerequisites:**
   - [Python 3.8+](https://python.org/downloads)
   - [yt-dlp](https://github.com/yt-dlp/yt-dlp) — `pip install -U yt-dlp`
   - [FFmpeg](https://ffmpeg.org/download.html) — for video merging (optional but recommended)

2. **Run the installer:**
   ```cmd
   scripts\install_windows.bat
   ```

3. **Install the extension:**
   - Open Firefox → `about:addons`
   - Click the gear icon → "Install Add-on From File"
   - Select `yt-dlp-downloader.xpi`
   - Restart Firefox

4. **Done!** Click the extension icon to use it.

### Manual Install (Any Platform)

1. Copy `native_host/com.kajusmar.ytdlp_downloader.json` to Firefox's native messaging hosts directory:
   - **Windows:** `%APPDATA%\Mozilla\NativeMessagingHosts\`
   - **macOS:** `~/Library/Application Support/Mozilla/NativeMessagingHosts/`
   - **Linux:** `~/.mozilla/native-messaging-hosts/`

2. Edit the manifest to point to the correct `host.py` path

3. Install the `.xpi` file in Firefox

## Usage

### From Extension Popup
1. Navigate to any video page
2. Click the extension icon
3. **Detected** tab shows videos found on the page
4. **Manual URL** tab lets you paste any URL
5. Choose format and click **Download**

### Context Menu
Right-click any video, link, or page → "Download video with yt-dlp"

### Keyboard Shortcut
Press `Alt+D` on any video page to start downloading

## Supported Sites

yt-dlp supports 1000+ sites including:
- YouTube (including Shorts, Live, Playlists)
- Vimeo
- Twitch (VODs, clips)
- Twitter / X
- Reddit (v.redd.it, gfycat, etc.)
- TikTok
- Instagram (Reels, posts, stories)
- Facebook
- Bilibili
- SoundCloud
- Bandcamp
- And many more — [full list](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Format Options

| Format | Description |
|--------|-------------|
| Best quality (≤1080p) | Best video+audio, capped at 1080p |
| Best available | Best quality regardless of resolution |
| 720p | 720p video + audio |
| 480p | 480p video + audio |
| Audio only (MP3) | Extract audio as MP3 |

## Download Location

Default: `~/Videos/yt-dlp/` (Windows: `%USERPROFILE%\Videos\yt-dlp\`)

## Development

### Project Structure
```
├── extension/              # Firefox WebExtension (MV2)
│   ├── background/         # Background script (native messaging)
│   ├── content/            # Content script (video detection)
│   ├── popup/              # Popup UI
│   └── manifest.json
├── native_host/
│   ├── host.py             # Native messaging host (Python)
│   └── com.kajusmar.ytdlp_downloader.json  # Firefox manifest
├── scripts/
│   └── install_windows.bat # Windows installer
└── yt-dlp-downloader.xpi   # Packaged extension
```

### Building
```bash
cd extension
zip -r ../yt-dlp-downloader.xpi .
```

## How It Works

1. **Extension** (Firefox WebExtension) provides UI and detects videos
2. **Native Messaging Host** (Python) communicates with extension via stdin/stdout
3. **yt-dlp** does the actual downloading — runs as a subprocess
4. **FFmpeg** merges video+audio streams

This architecture is required because browser extensions cannot spawn processes directly.

## Privacy

- **No tracking** — no analytics, no telemetry, no external connections except to download videos
- **No accounts** — works without login (uses cookies from your browser if available)
- **Open source** — MIT license, fully auditable

## Troubleshooting

### "Native host not connected"
- Run `scripts/install_windows.bat` again
- Check `%APPDATA%\Mozilla\NativeMessagingHosts\com.kajusmar.ytdlp_downloader.json` exists
- Restart Firefox completely

### "yt-dlp not found"
- Ensure `yt-dlp` is in your PATH: `yt-dlp --version`
- Or install: `pip install -U yt-dlp`

### Downloads fail / no ffmpeg
- Install FFmpeg and add to PATH
- Without FFmpeg, yt-dlp can't merge separate video/audio streams

### Extension doesn't detect videos
- Some sites load videos dynamically — click "Scan Again" in popup
- Try the Manual URL tab with the direct video URL

## License

MIT License — see [LICENSE](LICENSE) for details.

## Credits

- **yt-dlp** — the amazing downloader library
- **FFmpeg** — video/audio processing
- **Firefox WebExtensions API** — extension platform

---

**Repository:** https://github.com/KajusMar/yt-dlp-downloader