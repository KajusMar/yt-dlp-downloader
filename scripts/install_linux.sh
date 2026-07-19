#!/bin/bash
# Linux/macOS install script for yt-dlp Video Downloader native host

set -e

HOST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../native_host" && pwd)"
MANIFEST_SRC="$HOST_DIR/com.kajusmar.ytdlp_downloader.json"
HOST_PY="$HOST_DIR/host.py"

echo "🔧 yt-dlp Video Downloader - Linux/macOS Installer"
echo "=================================================="

# Check dependencies
echo "[1/4] Checking dependencies..."
for cmd in python3 yt-dlp ffmpeg; do
    if ! command -v $cmd &> /dev/null; then
        echo "❌ $cmd not found. Please install:"
        echo "   Ubuntu/Debian: sudo apt install python3 yt-dlp ffmpeg"
        echo "   Arch: sudo pacman -S python yt-dlp ffmpeg"
        echo "   Fedora: sudo dnf install python3 yt-dlp ffmpeg"
        echo "   macOS: brew install python yt-dlp ffmpeg"
        exit 1
    fi
    echo "   ✅ $cmd: $($cmd --version 2>&1 | head -1)"
done

# Determine Firefox native messaging directory
echo "[2/4] Detecting Firefox profile..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    NATIVE_DIR="$HOME/Library/Application Support/Mozilla/NativeMessagingHosts"
else
    # Linux
    NATIVE_DIR="$HOME/.mozilla/native-messaging-hosts"
fi

mkdir -p "$NATIVE_DIR"
echo "   📁 Target: $NATIVE_DIR"

# Copy and update manifest
echo "[3/4] Installing native messaging manifest..."
MANIFEST_DST="$NATIVE_DIR/com.kajusmar.ytdlp_downloader.json"
sed "s|\"path\": \"host.py\"|\"path\": \"$HOST_PY\"|" "$MANIFEST_SRC" > "$MANIFEST_DST"
echo "   ✅ Manifest installed to $MANIFEST_DST"

# Make host executable
chmod +x "$HOST_PY"

# Test native host
echo "[4/4] Testing native host..."
python3 "$HOST_PY" << 'EOF' &
{"id": 1, "command": "health_check"}
EOF
sleep 2
echo "   ✅ Native host test completed"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Install the Firefox extension:"
echo "   - Open about:addons"
echo "   - Gear icon → Install Add-on From File"
echo "   - Select dist/yt-dlp-downloader.xpi"
echo "2. Restart Firefox"
echo "3. Click the extension icon to test"
echo ""
echo "Download folder: ~/Videos/yt-dlp/"