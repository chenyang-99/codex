"""Shared normalized Evidence contract, mirrored from opentopic_radar.models."""
from dataclasses import dataclass,asdict,field
from datetime import datetime,timezone
from hashlib import sha256
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
TRACKING={"fbclid","gclid","ref_src","utm_source","utm_medium","utm_campaign"}
def now_utc():return datetime.now(timezone.utc).isoformat(timespec="microseconds")
def canonicalize(url):
    p=urlsplit(url.strip())
    if p.scheme not in ("http","https") or not p.hostname or p.username or p.password:raise ValueError("Invalid URL")
    query=urlencode([(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if k.lower() not in TRACKING and not k.lower().startswith("utm_")])
    host=p.hostname.lower();path=p.path.rstrip("/") or "/"
    if host in ("github.com","www.github.com"):
        host="github.com";parts=[x for x in path.split("/") if x]
        if len(parts)>=2:path="/"+"/".join(parts[:2]).lower();query=""
    return urlunsplit((p.scheme,host,path,query,""))
def entity_for(url):return sha256(canonicalize(url).encode()).hexdigest()[:24]
@dataclass(frozen=True)
class Evidence:
    source_id:str
    platform:str
    source_url:str
    canonical_url:str
    author:str
    published_at:str|None
    collected_at:str
    language:str|None
    content_type:str
    title:str
    body_excerpt:str
    raw_ref:str
    metrics:dict=field(default_factory=dict)
    mode:str="K"
    evidence_status:str="official_metadata_only"
    access_limitation:str|None=None
    adapter_version:str="0.1.0"
    job_id:str=""
    entity_id:str=""
    def as_dict(self):
        d=asdict(self);d["canonical_url"]=canonicalize(d["canonical_url"]);d["entity_id"]=self.entity_id or entity_for(d["canonical_url"]);return d
