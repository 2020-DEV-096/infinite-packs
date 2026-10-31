#!/bin/bash
# Usage: pack-verify.sh <manifest.json|URL> [packs_dir]
set -euo pipefail; HERE="$(cd "$(dirname "$0")" && pwd)"
PY=/Volumes/ssdDesiSam/Processing/infinite-packs/.venv/bin/python
M="$1"; if [[ "$M" == https://* ]]; then T=$(mktemp); curl -fsSL "$M" -o "$T"; M="$T"; fi
"$PY" "$HERE/packlib.py" verify "$M" "$(cat "$HERE/../keys/pack-signing-ed25519.pub.b64")" ${2:-}
