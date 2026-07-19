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

# Create .xpi - use PowerShell on Windows, zip on Unix
if command -v zip >/dev/null 2>&1; then
    # Unix/Linux/macOS with zip
    cd "$EXT_DIR"
    zip -r "../$DIST_DIR/$XPI_NAME" . \
        -x "*.DS_Store" \
        -x "*/\.*" \
        -x "*.map" \
        -x "*.ts" \
        -x "*.md" \
        -x "node_modules/*" \
        -x "*.test.*" \
        -x "*.spec.*"
    cd ..
elif command -v powershell >/dev/null 2>&1 || command -v pwsh >/dev/null 2>&1; then
    # Windows with PowerShell
    PS_CMD="powershell"
    command -v pwsh >/dev/null 2>&1 && PS_CMD="pwsh"
    
    $PS_CMD -NoProfile -Command "
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            '$(pwd -W)/extension',
            '$(pwd -W)/dist/$XPI_NAME',
            [System.IO.Compression.CompressionLevel]::Optimal,
            \$false
        )
    "
else
    echo "❌ Neither 'zip' nor 'powershell' found. Cannot create .xpi"
    exit 1
fi

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