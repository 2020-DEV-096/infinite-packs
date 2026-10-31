# infinite-packs
Signed, data-only remote update packs for Infinite (build 4+). No executable code is ever shipped.

## Endpoints
- Primary: `https://privaku.com/infinite/packs/manifest.json` (+ `manifest-v<N>.json`, `<id>__<type>__<version>.zip`)
- Mirror: `https://github.com/2020-DEV-096/infinite-packs/releases/download/m<N>/<file>` (latest: `releases/latest/download/manifest.json`)

## Manifest (schema `infinite-packs/1`, see schema/manifest.schema.json)
```json
{"schema":"infinite-packs/1","version":1,"min_app_version":"4.0","issued_at":"2026-10-31T13:00:00Z",
 "packs":[{"id":"test-rules","type":"rules","version":1,"url":"https://privaku.com/infinite/packs/test-rules__rules__1.zip",
  "mirror_url":"https://github.com/2020-DEV-096/infinite-packs/releases/download/m1/test-rules__rules__1.zip","sha256":"<hex>","size":123}],
 "signature":{"alg":"ed25519","key_id":"<first 16 hex of sha256(pubkey)>","value":"<base64 sig>"}}
```
Signature: Ed25519 over canonical JSON of the manifest without `signature` (sorted keys, `,`/`:` separators, UTF-8, non-ASCII unescaped).
`type` ∈ rules|config|prompts|weights|content|model. Packs are zips of data files only (json/txt/md/csv/yaml/bin/safetensors/gguf/mlmodel/onnx/tflite/images/audio); scripts, binaries, symlinks, exec bits are rejected.

## App rules
1. Fetch primary, fall back to mirror. 2. Verify signature with embedded key (`keys/pack-signing-ed25519.pub.b64`). 3. Reject if `version` ≤ installed (no rollback) or app < `min_app_version`. 4. Download each pack, check size+sha256, then swap atomically; keep the last good set.
5. Trigger: silent push (`content-available:1`, payload `infinite_packs.manifest_version`) or app launch/background refresh.

## Tools
- `tools/pack-publish.sh <dir> <version> <min_app> [--release]` sign, verify, stage, (GitHub release)
- `tools/pack-verify.sh <manifest|URL> [dir]`
- `tools/apns-silent-push.py <token> <version> [--send]` (dry run by default)
Private key is never in this repo.
