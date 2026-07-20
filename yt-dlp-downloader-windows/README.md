# yt-dlp Video Downloader

[![Firefox Add-on](https://img.shields.io/badge/Firefox-Add--on-orange?logo=firefox-browser&logoColor=white)](https://addons.mozilla.org/firefox/addon/yt-dlp-video-downloader/)
[![GitHub Release](https://img.shields.io/github/v/release/KajusMar/yt-dlp-downloader?logo=github)](https://github.com/KajusMar/yt-dlp-downloader/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-2026.07-red?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)

**Download videos from YouTube and 1000+ sites directly in Firefox — no quality limits, no ads, open source.**

![Screenshot](docs/screenshot.png)

## ✨ Features

- **1000+ sites supported** via [yt-dlp](https://github.com/yt-dlp/yt-dlp) (YouTube, Vimeo, Twitch, Twitter/X, TikTok, Instagram, Reddit, etc.)
- **Auto-detects videos** on pages — adds download buttons on hover
- **Context menu** → "Download with yt-dlp" on any link/video
- **Format selection**: Best (≤1080p), Best Available, 720p, 480p, Audio Only (MP3)
- **Real-time progress** in popup
- **Keyboard shortcut**: `Alt+D`
- **No external servers** — runs locally via native messaging
- **Privacy-focused** — no tracking, no accounts, no data collection

## 🚀 Quick Install

### Option 1: One-click Auto-Install (Recommended, Windows)

[![Install from GitHub Releases](https://img.shields.io/badge/📥_Install-Latest_Release-orange?style=for-the-badge&logo=github)](https://github.com/KajusMar/yt-dlp-downloader/releases/latest)

1. Click the button above → download **`yt-dlp-downloader-windows.zip`** (not just the `.xpi`)
2. Extract the zip → run **`scripts\install_windows.bat`** as Administrator
3. Open Firefox → `about:addons` → Gear icon → **Install Add-on From File**
4. Select the extracted `yt-dlp-downloader.xpi` → **Restart Firefox**
5. Done! 🎉

*The auto-installer registers the native host, checks/installs yt-dlp + ffmpeg, and configures everything.*

### Option 2: Manual Install (Any OS)

[![Install from GitHub Releases](https://img.shields.io/badge/📥_Install-Latest_Release-orange?style=for-the-badge&logo=github)](https://github.com/KajusMar/yt-dlp-downloader/releases/latest)

1. Click the button above → download `yt-dlp-downloader.xpi`
2. Open Firefox → `about:addons` → Gear icon → **Install Add-on From File**
3. Select the `.xpi` → **Restart Firefox**
4. Done! 🎉

*Requires yt-dlp + ffmpeg in PATH. See requirements below.*

### Option 2: From Source

```bash
# Prerequisites
winget install yt-dlp ffmpeg python  # Windows
# OR: brew install yt-dlp ffmpeg python  # macOS
# OR: sudo apt install yt-dlp ffmpeg python3  # Linux

# Clone & build
git clone https://github.com/KajusMar/yt-dlp-downloader
cd yt-dlp-downloader
./scripts/build.sh  # Creates .xpi in dist/
```

### Option 3: Automated Install (Windows)

```cmd
git clone https://github.com/KajusMar/yt-dlp-downloader
cd yt-dlp-downloader
scripts\install_windows.bat
```

This installs:
- ✅ Native messaging host (registers with Firefox)
- ✅ yt-dlp + ffmpeg (if missing)
- ✅ Extension manifest

Then just drag `dist/yt-dlp-downloader.xpi` into `about:addons`.

## 📖 Usage

| Action | How |
|--------|-----|
| **Download from current page** | Click extension icon → **Detected** tab → click **Download** |
| **Download from URL** | Click extension icon → **Manual URL** tab → paste link → **Get Info** → **Download** |
| **Right-click any link** | Context menu → **Download with yt-dlp** / **Audio Only** / **Best Quality** |
| **Keyboard shortcut** | Press `Alt+D` on any video page |
| **Watch progress** | Extension popup → **Downloads** tab |

## ⚙️ Requirements

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.8+ | Runs native host |
| **yt-dlp** | 2024+ | Video downloading |
| **ffmpeg** | 4.0+ | Video/audio merging |
| **Firefox** | 57+ | Extension runtime |

## 🔧 How It Works

```
┌─────────────┐     Native Messaging      ┌──────────────────┐
│  Firefox    │ ◄──────────────────────► │  Python Host     │
│  Extension  │   (JSON over stdin/stdout) │  (native_host/)  │
└─────────────┘                           └────────┬─────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │  yt-dlp + ffmpeg │
                                          │  (system PATH)   │
                                          └──────────────────┘
```

The extension **never** communicates with external servers. All downloads run locally on your machine.

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run native host directly (for testing)
echo '{"id":1,"command":"health_check"}' | python native_host/host.py

# Build extension
./scripts/build.sh

# Run tests
pytest tests/
```

### Project Structure

```
yt-dlp-downloader/
├── extension/              # Firefox WebExtension (MV2)
│   ├── manifest.json
│   ├── background/         # Service worker
│   ├── content/           # Content scripts
│   ├── popup/             # Popup UI (HTML/CSS/JS)
│   └── icons/
├── native_host/           # Python native messaging host
│   ├── host.py
│   └── com.kajusmar.ytdlp_downloader.json
├── scripts/
│   ├── install_windows.bat
│   ├── install_linux.sh
│   └── build.sh
├── tests/
└── dist/                  # Built .xpi files
```

## 📦 Building Releases

GitHub Actions automatically builds `.xpi` on tag push:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow:
1. Runs tests
2. Builds `.xpi` 
3. Creates GitHub Release with artifact

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — the incredible downloader engine
- [ffmpeg](https://ffmpeg.org/) — media processing
- [Firefox WebExtensions API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)

## ⚠️ Disclaimer

This tool is for **personal use only**. Respect copyright and Terms of Service of video platforms. The authors are not responsible for misuse.