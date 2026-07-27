#!/bin/bash
# build_macos.sh — aichat-hub macOS .app + .dmg 构建脚本
#
# 产物:
#   packaging/aichat-hub.app       (1.1MB,可双击)
#   dist/aichat-hub-1.0.2-arm64.dmg (520KB,DMG 安装镜像)
#
# 跨平台:必须在 macOS 上跑(hdiutil 是 macOS 专属)
#        非 macOS 平台只能构建 .app,无法生成 .dmg

set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT_DIR/packaging/aichat-hub.app"
DIST_DIR="$ROOT_DIR/dist"
DMG_NAME="aichat-hub-1.0.2-arm64.dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME"

echo "[build_macos] === Build aichat-hub.app ==="

# 1. 创建 .app bundle 目录结构
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources/aichat-hub"

# 2. 拷贝 Info.plist
cat > "$APP_DIR/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>aichat-hub</string>
    <key>CFBundleDisplayName</key>
    <string>aichat-hub</string>
    <key>CFBundleIdentifier</key>
    <string>local.aichat-hub</string>
    <key>CFBundleVersion</key>
    <string>1.0.2</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.2</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>aichat-hub-launcher</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    <key>NSHumanReadableCopyright</key>
    <string>MIT License - aichat-hub v1.0.2</string>
</dict>
</plist>
EOF

# 3. 写 launcher 脚本(启动真·桌面 app,tcl/tk)
cat > "$APP_DIR/Contents/MacOS/aichat-hub-launcher" <<'LAUNCHER_EOF'
#!/bin/bash
# aichat-hub macOS .app launcher
# 启动真·桌面 app(tkinter,需要 Python 3.12+)
set +e

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RES_DIR="$APP_DIR/Contents/Resources"
SCRIPTS_DIR="$RES_DIR/aichat-hub/scripts"
LOG_DIR="$HOME/Library/Logs/aichat-hub"
LOG_FILE="$LOG_DIR/launcher.log"
SERVER_LOG="$LOG_DIR/server.log"
PID_FILE="$LOG_DIR/desktop.pid"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "============================================"
log "aichat-hub 桌面 app 启动器"

# 1. 检查是否已经在跑
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    log "已在运行 (PID $(cat "$PID_FILE"))"
    osascript -e 'display notification "aichat-hub 已在运行" with title "aichat-hub"' 2>/dev/null
    exit 0
fi

# 2. 找 Python 3.13+(macOS 15 tkinter 兼容)
PYTHON_BIN=""
for py in /Users/yuefeng/.local/bin/python3.13 python3.13 /opt/homebrew/bin/python3.13 \
           /Users/yuefeng/.local/bin/python3.12 python3.12 /opt/homebrew/bin/python3.12 \
           /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3 python3; do
    if command -v "$py" >/dev/null 2>&1; then
        v=$("$py" -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>/dev/null)
        if [ -n "$v" ]; then
            major=$(echo "$v" | awk '{print $1}')
            minor=$(echo "$v" | awk '{print $2}')
            if [ "$major" = "3" ] && [ "$minor" -ge "12" ] 2>/dev/null; then
                if "$py" -c "import tkinter" 2>/dev/null; then
                    PYTHON_BIN="$py"
                    break
                fi
            fi
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    log "ERROR: 没找到 Python 3.12+"
    osascript -e 'display alert "aichat-hub" message "找不到 Python 3.12+(macOS 15 tkinter 兼容)。\nbrew install python3.13" as critical'
    exit 1
fi

log "Python: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"

# 3. 启动桌面 app
cd "$RES_DIR/aichat-hub"
export PYTHONPATH="$SCRIPTS_DIR:$PYTHONPATH"

nohup "$PYTHON_BIN" "$SCRIPTS_DIR/desktop_app.py" > "$SERVER_LOG" 2>&1 &
APP_PID=$!
echo $APP_PID > "$PID_FILE"
log "桌面 app PID: $APP_PID"

sleep 2
if kill -0 "$APP_PID" 2>/dev/null; then
    log "✓ 桌面 app 已启动"
    osascript -e 'display notification "已启动,查看 Dock 窗口" with title "aichat-hub" subtitle "v1.0.2"' 2>/dev/null
else
    log "ERROR: 启动失败"
    cat "$SERVER_LOG" >> "$LOG_FILE"
    rm -f "$PID_FILE"
    osascript -e 'display alert "aichat-hub 启动失败" message "查看日志: '"$LOG_FILE"'" as critical'
    exit 1
fi
exit 0
LAUNCHER_EOF
chmod +x "$APP_DIR/Contents/MacOS/aichat-hub-launcher"

# 4. 拷贝资源
RES="$APP_DIR/Contents/Resources/aichat-hub"
cp -r "$ROOT_DIR/scripts" "$RES/scripts"
cp -r "$ROOT_DIR/data" "$RES/data"
cp -r "$ROOT_DIR/research" "$RES/research"
cp "$ROOT_DIR/README.md" "$RES/"
cp "$ROOT_DIR/CHANGELOG.md" "$RES/"
cp "$ROOT_DIR/LICENSE" "$RES/"

# 5. 拷贝论文(只 JSON,不含 PDF)
mkdir -p "$RES/papers"
for d in "$ROOT_DIR/papers"/*/; do
    name=$(basename "$d")
    if [ "$name" != "pdfs" ]; then
        mkdir -p "$RES/papers/$name"
        cp "$d"*.json "$RES/papers/$name/" 2>/dev/null || true
    fi
done

echo "[build_macos] .app bundle: $APP_DIR"
du -sh "$APP_DIR"

# 6. 验证 Info.plist
if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$APP_DIR/Contents/Info.plist"
else
    python3 -c "import plistlib; plistlib.load(open('$APP_DIR/Contents/Info.plist', 'rb'))" && echo "[build_macos] ✓ Info.plist valid"
fi

# 7. 构建 DMG(仅 macOS)
if [ "$(uname)" = "Darwin" ]; then
    echo ""
    echo "[build_macos] === Build .dmg ==="
    mkdir -p "$DIST_DIR"
    STAGING="$(mktemp -d -t aichat-dmg)"
    cp -R "$APP_DIR" "$STAGING/"
    ln -s /Applications "$STAGING/Applications"
    hdiutil create -volname "aichat-hub 1.0.2" -srcfolder "$STAGING" -ov -format UDZO "$DMG_PATH" 2>&1 | tail -3
    rm -rf "$STAGING"
    echo "[build_macos] DMG: $DMG_PATH"
    ls -lah "$DMG_PATH"
else
    echo "[build_macos] ⚠️  DMG build skipped (only macOS supports hdiutil)"
fi

echo ""
echo "[build_macos] ✅ Build complete!"
echo ""
echo "产物:"
echo "  $APP_DIR ($(du -sh "$APP_DIR" | cut -f1))"
[ -f "$DMG_PATH" ] && echo "  $DMG_PATH ($(du -sh "$DMG_PATH" | cut -f1))"
echo ""
echo "用法(macOS):"
echo "  open $APP_DIR              # 双击启动"
echo "  open $DMG_PATH             # 打开 DMG,拖到 /Applications 安装"
