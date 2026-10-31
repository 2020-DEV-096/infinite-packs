#!/bin/bash
# Usage: pack-publish.sh <packs_dir> <manifest_version> <min_app_version> [--release]
# Signs manifest.json, verifies it, stages files for privaku.com/infinite/packs/ and
# (with --release) uploads them to GitHub Release m<version> on 2020-DEV-096/infinite-packs.
# Does NOT deploy privaku.com; copy the staged dir into the site branch the CEO names.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT=/Volumes/ssdDesiSam/Processing/infinite-packs
PY="$ROOT/.venv/bin/python"
KEY="${INFINITE_PACK_KEY:-/Users/sameeran/RESTRICTED/infinite-packs/signing-ed25519.key}"
[ -r "$KEY" ] || KEY="$ROOT/keys/signing-ed25519.key"
PUB="$(cat "$HERE/../keys/pack-signing-ed25519.pub.b64")"
DIR="$1"; VER="$2"; MIN="$3"; TAG="m$VER"; OUT="$ROOT/staging/$TAG"
[ -e "$OUT" ] && { echo "refusing to overwrite $OUT"; exit 1; }
mkdir -p "$OUT"; cp -n "$DIR"/*.zip "$OUT"/
"$PY" "$HERE/packlib.py" build "$OUT" "$VER" "$MIN" "$KEY" "$TAG" > "$OUT/manifest.json"
"$PY" "$HERE/packlib.py" verify "$OUT/manifest.json" "$PUB" "$OUT"
cp "$OUT/manifest.json" "$OUT/manifest-v$VER.json"
if [ "${4:-}" = "--release" ]; then
  gh release create "$TAG" -R 2020-DEV-096/infinite-packs -t "Manifest v$VER" -n "Signed data packs, manifest v$VER" "$OUT"/*.zip "$OUT"/manifest*.json
fi
echo "Staged: $OUT  -> site path infinite/packs/"
