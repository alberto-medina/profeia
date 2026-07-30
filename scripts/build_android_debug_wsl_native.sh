#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="$HOME/profeia-android-build-$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BUILD_ROOT"

rsync -a --exclude ".buildozer" --exclude "bin" "$SOURCE_ROOT/frontend" "$BUILD_ROOT/"
rsync -a "$SOURCE_ROOT/scripts" "$BUILD_ROOT/"

cd "$BUILD_ROOT"
bash scripts/build_android_debug_wsl.sh

mkdir -p "$SOURCE_ROOT/frontend/bin"
cp -v frontend/bin/*.apk "$SOURCE_ROOT/frontend/bin/"
ls -lh "$SOURCE_ROOT/frontend/bin/"*.apk
