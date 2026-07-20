# Quick Install Guide

## 🚀 Easiest Way (Windows)

1. **Download** `yt-dlp-downloader-windows.zip` from [latest release](https://github.com/KajusMar/yt-dlp-downloader/releases/latest)
2. **Extract** the zip file
3. **Right-click** `scripts\install_windows.bat` → **Run as Administrator**
4. Open Firefox → `about:addons` → Gear (⚙️) → **Install Add-on From File**
5. Select `yt-dlp-downloader.xpi` from the extracted folder
6. **Restart Firefox** when prompted

✅ Done! The auto-installer:
- Registers the native messaging host with Firefox
- Checks/installs `yt-dlp` and `ffmpeg` via winget
- Configures all permissions

---

## 📋 Manual Install (Any OS)

1. Download `yt-dlp-downloader.xpi` from [latest release](https://github.com/KajusMar/yt-dlp-downloader/releases/latest)
2. Open Firefox → `about:addons` → Gear (⚙️) → **Install Add-on From File**
3. Select the `.xpi` file
4. **Restart Firefox**

**Requirements** (manual install only): `yt-dlp` + `ffmpeg` must be in your PATH
- Windows: `winget install yt-dlp ffmpeg`
- macOS: `brew install yt-dlp ffmpeg`
- Linux: `sudo apt install yt-dlp ffmpeg`

---

## 🎮 How to Use

| Action | How |
|--------|-----|
| **Detect videos on page** | Click extension icon → **Detected** tab |
| **Download from URL** | Extension icon → **Manual URL** tab → paste link → **Get Info** → **Download** |
| **Right-click any link** | Context menu → **Download with yt-dlp** |
| **Keyboard shortcut** | `Alt+D` on any video page |
| **Progress** | Extension popup → **Downloads** tab |

---

## ⚡ Quick Test

After install, click the extension icon — you should see:
- `yt-dlp 2026.07.04 • ffmpeg` (or similar)
- "Connected" status

If it says "Not connected": restart Firefox, or run the auto-installer again.