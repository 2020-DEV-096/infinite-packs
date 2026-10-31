"""Infinite pack manifest sign/verify. Signature = Ed25519 over canonical JSON
(sorted keys, no spaces, UTF-8) of the manifest WITHOUT the 'signature' field."""
import base64, hashlib, json, os, sys, zipfile, datetime
from cryptography.hazmat.primitives import serialization as s
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
TYPES={"rules","config","prompts","weights","content","model"}
DATA_EXT={".json",".txt",".md",".csv",".yaml",".yml",".bin",".safetensors",".gguf",".mlmodel",".mlpackage",".onnx",".tflite",".png",".jpg",".webp",".mp3",".m4a"}
BAD_EXT={".js",".py",".sh",".dylib",".so",".exe",".bundle",".framework",".wasm",".lua",".swift",".plist"}
BASE="https://privaku.com/infinite/packs/"; MIRROR="https://github.com/2020-DEV-096/infinite-packs/releases/download/"
def canon(m): return json.dumps({k:v for k,v in m.items() if k!="signature"},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def key_id(pub): return hashlib.sha256(pub).hexdigest()[:16]
def check_data_only(path):
    """Packs are zip archives of data files only; reject code/executables/symlinks."""
    with zipfile.ZipFile(path) as z:
        for i in z.infolist():
            n=i.filename; ext=os.path.splitext(n)[1].lower()
            if n.startswith("/") or ".." in n.split("/"): raise SystemExit(f"unsafe path {n}")
            if (i.external_attr>>16)&0o170000==0o120000: raise SystemExit(f"symlink {n}")
            if (i.external_attr>>16)&0o111: raise SystemExit(f"executable bit {n}")
            if n.endswith("/"): continue
            if ext in BAD_EXT or ext not in DATA_EXT: raise SystemExit(f"non-data file {n}")
            if z.read(n)[:4] in (b"\xcf\xfa\xed\xfe",b"\xca\xfe\xba\xbe",b"\x7fELF") or z.read(n)[:2]==b"#!": raise SystemExit(f"binary/script {n}")
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def build(packs_dir, version, min_app, keyfile, tag):
    with open(keyfile,"rb") as f: k=s.load_pem_private_key(f.read(),None)
    pub=k.public_key().public_bytes(s.Encoding.Raw,s.PublicFormat.Raw)
    packs=[]
    for fn in sorted(os.listdir(packs_dir)):
        if not fn.endswith(".zip"): continue
        pid,ptype,pver=fn[:-4].rsplit("__",2)  # <id>__<type>__<version>.zip
        assert ptype in TYPES, fn; p=os.path.join(packs_dir,fn); check_data_only(p)
        packs.append({"id":pid,"type":ptype,"version":int(pver),"url":BASE+fn,"mirror_url":f"{MIRROR}{tag}/{fn}","sha256":sha(p),"size":os.path.getsize(p)})
    m={"schema":"infinite-packs/1","version":int(version),"min_app_version":min_app,
       "issued_at":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),"packs":packs}
    m["signature"]={"alg":"ed25519","key_id":key_id(pub),"value":base64.b64encode(k.sign(canon(m))).decode()}
    return m
def verify(manifest_path, pub_b64, packs_dir=None):
    m=json.load(open(manifest_path)); pub=base64.b64decode(pub_b64)
    assert m.get("schema")=="infinite-packs/1" and m["signature"]["alg"]=="ed25519"
    assert m["signature"]["key_id"]==key_id(pub), "key_id mismatch"
    Ed25519PublicKey.from_public_bytes(pub).verify(base64.b64decode(m["signature"]["value"]),canon(m))
    for p in m["packs"]:
        assert p["type"] in TYPES and p["url"].startswith(BASE) and p["mirror_url"].startswith(MIRROR)
        if packs_dir:
            f=os.path.join(packs_dir,os.path.basename(p["url"]))
            assert sha(f)==p["sha256"] and os.path.getsize(f)==p["size"], f"hash/size mismatch {f}"; check_data_only(f)
    return m
if __name__=="__main__":
    c=sys.argv[1]
    if c=="build": json.dump(build(*sys.argv[2:7]),sys.stdout,indent=2); print()
    elif c=="verify": m=verify(*sys.argv[2:]); print(f"OK manifest v{m['version']} ({len(m['packs'])} packs)")
