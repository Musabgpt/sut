#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEB_ROOT="$PROJECT_ROOT/packaging/deb"
DIST_DIR="$PROJECT_ROOT/dist"
VERSION="$(awk '/^Version:/ {print $2; exit}' "$DEB_ROOT/DEBIAN/control")"
ICON="$PROJECT_ROOT/assets/sut.png"

# Stage a clean copy of the Python package inside the DEB tree.
rm -rf "$DEB_ROOT/usr/share/sut"
mkdir -p "$DEB_ROOT/usr/share/sut"
cp -r "$PROJECT_ROOT/sut" "$DEB_ROOT/usr/share/sut/sut"
find "$DEB_ROOT/usr/share/sut" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$DEB_ROOT/usr/share/sut" -name '*.pyc' -delete

# Application icon and documentation.
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps" "$DEB_ROOT/usr/share/doc/sut"
cp "$ICON" "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/sut.png"
cp "$PROJECT_ROOT/README.md" "$DEB_ROOT/usr/share/doc/sut/README.md"
chmod 0755 "$DEB_ROOT/usr/bin/sut"
chmod 0644 "$DEB_ROOT/usr/share/applications/sut.desktop"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DIST_DIR/sut_${VERSION}_all.deb"
echo "Built $DIST_DIR/sut_${VERSION}_all.deb"
