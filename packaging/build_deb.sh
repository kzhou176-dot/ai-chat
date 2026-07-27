#!/bin/bash
# build_deb.sh — aichat-hub DEB 包构建脚本
#
# 用法:
#   bash packaging/build_deb.sh                  # 默认 all(跨架构)
#   bash packaging/build_deb.sh arm64            # Linux aarch64
#   bash packaging/build_deb.sh armhf            # Linux armv7
#   bash packaging/build_deb.sh amd64            # Linux x86_64
#
# 源文件:
#   packaging/debian/                  DEB 元数据(控制文件,conffiles,postinst 等)
#   scripts/  data/  research/  papers/   内容(不含 pdfs)
#   README.md  CHANGELOG.md  LICENSE   文档
#
# 输出:
#   dist/aichat-hub_1.0.2_${ARCH}.deb
#
# 跨平台:macOS/Linux 都能跑(只依赖 tar + ar,无需 dpkg-deb)

set -e

PACKAGE_NAME="aichat-hub"
VERSION="1.0.2"
ARCH="${1:-all}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEBIAN_SRC="$ROOT_DIR/packaging/debian"
STAGE_DIR="$ROOT_DIR/packaging/stage"
DIST_DIR="$ROOT_DIR/dist"
DEB_FILE="$DIST_DIR/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

case "$ARCH" in
    all|amd64|arm64|armhf) ;;
    *) echo "ERROR: unsupported arch '$ARCH'. Use: all|amd64|arm64|armhf" >&2; exit 1 ;;
esac

echo "[build_deb] Package: $PACKAGE_NAME $VERSION ($ARCH)"
echo "[build_deb] Source:  $ROOT_DIR"
echo "[build_deb] Output:  $DEB_FILE"

# 1. 准备 stage
echo "[build_deb] Preparing stage..."
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/DEBIAN"
mkdir -p "$STAGE_DIR/usr/bin"
mkdir -p "$STAGE_DIR/usr/lib/aichat-hub/scripts"
mkdir -p "$STAGE_DIR/usr/share/aichat-hub"
mkdir -p "$STAGE_DIR/etc/aichat-hub"
mkdir -p "$DIST_DIR"

# 复制 DEBIAN 元数据
cp "$DEBIAN_SRC/control" "$STAGE_DIR/DEBIAN/control"
cp "$DEBIAN_SRC/conffiles" "$STAGE_DIR/DEBIAN/" 2>/dev/null || true
cp "$DEBIAN_SRC/postinst" "$STAGE_DIR/DEBIAN/" 2>/dev/null || true
cp "$DEBIAN_SRC/postrm" "$STAGE_DIR/DEBIAN/" 2>/dev/null || true
cp "$DEBIAN_SRC/prerm" "$STAGE_DIR/DEBIAN/" 2>/dev/null || true
cp "$DEBIAN_SRC/changelog.Debian.gz" "$STAGE_DIR/DEBIAN/" 2>/dev/null || true
chmod 755 "$STAGE_DIR/DEBIAN/postinst" "$STAGE_DIR/DEBIAN/postrm" "$STAGE_DIR/DEBIAN/prerm" 2>/dev/null || true

# 复制 scripts → usr/lib/aichat-hub/scripts
cp -r "$ROOT_DIR/scripts/." "$STAGE_DIR/usr/lib/aichat-hub/scripts/"

# 复制 data / research → usr/share/aichat-hub
cp -r "$ROOT_DIR/data" "$STAGE_DIR/usr/share/aichat-hub/data"
cp -r "$ROOT_DIR/research" "$STAGE_DIR/usr/share/aichat-hub/research"

# 复制 papers(只 JSON,不含 pdfs)
mkdir -p "$STAGE_DIR/usr/share/aichat-hub/papers"
for d in "$ROOT_DIR/papers"/*/; do
    name=$(basename "$d")
    if [ "$name" != "pdfs" ]; then
        mkdir -p "$STAGE_DIR/usr/share/aichat-hub/papers/$name"
        cp "$d"*.json "$STAGE_DIR/usr/share/aichat-hub/papers/$name/" 2>/dev/null || true
    fi
done

# 文档
mkdir -p "$STAGE_DIR/usr/share/doc/aichat-hub"
cp "$ROOT_DIR/README.md" "$STAGE_DIR/usr/share/doc/aichat-hub/" 2>/dev/null || true
cp "$ROOT_DIR/CHANGELOG.md" "$STAGE_DIR/usr/share/doc/aichat-hub/" 2>/dev/null || true
cp "$ROOT_DIR/LICENSE" "$STAGE_DIR/usr/share/doc/aichat-hub/" 2>/dev/null || true
cp "$ROOT_DIR/MASTER_PLAN.md" "$STAGE_DIR/usr/share/doc/aichat-hub/" 2>/dev/null || true

# 启动器
cp "$ROOT_DIR/bin/aichat-hub-launcher" "$STAGE_DIR/usr/bin/aichat-hub"
chmod +x "$STAGE_DIR/usr/bin/aichat-hub"

# 2. 动态改 Architecture(如果指定)
if [ "$ARCH" != "all" ]; then
    sed -i.bak "s/^Architecture: .*/Architecture: $ARCH/" "$STAGE_DIR/DEBIAN/control"
    rm -f "$STAGE_DIR/DEBIAN/control.bak"
fi

# 3. 打包
BUILD_TMP="$(mktemp -d -t aichat-deb)"
trap "rm -rf $BUILD_TMP" EXIT

# 3a. debian-binary
echo "2.0" > "$BUILD_TMP/debian-binary"

# 3b. control.tar.gz
mkdir -p "$BUILD_TMP/control"
cp "$STAGE_DIR/DEBIAN/control" "$BUILD_TMP/control/control"
cp "$STAGE_DIR/DEBIAN/conffiles" "$BUILD_TMP/control/" 2>/dev/null || true
cp "$STAGE_DIR/DEBIAN/postinst" "$BUILD_TMP/control/" 2>/dev/null || true
cp "$STAGE_DIR/DEBIAN/postrm" "$BUILD_TMP/control/" 2>/dev/null || true
cp "$STAGE_DIR/DEBIAN/prerm" "$BUILD_TMP/control/" 2>/dev/null || true
cp "$STAGE_DIR/DEBIAN/changelog.Debian.gz" "$BUILD_TMP/control/" 2>/dev/null || true
chmod 644 "$BUILD_TMP/control/"* 2>/dev/null || true
chmod 755 "$BUILD_TMP/control/postinst" "$BUILD_TMP/control/postrm" "$BUILD_TMP/control/prerm" 2>/dev/null || true
(cd "$BUILD_TMP/control" && tar -czf "$BUILD_TMP/control.tar.gz" .)

# 3c. data.tar.gz
(cd "$STAGE_DIR" && tar -czf "$BUILD_TMP/data.tar.gz" usr etc)

# 3d. ar — 用 Python(跨平台,避免 macOS BSD ar 与 GNU ar 不兼容)
python3 - "$DEB_FILE" "$BUILD_TMP/debian-binary" "$BUILD_TMP/control.tar.gz" "$BUILD_TMP/data.tar.gz" <<'AR_EOF'
import sys
out, *parts = sys.argv[1:]
with open(out, "wb") as f:
    f.write(b"!<arch>\n")
    for p in parts:
        with open(p, "rb") as src:
            data = src.read()
        name = p.split("/")[-1].encode()
        if len(name) > 16:
            name = name[:16]
        else:
            name = name + b"/" * (16 - len(name))
        size = len(data)
        # 偶数对齐
        if size % 2:
            data += b"\n"
        f.write(name)
        f.write(b"0           ")  # date 12
        f.write(b"0     ")         # uid 6
        f.write(b"0     ")         # gid 6
        f.write(b"100644  ")       # mode 8
        f.write(f"{size:<10}".encode())  # size 10
        f.write(b"\x60\n")         # fmag
        f.write(data)
AR_EOF

echo "[build_deb] ✅ Built: $DEB_FILE"
echo "[build_deb] Size: $(du -h "$DEB_FILE" | cut -f1)"
echo ""
echo "Install on Linux:  sudo dpkg -i $DEB_FILE"
echo "Inspect on macOS:  ar tv $DEB_FILE"
