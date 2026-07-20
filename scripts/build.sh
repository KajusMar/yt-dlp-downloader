#!/bin/bash
# Build script for yt-dlp Video Downloader (cross-platform)

set -e

EXT_DIR="extension"
DIST_DIR="dist"
XPI_NAME="yt-dlp-downloader.xpi"

echo "🔨 Building yt-dlp Video Downloader..."

# Clean & create dist
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Validate manifest
if [ ! -f "$EXT_DIR/manifest.json" ]; then
    echo "❌ manifest.json not found in $EXT_DIR"
    exit 1
fi

# Get version from manifest
VERSION=$(grep '"version"' "$EXT_DIR/manifest.json" | sed -E 's/.*"version": "([^"]+)".*/\1/')
echo "📦 Version: $VERSION"

# Build the .xpi with Python's zipfile (Firefox-compatible nested paths).
# We deliberately avoid PowerShell Compress-Archive: it emits ZIP entries that
# Firefox's strict JAR reader sometimes fails to serve (manifest.json loads but
# subfolder files like popup/popup.html 404). See scripts/build_xpi.py.
python3 scripts/build_xpi.py 2>/dev/null || python scripts/build_xpi.py

# Verify
if [ -f "$DIST_DIR/$XPI_NAME" ]; then
    SIZE=$(du -h "$DIST_DIR/$XPI_NAME" 2>/dev/null | cut -f1 || stat -c%s "$DIST_DIR/$XPI_NAME" 2>/dev/null | awk '{print $1/1024 "K"}' || echo "?")
    echo "✅ Built: $DIST_DIR/$XPI_NAME ($SIZE)"
    
    # Also create versioned copy
    cp "$DIST_DIR/$XPI_NAME" "$DIST_DIR/yt-dlp-downloader-v$VERSION.xpi"
    echo "✅ Versioned: $DIST_DIR/yt-dlp-downloader-v$VERSION.xpi"
else
    echo "❌ Build failed"
    exit 1
fi

# List contents
echo ""
echo "📋 Extension contents:"
if command -v unzip >/dev/null 2>&1; then
    unzip -l "$DIST_DIR/$XPI_NAME" | head -30
elif command -v powershell >/dev/null 2>&1 || command -v pwsh >/dev/null 2>&1; then
    $PS_CMD -NoProfile -Command "
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        \$zip = [System.IO.Compression.ZipFile]::OpenRead('$(pwd -W)/dist/$XPI_NAME')
        \$zip.Entries | Select-Object Name, CompressedLength, LastWriteTime | Format-Table -AutoSize
        \$zip.Dispose()
    "
fi