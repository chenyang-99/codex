#!/usr/bin/env python3
"""One read-only, anonymous Xiaohongshu public feed test; no account or user Cookie."""
import hashlib,io,json,os,subprocess,tarfile,tempfile
from pathlib import Path
from urllib.request import urlopen,Request
p=Path(__file__).resolve().parent
url="https://github.com/tamnd/xiaohongshu-cli/releases/download/v0.2.0/xhs_0.2.0_linux_amd64.tar.gz"
expected="38cf3131531e78ea8cc41a29fd5b38277406a58beb68f13c9b36f02bc131cbfb"
r={"platform":"xiaohongshu","status":"not_verified","records_returned":0,
   "comments":"requires_login_not_tested","personal_account_login":False,
   "anonymous_session_cookie_may_be_created":True}
try:
    with urlopen(Request(url,headers={"User-Agent":"PublicTopicResearch/1.0"}),timeout=30) as stream:
        blob=stream.read(12000000)
    if hashlib.sha256(blob).hexdigest()!=expected:raise ValueError("SHA256 mismatch")
    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as arc:
        entries=[m for m in arc.getmembers() if m.isfile() and Path(m.name).name=="xhs"]
        if len(entries)!=1:raise ValueError("No unambiguous xhs executable")
        data=arc.extractfile(entries[0]).read()
    with tempfile.TemporaryDirectory() as tmp:
        exe=Path(tmp)/"xhs";exe.write_bytes(data);exe.chmod(0o700)
        env={k:v for k,v in os.environ.items() if not k.startswith("XHS_")}
        env.update({"HOME":tmp,"XHS_CONFIG_DIR":str(Path(tmp)/"conf")})
        process=subprocess.run([str(exe),"feed","-n","3","-o","json"],
                               capture_output=True,text=True,timeout=42,env=env)
        r["cli_exit"]=process.returncode
        if process.returncode==0:
            try:
                raw=json.loads(process.stdout)
                rows=raw if isinstance(raw,list) else next((raw[k] for k in ("notes","data","items") if isinstance(raw.get(k),list)),[])
                real=[x for x in rows if isinstance(x,dict) and any(x.get(k) for k in ("title","note_id","id","desc"))]
                r.update(status="verified" if real else "unverified_output",records_returned=len(real),
                         sample_keys=[list(x.keys())[:8] for x in real[:2]])
            except Exception:r["status"]="unverified_output"
        else:
            r["status"]="restricted_or_failed"
            r["error"]=" ".join((process.stderr or process.stdout).split())[:180]
except Exception as exc:r["error"]=type(exc).__name__+": "+" ".join(str(exc).split())[:180]
q=p/"output";q.mkdir(exist_ok=True)
(q/"xiaohongshu-public.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"test":"anonymous_xhs_feed",**r},ensure_ascii=False))
