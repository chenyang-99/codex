#!/usr/bin/env python3
"""One anonymous Douyin open hot-board probe. No login, cookies or protected APIs."""
import hashlib,io,json,os,subprocess,tarfile,tempfile
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent/"output"
URL="https://github.com/tamnd/douyin-cli/releases/download/v0.1.1/douyin_0.1.1_linux_amd64.tar.gz"
EXPECTED="4baca0b04ed6d1e6568233cdd53bb818ae3bf033ccb8da4ffbbb6bcd7761796d"
report={"platform":"douyin","checked_at_utc":datetime.now(timezone.utc).isoformat(),
        "surface":"public hot-search billboard only","status":"not_verified",
        "records_returned":0,"comments_status":"not_supported_anonymous",
        "social_account_login_used":False}
try:
    with urlopen(Request(URL,headers={"User-Agent":"PublicTopicRadar/1.0"}),timeout=30) as stream:
        blob=stream.read(12000000)
    if hashlib.sha256(blob).hexdigest()!=EXPECTED:raise ValueError("SHA256 integrity failure")
    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:gz") as arc:
        rows=[m for m in arc.getmembers() if m.isfile() and Path(m.name).name=="douyin"]
        if len(rows)!=1:raise ValueError("No unambiguous binary")
        executable=arc.extractfile(rows[0]).read()
    with tempfile.TemporaryDirectory() as folder:
        binary=Path(folder)/"douyin";binary.write_bytes(executable);binary.chmod(0o700)
        env={k:v for k,v in os.environ.items() if not k.startswith("DOUYIN_")}
        env["HOME"]=folder
        process=subprocess.run([str(binary),"hot","-n","12","-o","json"],
                               capture_output=True,text=True,timeout=40,env=env)
        report["exit_code"]=process.returncode
        if process.returncode==0:
            try:
                payload=json.loads(process.stdout)
                if isinstance(payload,list):items=payload
                elif isinstance(payload,dict):
                    items=next((payload[k] for k in ("items","data","hot","list")
                                if isinstance(payload.get(k),list)),[])
                else:items=[]
                real=[x for x in items if isinstance(x,dict) and any(x.get(k) for k in ("word","name","title","rank"))]
                report.update(status="verified" if real else "unverified_response",
                              records_returned=len(real),
                              sample=[{k:str(v)[:100] for k,v in x.items() if k in ("word","name","title","rank","hot_value")}
                                      for x in real[:5]])
            except ValueError: report["status"]="unverified_response"
        else:
            report["status"]="restricted_or_failed"
            report["note"]=" ".join((process.stderr or process.stdout).split())[:170]
except Exception as exc:report["note"]=type(exc).__name__+": "+" ".join(str(exc).split())[:170]
OUT.mkdir(exist_ok=True,parents=True)
(OUT/"douyin-public.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"test":"douyin_public_hot",**report},ensure_ascii=False))
