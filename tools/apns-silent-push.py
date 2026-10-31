#!/usr/bin/env python3
"""Send a silent (content-available:1) APNs push telling Infinite to fetch a new pack manifest.
Config: apns.config.json (env vars override): APNS_KEY_PATH (.p8 APNs auth key, read-only, never printed), APNS_KEY_ID, APNS_TEAM_ID,
     APNS_TOPIC (bundle id), APNS_ENV=sandbox|production (default sandbox).
Usage: apns-silent-push.py <device_token> <manifest_version> [--send]   (dry run without --send)"""
import base64, json, os, subprocess, sys, time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
b64=lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def jwt(key_path,kid,team):
    with open(key_path,"rb") as f: k=serialization.load_pem_private_key(f.read(),None)
    h=b64(json.dumps({"alg":"ES256","kid":kid}).encode()); p=b64(json.dumps({"iss":team,"iat":int(time.time())}).encode())
    r,s=decode_dss_signature(k.sign(f"{h}.{p}".encode(),ec.ECDSA(hashes.SHA256())))
    return f"{h}.{p}.{b64(r.to_bytes(32,'big')+s.to_bytes(32,'big'))}"
CFG=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","apns.config.json")))
def conf(env,key): return os.environ.get(env) or CFG.get(key,"")
def main():
    a=sys.argv[1:]
    if len(a)<2: sys.exit(__doc__)
    token,ver,send=a[0],int(a[1]),"--send" in a
    body={"aps":{"content-available":1},"infinite_packs":{"manifest_version":ver,"manifest_url":"https://privaku.com/infinite/packs/manifest.json"}}
    host="api.sandbox.push.apple.com" if conf("APNS_ENV","env")!="production" else "api.push.apple.com"
    topic=conf("APNS_TOPIC","topic")
    print("payload:",json.dumps(body)); print("host:",host,"topic:",topic,"token:",token[:8]+"…")
    kp=conf("APNS_KEY_PATH","key_path"); print("team:",conf("APNS_TEAM_ID","team_id"),"key_id:",conf("APNS_KEY_ID","key_id") or "(unset)","key file present:",os.path.isfile(kp))
    if not send: print("dry run (add --send)"); return
    if not (os.path.isfile(kp) and conf("APNS_KEY_ID","key_id")): sys.exit("no APNs key configured")
    auth=jwt(conf("APNS_KEY_PATH","key_path"),conf("APNS_KEY_ID","key_id"),conf("APNS_TEAM_ID","team_id"))
    r=subprocess.run(["curl","-sS","--http2","-o","/dev/stderr","-w","%{http_code}","-H","apns-push-type: background","-H","apns-priority: 5",
        "-H",f"apns-topic: {topic}","-H","@-","-d",json.dumps(body),f"https://{host}/3/device/{token}"],
        input=f"authorization: bearer {auth}\n",capture_output=True,text=True)  # header via stdin: JWT never on argv
    print("HTTP",r.stdout, r.stderr.strip()); sys.exit(0 if r.stdout=="200" else 1)
main()
