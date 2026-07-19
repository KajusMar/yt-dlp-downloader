#!/bin/bash
# Build script for yt-dlp Video Downloader

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

# Create .xpi (zip with specific structure)
cd "$EXT_DIR"
# Create zip excluding unnecessary files
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

# Verify
if [ -f "$DIST_DIR/$XPI_NAME" ]; then
    SIZE=$(du -h "$DIST_DIR/$XPI_NAME" | cut -f1)
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
unzip -l "$DIST_DIR/$XPI_NAME" | head -30