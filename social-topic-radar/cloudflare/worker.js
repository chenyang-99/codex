const BASE_COMMIT="24a8413586fdc58276df2fb5e2b8a6b769161c3c";
const VERSION="v3.2-cf-migration-phase4";
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
 if(!["hn_json","devto_json","v2ex_json","hf_json","hf_models_json","hf_spaces_recent_json","lobsters_json","github_mirror_json"].includes(src.kind)){
  const out=await capFetch(src.feed_url);return{status:out.status,items:out.items.map(z=>item({url:z.url,title:z.title,excerpt:z.excerpt,author:z.author,published:z.date,scope:src.kind==="indexed_rss"?"public_search_index_only_not_native_platform_posts":"rss_title_excerpt_only"})).filter(Boolean).slice(0,12)}
 }
 const data=await readJson(src.feed_url);const things=[];
 if(src.kind==="hn_json"){if(!Array.isArray(data))throw Error("hn_list_invalid");const ids=data.filter(n=>Number.isInteger(n)&&n>0).slice(0,6);const results=await Promise.allSettled(ids.map(n=>readJson("https://hacker-news.firebaseio.com/v0/item/"+n+".json")));
 for(let i=0;i<ids.length;i++){const row=results[i].status==="fulfilled"?results[i].value:null;if(!row||row.deleted||row.dead)continue;things.push(item({url:"https://news.ycombinator.com/item?id="+ids[i],title:row.title,author:row.by,published:row.time,metrics:{points:row.score,comments:row.descendants},scope:"hackernews_native_metrics",project_url:isHttps(row.url)&&new URL(row.url).hostname==="github.com"?row.url:""}));}}
 if(src.kind==="devto_json"){if(!Array.isArray(data))throw Error("devto_invalid");for(const row of data.slice(0,12))things.push(item({url:row.url,title:row.title,excerpt:row.description,author:row.user?.username,published:row.published_at,metrics:{comments:row.comments_count,likes:row.positive_reactions_count},scope:"devto_native_metrics"}));}
 if(src.kind==="v2ex_json"){if(!Array.isArray(data))throw Error("v2ex_invalid");for(const row of data.slice(0,12))things.push(item({url:row.url,title:row.title,excerpt:row.content_rendered||"",author:row.member?.username,published:row.created,metrics:{comments:row.replies},scope:"v2ex_native_metrics"}));}
 if(src.kind==="hf_json"){if(!Array.isArray(data))throw Error("hf_invalid");for(const row of data.slice(0,12))things.push(item({url:"https://huggingface.co/spaces/"+row.id,title:row.cardData?.title||row.id,excerpt:row.cardData?.short_description||"",author:row.author,published:row.createdAt||row.lastModified,metrics:{likes:row.likes},scope:"huggingface_native_metrics",project_url:"https://huggingface.co/spaces/"+row.id}));}
 
 if(src.kind==="hf_models_json"||src.kind==="hf_spaces_recent_json"){
  if(!Array.isArray(data))throw Error("huggingface_data_not_array");
  const visualTerms=["image","photo","video","visual","comfy","flux","wan","cinema","3d","seedance","anime","draw","portrait","motion","edit","recraft","kling","diffusion"];
  for(const row of data.slice(0,50)){if(!row||typeof row!=="object"||row.private===true)continue;
   const id=String(row.id||row.modelId||"");if(!/^[^/]+\/[^/]+$/.test(id))continue;
   const tags=Array.isArray(row.tags)?row.tags.slice(0,20):[];
   if(src.kind==="hf_spaces_recent_json"&&!visualTerms.some(term=>(id+" "+tags.join(" ")).toLowerCase().includes(term)))continue;
   const u="https://huggingface.co/"+(src.kind==="hf_spaces_recent_json"?"spaces/":"")+id;
   const notes="Official Hugging Face public metadata; tags: "+tags.join(", ").slice(0,360);
   things.push(item({url:u,title:id,excerpt:notes,author:id.split("/")[0],published:row.createdAt||null,scope:"huggingface_first_party_aicg_metadata_not_original_media_viewed",project_url:u,metrics:{likes:row.likes}}));
   if(things.length>=12)break;
  }
 }

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

const VALUE_PROOF_FIELDS_CF={utility:["task_input","deliverable_example","success_check"],learning:["teachable_skill","steps_and_prerequisites","learner_verification"],save:["reusable_asset","access_conditions","reuse_scenario"],decision:["options_compared","tradeoffs","decision_rule"],insight:["prior_understanding","new_interpretation","supporting_observation"],information:["new_fact","event_date","reader_impact"],emotion:["specific_story","emotional_turn","audience_connection"],entertainment:["actually_viewed_work","standout_moment","experience_reason"],social_expression:["discussion_question","grounded_positions","reason_to_express"]};
const LEGACY_SCORE_CAPS={attraction:25,spread:30,payoff:30,credibility:15},LEGACY_SCORE_MINS={attraction:20,spread:23,payoff:21,credibility:10};
const LEGACY_VALUE_LABELS={utility:"实用",learning:"学习",save:"收藏",decision:"决策",insight:"认知",information:"信息",emotion:"情绪",entertainment:"审美娱乐",social_expression:"社交表达"};
function auditLegacyTopic(topic){
 const t=topic&&typeof topic==="object"?topic:{},errors=[],need=(obj,fields,pre)=>{for(const key of fields)if(typeof obj?.[key]!=="string"||!obj[key].trim())errors.push(pre+key)};
 need(t,["topic_id","problem_key","title","audience","trigger","job","outcome","angle","promise","proof_plan","competitor_gap","difference_rationale","source_limitations"],"missing_");
 if(!Object.values(LEGACY_VALUE_LABELS).includes(t.value_type))errors.push("missing_or_invalid_value_type");
 if(t.requires_test&&!t.test_gap)errors.push("missing_preproduction_test_gap");
 const cv=t.content_values&&typeof t.content_values==="object"?t.content_values:{};
 need(cv,["attraction","spread_mechanism","payoff_description"],"missing_content_value_");
 const payoff=cv.payoff_type;if(!Object.keys(LEGACY_VALUE_LABELS).includes(payoff))errors.push("missing_or_invalid_payoff_type");
 if(!["verified_viral","fresh_potential"].includes(cv.spread_class))errors.push("missing_or_unverified_spread_class");
 if(!canonical(cv.spread_source_url))errors.push("missing_spread_primary_source");
 if(cv.spread_class==="verified_viral")need(cv,["spread_metric","spread_checked_at"],"missing_verified_");
 if(cv.spread_class==="fresh_potential")need(cv,["original_published_at","freshness_reason"],"missing_");
 const scores=t.content_scores;
 if(!scores||typeof scores!=="object")errors.push("missing_content_scores");
 else if(Object.entries(LEGACY_SCORE_CAPS).some(([k,cap])=>typeof scores[k]!=="number"||!Number.isFinite(scores[k])||scores[k]<0||scores[k]>cap))errors.push("invalid_content_scores");
 else {for(const [k,min] of Object.entries(LEGACY_SCORE_MINS))if(scores[k]<min)errors.push("content_score_below_minimum_"+k);if(Object.keys(LEGACY_SCORE_CAPS).reduce((sum,k)=>sum+scores[k],0)<85)errors.push("content_score_total_below_85");if(!t.score_evidence||Object.keys(LEGACY_SCORE_CAPS).some(k=>!String(t.score_evidence[k]||"").trim()))errors.push("missing_score_evidence_by_dimension")}
 const scan=t.value_scan&&typeof t.value_scan==="object"?t.value_scan:null;
 if(!scan)errors.push("missing_nine_value_scan");
 else{for(const k of Object.keys(LEGACY_VALUE_LABELS))if(!["primary","secondary","not_applicable"].includes(scan[k]))errors.push("missing_or_invalid_value_scan_"+k);if(Object.keys(scan).some(k=>!(k in LEGACY_VALUE_LABELS)))errors.push("unknown_value_scan_dimension");const primary=Object.keys(LEGACY_VALUE_LABELS).filter(k=>scan[k]==="primary");if(primary.length!==1)errors.push("nine_value_scan_requires_one_primary");if(primary.length===1&&primary[0]!==payoff)errors.push("primary_value_mismatch")}
 if(t.value_type!==LEGACY_VALUE_LABELS[payoff])errors.push("chinese_value_label_mismatch");
 const proof=t.value_proof;if(!proof||typeof proof!=="object")errors.push("missing_value_proof");
 else{need(proof,["observed_material","reader_deliverable","verification_check","limitations"],"missing_value_proof_");if(!["source_reviewed","independently_tested"].includes(proof.evidence_status))errors.push("unverified_value_evidence");if(!["original_read","original_viewed","official_document_read","independently_tested"].includes(proof.source_access))errors.push("unverified_value_source_access");const linked=canonical(proof.source_url);if(!linked)errors.push("missing_value_proof_source_url");else if(!(t.signals||[]).some(s=>canonical(s?.url)===linked))errors.push("unlinked_value_proof_source");if(!proof.category_evidence||typeof proof.category_evidence!=="object")errors.push("missing_category_value_evidence");else need(proof.category_evidence,VALUE_PROOF_FIELDS_CF[payoff]||[],"missing_value_"+payoff+"_");if(payoff==="entertainment"&&!["original_viewed","independently_tested"].includes(proof.source_access))errors.push("visual_work_not_viewed")}
 const pitch=t.social_pitch;if(!pitch||typeof pitch!=="object")errors.push("missing_social_pitch");
 else{if(!["x","xiaohongshu","douyin"].includes(pitch.platform))errors.push("missing_target_platform");need(pitch,["first_screen","proof_object","why_share_or_save","account_fit","support_observation"],"missing_social_");if(!["own_post","same_platform_post","original_work"].includes(pitch.support_type))errors.push("missing_or_invalid_social_support_type");if(!canonical(pitch.support_url))errors.push("missing_social_support_url");if(["own_post","same_platform_post"].includes(pitch.support_type))need(pitch,["support_metric","support_checked_at"],"missing_social_");if(pitch.support_type==="original_work")need(pitch,["original_published_at","editorial_hypothesis"],"missing_social_")}
 const signals=Array.isArray(t.signals)?t.signals:[];const valid=signals.filter(s=>s&&canonical(s.url)&&["user_post","user_comment","official_release","original_case"].includes(s.kind)&&s.read_scope&&!["search_snippet_only","headline_only","unavailable","unknown"].includes(s.read_scope)&&((["user_post","user_comment"].includes(s.kind)&&s.quote)||(s.kind==="official_release"&&s.claim)||(s.kind==="original_case"&&s.observed_result)));
 if(valid.length===0){errors.push("no_recheckable_primary_evidence");errors.push("no_direct_user_official_or_original_evidence");errors.push("no_independent_source_context")}
 return{status:errors.length?"blocked":"manual_editorial_review_required",blocking_reasons:[...new Set(errors)],machine_approval:false,human_editorial_approval:false,user_approved:false,published:false,contract:"original_python_topic_quality_gate_v3.2_structural_subset",notice:"Source truth, 85pt editorial evidence, actual artwork viewing and final content judgement require a human. Even zero blockers is not publishing authorization."};
}


function xConservativeLength(body){
 const normalized=String(body||"").replace(/https?:\/\/[^\s<>\u3000]+/gi,"\uFFF0");
 return [...normalized].reduce((sum,ch)=>sum+(ch==="\uFFF0"?23:ch.codePointAt(0)<128?1:2),0);
}
function qaSyntheticFixture(){
 const url="https://example.org/original";
 const scans=Object.fromEntries(Object.keys(LEGACY_VALUE_LABELS).map(key=>[key,key==="learning"?"primary":"not_applicable"]));
 return {
 topic_id:"synthetic",problem_key:"one-task",title:"Reproducible AI example",audience:"AI learners",trigger:"new workflow",job:"learn method",outcome:"replicable output",angle:"source-led tutorial",promise:"tested workflow",proof_plan:"check original documents",competitor_gap:"others skip limitations",difference_rationale:"verified key steps",source_limitations:"example only",value_type:"学习",
 content_values:{attraction:"Specific first-screen value",spread_mechanism:"Learnable resource",payoff_description:"Reusable skill",payoff_type:"learning",spread_class:"fresh_potential",spread_source_url:url,original_published_at:"2026-10-24T00:00:00Z",freshness_reason:"new official source"},
 content_scores:{attraction:22,spread:25,payoff:25,credibility:14},score_evidence:{attraction:"Original useful entry",spread:"Shareable worked steps",payoff:"Reusable method",credibility:"Direct original reference"},
 value_scan:scans,
 value_proof:{observed_material:"documentation observed",reader_deliverable:"repeatable steps",verification_check:"expected output",limitations:"synthetic only",evidence_status:"source_reviewed",source_access:"official_document_read",source_url:url,category_evidence:{teachable_skill:"study method",steps_and_prerequisites:"setup and tools",learner_verification:"compare result"}},
 social_pitch:{platform:"x",first_screen:"source-backed learning example",proof_object:"original documented workflow",why_share_or_save:"reusable how-to",account_fit:"educational AI use",support_observation:"fictional test only",support_type:"original_work",support_url:url,original_published_at:"2026-10-24",editorial_hypothesis:"likely useful to learners"},
 signals:[{url,kind:"official_release",read_scope:"official_read",claim:"documented method for this purely synthetic example"}]
 };
}

async function persist(env,src,row,now){
 const ekey=entityIdentity(row);const prev=await env.DB.prepare("SELECT source_ids_json FROM entities WHERE entity_key=?").bind(ekey).first();
 let families=[];try{families=JSON.parse(prev?.source_ids_json||"[]");if(!Array.isArray(families))families=[]}catch{families=[]}
 if(!families.includes(src.source_id))families.push(src.source_id);
 const prior=await env.DB.prepare("SELECT first_seen_utc FROM evidence WHERE source_id=? AND canonical_url=?").bind(src.source_id,row.url).first();
 await env.DB.prepare("INSERT INTO evidence(source_id,canonical_url,original_url,title,excerpt,author,published_utc,first_seen_utc,last_seen_utc,source_scope,observed_metrics_json,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id,canonical_url) DO UPDATE SET title=excluded.title,excerpt=excluded.excerpt,last_seen_utc=excluded.last_seen_utc,observed_metrics_json=excluded.observed_metrics_json,raw_json=excluded.raw_json").bind(src.source_id,row.url,row.url,row.title,row.excerpt,row.author,row.date,prior?.first_seen_utc||now,now,row.scope,JSON.stringify({metrics:row.metrics,scope:METRIC_SCOPE,checked_at:now}),JSON.stringify({url:row.url,title:row.title,excerpt:row.excerpt,project_url:row.project_url,lanes:lanesOf(row.title)})).run();
 if(prev)await env.DB.prepare("UPDATE entities SET last_seen_utc=?,title=?,source_ids_json=?,cross_source_count=? WHERE entity_key=?").bind(now,row.title,JSON.stringify(families),families.length,ekey).run();
 else await env.DB.prepare("INSERT INTO entities(entity_key,canonical_url,title,first_seen_utc,last_seen_utc,cross_source_count,source_ids_json,state) VALUES(?,?,?,?,?,?,?,'research_only')").bind(ekey,row.url,row.title,now,now,1,JSON.stringify(families)).run();
 await env.DB.prepare("INSERT OR IGNORE INTO editorial_review(entity_key,value_scan_json,original_review_status,updated_utc) VALUES(?,?,'pending',?)").bind(ekey,JSON.stringify(NINE_VALUE_SCAN),now).run();
 await env.DB.prepare("UPDATE editorial_review SET machine_blockers_json=? WHERE entity_key=? AND original_review_status='pending'").bind(JSON.stringify(auditLegacyTopic({title:row.title,signals:[{url:row.url,read_scope:row.scope}]}).blocking_reasons),ekey).run();
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
 if(u.pathname==="/"||u.pathname==="/health"){try{return json({name:"30天图文账号 Cloudflare V3.2 source migration",version:"v3.2-cf-migration-phase4",source_commit:BASE_COMMIT,stage:"controlled_staging",automation_enabled:env.ENABLE_COLLECTION==="true",publication_auto_approved:false,manual_publish_only:true,db:await inspect(env)});}catch(e){return json({status:"db_error",detail:String(e).slice(0,160)},503)}}
 if(u.pathname==="/self-test")return json(await selfTest());
 if(u.pathname==="/quality-self-test"){
 const empty=auditLegacyTopic({}),headline=auditLegacyTopic({title:"Headline-only",signals:[{url:"https://example.org/post",read_scope:"headline_only"}]});
 const example=qaSyntheticFixture(),complete=auditLegacyTopic(example);
 const low=auditLegacyTopic({...example,content_scores:{...example.content_scores,payoff:22}});
 const artistic=auditLegacyTopic({...example,value_type:"审美娱乐",content_values:{...example.content_values,payoff_type:"entertainment"},value_scan:Object.fromEntries(Object.keys(LEGACY_VALUE_LABELS).map(k=>[k,k==="entertainment"?"primary":"not_applicable"])),value_proof:{...example.value_proof,source_access:"original_read",category_evidence:{actually_viewed_work:"sample artwork",standout_moment:"sample shot",experience_reason:"sample expression"}}});
 const checks={no_evidence_blocked:empty.status==="blocked"&&headline.blocking_reasons.includes("no_recheckable_primary_evidence"),synthetic_complete_structure_needs_human:complete.blocking_reasons.length===0&&complete.status==="manual_editorial_review_required"&&complete.machine_approval===false,score_below_85_blocked:low.blocking_reasons.includes("content_score_total_below_85"),unviewed_aicg_blocked:artistic.blocking_reasons.includes("visual_work_not_viewed"),x_length_limit:xConservativeLength("你".repeat(141))>280&&xConservativeLength("你好")===4&&xConservativeLength("https://example.org")===23};
 return json({pass:Object.values(checks).every(Boolean),checks,checks_count:Object.keys(checks).length,automatic_publication:false,limitation:"Static fixtures do not prove complete Python test parity or human visual review."});
}

 if(u.pathname==="/readiness")return json({full_parity:false,runtime:"CF_only",configured_source_categories:["24 originally configured RSS sources; one paused after invalid 404","11 original public community, hot and video metadata adapters","six free Google News indirect site-index discovery feeds (not original posts)","three Hugging Face first-party AICG model/Spaces metadata streams","38 X creator/AICG website seeds disabled unless legally verified"],implemented:["persistent D1 source/evidence/entity datasets","per-source HTTP success, empty and failure receipts","canonical URL and project-level across-day dedup","private queryable editorial review queue","structural nine-reader-value and four-score gate with manual veto","original X 280 weighted-char conservative format check","positive, negative, incomplete and visual-unviewed fixture tests"],missing:["global original X keyword and AICG author content collector","original media playback and visual quality acceptance","original native Douyin and Xiaohongshu search/comments","full 119 original Python quality regressions inside CF","original copy P0 full release gate running on CF rather than ChatGPT editorial skill","actual human-reviewed and approved content delivery"],publication_approved:0,production_autopublish:false,capability_status:"partial_functionality_validated_not_full_parity"});
 if(u.pathname==="/quality-contract")return json({status:"metadata_and_human_gated",score_caps:LEGACY_SCORE_CAPS,score_minima:LEGACY_SCORE_MINS,total_required:85,dimensions:LEGACY_VALUE_LABELS,required_primary_count:1,original_source_required:true,social_pitch_required:true,human_editorial_approval:true,visual_originals_must_be_seen:true,copy_delivery_10_p0_gate:"ChatGPT ai-copy-production v3.1 original skill / release_gate.py; not executed on Cloudflare",automatic_publishing:false});
 if(u.pathname==="/coverage"){const data=(await env.DB.prepare("SELECT kind,enabled,COUNT(*) AS n,SUM(CASE WHEN last_result='retrieved' THEN 1 ELSE 0 END) AS last_success,SUM(CASE WHEN last_result='failed' THEN 1 ELSE 0 END) AS last_failed FROM sources GROUP BY kind,enabled ORDER BY kind").all()).results;return json({basis:"registered sources, not all verified accessible",sources:data,metric_scope:METRIC_SCOPE});}
 return json({error:"not_found"},404);
 },
 async scheduled(event,env,ctx){if(env.ENABLE_COLLECTION!=="true")return;ctx.waitUntil(processRun(env,"cf_cron_incremental"));}
};