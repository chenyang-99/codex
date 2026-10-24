const BASE_COMMIT="24a8413586fdc58276df2fb5e2b8a6b769161c3c";
const VERSION="v3.2-cf-migration-rss1";
const VALUES=["utility","learning","save","decision","insight","information","emotion","entertainment","social_expression"];
const headers={"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"};
function json(obj,status=200){return new Response(JSON.stringify(obj),{status,headers});}
function canonical(raw){try{const u=new URL(raw);if(!["http:","https:"].includes(u.protocol))return "";u.hash="";for(const k of [...u.searchParams.keys()])if(/^utm_|^fbclid$|^gclid$|^ref$/i.test(k))u.searchParams.delete(k);if(u.hostname==="twitter.com"||u.hostname==="www.twitter.com")u.hostname="x.com";return u.toString()}catch{return ""}}
function xmlDecode(t){return String(t||"").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,"$1").replace(/&#x([0-9a-f]+);/gi,(_,n)=>String.fromCodePoint(parseInt(n,16))).replace(/&#([0-9]+);/g,(_,n)=>String.fromCodePoint(Number(n))).replace(/&(amp|lt|gt|quot|apos|nbsp);/gi,(_,x)=>({amp:"&",lt:"<",gt:">",quot:'"',apos:"'",nbsp:" "}[x.toLowerCase()]||" ")).replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim();}
function tag(b,n){const m=b.match(new RegExp("<(?:[\\w.-]+:)?"+n+"(?:\\s[^>]*)?>([\\s\\S]*?)<\\/(?:[\\w.-]+:)?"+n+">","i"));return m?xmlDecode(m[1]):""}
function rssList(raw){const found=[];const re=/<(?:item|entry)(?:\s[^>]*)?>([\s\S]*?)<\/(?:item|entry)>/gi;let m;while((m=re.exec(raw))&&found.length<30){const b=m[1];let link=tag(b,"link");if(!link){const l=b.match(/<link\b[^>]*href=["']([^"']+)["']/i);link=l?xmlDecode(l[1]):""}const url=canonical(link);const title=tag(b,"title");if(!url||!title)continue;found.push({url,title:title.slice(0,450),excerpt:(tag(b,"summary")||tag(b,"description")||"").slice(0,850),date:tag(b,"pubDate")||tag(b,"published")||tag(b,"updated")||null,author:tag(b,"author")||""})}return found}
async function capFetch(url){const x=await fetch(url,{headers:{"user-agent":"AI30 Topic Radar research-only/3.2","accept":"application/rss+xml, application/atom+xml, application/xml, text/xml, */*"},redirect:"follow",signal:AbortSignal.timeout(13000)});if(!x.ok)throw Error("http_"+x.status);const data=await x.text();if(data.length>1700000)throw Error("feed_too_large");return{status:x.status,items:rssList(data)}}
function normalizeDate(v){if(!v)return null;const d=new Date(v);return Number.isFinite(d.valueOf())?d.toISOString():null;}

const METRIC_SCOPE="platform_native_only";
function cleanDate(v){if(v===null||v===undefined||v==="")return null;let t=typeof v==="number"?new Date(v*1000):new Date(v);return Number.isFinite(t.getTime())?t.toISOString():null;}
async function readJson(url){const r=await fetch(url,{headers:{"accept":"application/json","user-agent":"AI30 Topic Radar/3.2 research metadata"},redirect:"follow",signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error("http_"+r.status);const size=r.headers.get("content-length");if(size&&Number(size)>1500000)throw Error("json_too_large");const t=await r.text();if(t.length>1500000)throw Error("json_too_large");return JSON.parse(t);}
function isHttps(url){return typeof url==="string"&&url.startsWith("https://")?canonical(url):""}
function metric(n){return Number.isFinite(n)&&n>=0?n:null}
function item({url,title,excerpt="",author="",published=null,metrics=null,scope="public_metadata",project_url=""}){
 const u=isHttps(url);if(!u||!String(title||"").trim())return null;
 const observed={};if(metrics&&typeof metrics==="object"){for(const k of ["points","comments","likes","bookmarks","views","reposts"]){const n=metric(metrics[k]);if(n!==null)observed[k]=n}}
 return {url:u,title:String(title).trim().slice(0,450),excerpt:String(excerpt||"").slice(0,900),author:String(author||"").slice(0,100),date:cleanDate(published),metrics:observed,scope,project_url:isHttps(project_url)};
}
async function getFromSource(src){
 if(!["hn_json","devto_json","v2ex_json","hf_json","lobsters_json","github_mirror_json"].includes(src.kind)){
  const out=await capFetch(src.feed_url);return{status:out.status,items:out.items.map(z=>item({url:z.url,title:z.title,excerpt:z.excerpt,author:z.author,published:z.date,scope:"rss_title_excerpt_only"})).filter(Boolean).slice(0,12)}
 }
 const data=await readJson(src.feed_url);const things=[];
 if(src.kind==="hn_json"){if(!Array.isArray(data))throw Error("hn_list_invalid");const ids=data.filter(n=>Number.isInteger(n)&&n>0).slice(0,6);const results=await Promise.allSettled(ids.map(n=>readJson("https://hacker-news.firebaseio.com/v0/item/"+n+".json")));
 for(let i=0;i<ids.length;i++){const row=results[i].status==="fulfilled"?results[i].value:null;if(!row||row.deleted||row.dead)continue;things.push(item({url:"https://news.ycombinator.com/item?id="+ids[i],title:row.title,author:row.by,published:row.time,metrics:{points:row.score,comments:row.descendants},scope:"hackernews_native_metrics",project_url:isHttps(row.url)&&new URL(row.url).hostname==="github.com"?row.url:""}));}}
 if(src.kind==="devto_json"){if(!Array.isArray(data))throw Error("devto_invalid");for(const row of data.slice(0,12))things.push(item({url:row.url,title:row.title,excerpt:row.description,author:row.user?.username,published:row.published_at,metrics:{comments:row.comments_count,likes:row.positive_reactions_count},scope:"devto_native_metrics"}));}
 if(src.kind==="v2ex_json"){if(!Array.isArray(data))throw Error("v2ex_invalid");for(const row of data.slice(0,12))things.push(item({url:row.url,title:row.title,excerpt:row.content_rendered||"",author:row.member?.username,published:row.created,metrics:{comments:row.replies},scope:"v2ex_native_metrics"}));}
 if(src.kind==="hf_json"){if(!Array.isArray(data))throw Error("hf_invalid");for(const row of data.slice(0,12))things.push(item({url:"https://huggingface.co/spaces/"+row.id,title:row.cardData?.title||row.id,excerpt:row.cardData?.short_description||"",author:row.author,published:row.createdAt||row.lastModified,metrics:{likes:row.likes},scope:"huggingface_native_metrics",project_url:"https://huggingface.co/spaces/"+row.id}));}
 if(src.kind==="lobsters_json"){if(!Array.isArray(data))throw Error("lobsters_invalid");for(const row of data.slice(0,12))things.push(item({url:row.short_id_url||row.comments_url,title:row.title,author:row.submitter_user?.username,published:row.created_at,metrics:{points:row.score,comments:row.comment_count},scope:"lobsters_native_metrics"}));}
 if(src.kind==="github_mirror_json"){const rows=Array.isArray(data)?data:data?.items;if(!Array.isArray(rows))throw Error("github_mirror_invalid");for(const row of rows.slice(0,12))things.push(item({url:row.url,title:row.title||row.name,excerpt:row.description,scope:"third_party_trending_unverified",project_url:row.url}));}
 return{status:200,items:things.filter(Boolean)};
}
function entityIdentity(row){
 const u=new URL(row.project_url||row.url);const parts=u.pathname.split("/").filter(Boolean);
 if(u.hostname==="github.com"&&parts.length===2)return"project:github:"+parts[0].toLowerCase()+"/"+parts[1].toLowerCase();
 if(u.hostname==="huggingface.co"&&parts[0]==="spaces"&&parts.length===3)return"project:hf:"+parts.slice(0,3).join("/").toLowerCase();
 return"post:"+row.url;
}
function lanesOf(title){
 const t=String(title||"").toLowerCase();const out=[];
 if(/合集|清单|资源库|awesome|collection|directory|resources|prompts|skills\b/.test(t))out.push("resource_collection");
 if(/教程|实操|如何|工作流|how to|tutorial|guide|workflow|walkthrough/.test(t))out.push("tutorial_workflow");
 if(/演示|视频|镜头|成片|视觉|动效|动画|demo|showcase|before.?after|rendered|animation/.test(t))out.push("creator_demonstration_unviewed");
 if(/开源|发布|上线|new version|released|launch|introduc|open.source/.test(t))out.push("tool_launch");
 return out.length?out:["unclassified_research"];
}
const NINE_VALUE_SCAN={utility:"not_assessed",learning:"not_assessed",save:"not_assessed",decision:"not_assessed",insight:"not_assessed",information:"not_assessed",emotion:"not_assessed",entertainment:"not_assessed",social_expression:"not_assessed"};
async function persist(env,src,row,now){
 const ekey=entityIdentity(row);const prev=await env.DB.prepare("SELECT source_ids_json FROM entities WHERE entity_key=?").bind(ekey).first();
 let families=[];try{families=JSON.parse(prev?.source_ids_json||"[]");if(!Array.isArray(families))families=[]}catch{families=[]}
 if(!families.includes(src.source_id))families.push(src.source_id);
 const prior=await env.DB.prepare("SELECT first_seen_utc FROM evidence WHERE source_id=? AND canonical_url=?").bind(src.source_id,row.url).first();
 await env.DB.prepare("INSERT INTO evidence(source_id,canonical_url,original_url,title,excerpt,author,published_utc,first_seen_utc,last_seen_utc,source_scope,observed_metrics_json,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id,canonical_url) DO UPDATE SET title=excluded.title,excerpt=excluded.excerpt,last_seen_utc=excluded.last_seen_utc,observed_metrics_json=excluded.observed_metrics_json,raw_json=excluded.raw_json").bind(src.source_id,row.url,row.url,row.title,row.excerpt,row.author,row.date,prior?.first_seen_utc||now,now,row.scope,JSON.stringify({metrics:row.metrics,scope:METRIC_SCOPE,checked_at:now}),JSON.stringify({url:row.url,title:row.title,excerpt:row.excerpt,project_url:row.project_url,lanes:lanesOf(row.title)})).run();
 if(prev)await env.DB.prepare("UPDATE entities SET last_seen_utc=?,title=?,source_ids_json=?,cross_source_count=? WHERE entity_key=?").bind(now,row.title,JSON.stringify(families),families.length,ekey).run();
 else await env.DB.prepare("INSERT INTO entities(entity_key,canonical_url,title,first_seen_utc,last_seen_utc,cross_source_count,source_ids_json,state) VALUES(?,?,?,?,?,?,?,'research_only')").bind(ekey,row.url,row.title,now,now,1,JSON.stringify(families)).run();
 await env.DB.prepare("INSERT OR IGNORE INTO editorial_review(entity_key,value_scan_json,original_review_status,updated_utc) VALUES(?,?,'pending',?)").bind(ekey,JSON.stringify(NINE_VALUE_SCAN),now).run();
 return !prev;
}
async function processRun(env,trigger){
 const started=new Date().toISOString(),run_id=crypto.randomUUID();
 await env.DB.prepare("INSERT INTO runs(run_id,trigger_kind,started_utc,status,provenance_commit) VALUES(?, ?, ?, 'running', ?)").bind(run_id,trigger,started,BASE_COMMIT).run();
 const sources=(await env.DB.prepare("SELECT source_id,name,feed_url,kind FROM sources WHERE enabled=1 ORDER BY coalesce(last_checked_utc,''), priority DESC, source_id LIMIT 4").all()).results||[];
 let checked=0,found=0,added=0,failures=[];
 for(const src of sources){let status="retrieved",http=200,rows=[];
 try{const res=await getFromSource(src);http=res.status;rows=res.items;if(!rows.length)status="empty_or_unparsed";
 for(const entry of rows){const isNew=await persist(env,src,entry,new Date().toISOString());if(isNew)added++;}
 found+=rows.length;}catch(e){status="failed";http=null;failures.push({source_id:src.source_id,error:String(e).slice(0,160)});}
 checked++;const timestamp=new Date().toISOString();
 await env.DB.prepare("INSERT INTO run_source_health(run_id,source_id,status,http_status,item_count,error_text,checked_utc) VALUES(?,?,?,?,?,?,?)").bind(run_id,src.source_id,status,http,rows.length,status==="failed"?failures.at(-1)?.error:null,timestamp).run();
 await env.DB.prepare("UPDATE sources SET last_checked_utc=?,last_result=? WHERE source_id=?").bind(timestamp,status,src.source_id).run();
 }
 await env.DB.prepare("UPDATE runs SET finished_utc=?,status=?,feeds_checked=?,retrieved=?,new_entities=?,errors_json=? WHERE run_id=?").bind(new Date().toISOString(),failures.length?"partial":"complete",checked,found,added,JSON.stringify(failures),run_id).run();
 return {run_id,checked,found,added,failed:failures.length,publication_approved:0};
}
async function inspect(env){const [src,ev,ent,run,pending]=await Promise.all([
 env.DB.prepare("SELECT COUNT(*) AS n,SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END) AS live FROM sources").first(),
 env.DB.prepare("SELECT COUNT(*) AS n FROM evidence").first(),
 env.DB.prepare("SELECT COUNT(*) AS n FROM entities").first(),
 env.DB.prepare("SELECT run_id,status,started_utc,feeds_checked,retrieved,new_entities FROM runs ORDER BY started_utc DESC LIMIT 1").first(),
 env.DB.prepare("SELECT COUNT(*) AS n FROM editorial_review WHERE original_review_status='pending'").first()
 ]);return{sources:src?.n,enabled_sources:src?.live,disabled_seed_sources:(src?.n||0)-(src?.live||0),evidence:ev?.n,entities:ent?.n,unreviewed:pending?.n,last_run:run||null}}
async function selfTest(){const fixture='<rss><channel><item><title>A&amp;B AI tutorial</title><link>https://example.org/a?utm_source=tracker</link><description>Short demo</description></item></channel></rss>';const parsed=rssList(fixture);const n=parsed[0]&&item({url:parsed[0].url,title:parsed[0].title,excerpt:parsed[0].excerpt});const key=n?entityIdentity(n):null;return{pass:parsed.length===1&&n?.title==="A&B AI tutorial"&&key==="post:https://example.org/a"&&Object.keys(NINE_VALUE_SCAN).length===9,fixture_count:parsed.length,normalized_url:n?.url,review_initial_state:"not_assessed",automatic_approval:false}}
export default{
 async fetch(request,env){const u=new URL(request.url);if(request.method!=="GET")return json({error:"read_only_http",automatic_posting:false},405);
 if(u.pathname==="/"||u.pathname==="/health"){try{return json({name:"30天图文账号 Cloudflare V3.2 source migration",version:"v3.2-cf-migration-phase2",source_commit:BASE_COMMIT,stage:"controlled_staging",automation_enabled:env.ENABLE_COLLECTION==="true",publication_auto_approved:false,manual_publish_only:true,db:await inspect(env)});}catch(e){return json({status:"db_error",detail:String(e).slice(0,160)},503)}}
 if(u.pathname==="/self-test")return json(await selfTest());
 if(u.pathname==="/readiness")return json({full_parity:false,implemented:["24 original RSS feeds","11 additional public discovery channels","38 AICG and X seed-only entries disabled","source-by-source errors","D1 durable evidence, URL/project dedupe","nine-value unassessed placeholders","human editorial queue"],missing:["native X global search (historically failed)","X creator content collector","AICG original-image viewing and quality gate","domestic Douyin/XHS native access","Python advanced editorial/copy gates port","verified historical parity against all 119 tests"],publication_approved:0,production_autopublish:false});
 if(u.pathname==="/coverage"){const data=(await env.DB.prepare("SELECT kind,enabled,COUNT(*) AS n,SUM(CASE WHEN last_result='retrieved' THEN 1 ELSE 0 END) AS last_success,SUM(CASE WHEN last_result='failed' THEN 1 ELSE 0 END) AS last_failed FROM sources GROUP BY kind,enabled ORDER BY kind").all()).results;return json({basis:"registered sources, not all verified accessible",sources:data,metric_scope:METRIC_SCOPE});}
 return json({error:"not_found"},404);
 },
 async scheduled(event,env,ctx){if(env.ENABLE_COLLECTION!=="true")return;ctx.waitUntil(processRun(env,"cf_cron_incremental"));}
};