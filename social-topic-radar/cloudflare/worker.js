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
function item({url,title,excerpt="",author="",published=null,metrics=null,scope="public_metadata",project_url="",preview_image=""}){
 const u=isHttps(url);if(!u||!String(title||"").trim())return null;
 const observed={};if(metrics&&typeof metrics==="object"){for(const k of ["points","comments","likes","bookmarks","views","reposts"]){const n=metric(metrics[k]);if(n!==null)observed[k]=n}}
 return {url:u,title:String(title).trim().slice(0,450),excerpt:String(excerpt||"").slice(0,900),author:String(author||"").slice(0,100),date:cleanDate(published),metrics:observed,scope,project_url:isHttps(project_url),preview_image:isHttps(preview_image)};
}

const AICG_SITE_RULES={
 "ComfyUI Workflows":{host:"comfy.org",path:/^\/workflows\/[a-f0-9-]{12,}\/?$/i},
 "Runway Academy":{host:"academy.runway.com",path:/^\/courses\/[^/]+\/?$/i},
 "Luma Learning Center":{host:"lumalabs.ai",path:/^\/learning-center\/[^/]+\/?$/i},
 "Replicate Collections":{host:"replicate.com",path:/^\/collections\/[^/]+\/?$/i},
 "Recraft Blog":{host:"www.recraft.ai",path:/^\/blog\/[^/]+\/?$/i},
 "Google DeepMind Blog":{host:"deepmind.google",path:/^\/blog\/[^/]+\/?$/i},
 "Black Forest Labs Blog":{host:"bfl.ai",path:/^\/blog\/[^/]+\/?$/i},
 "Higgsfield Community":{host:"higgsfield.ai",path:/^\/community\/[a-z0-9/_-]+\/?$/i},
 "Krea Community Apps":{host:"www.krea.ai",path:/^\/apps\/(?!community|background-remover)[a-z0-9/_-]+\/?$/i},
 "Runway AI Festival":{host:"aif.runwayml.com",path:/^\/(?:films|film|projects|winners)\/[^/]+\/?$/i}
};
async function htmlMetadata(url){
 const response=await fetch(url,{headers:{"user-agent":"AI30 Topic Radar/3.2 public metadata (no login)","accept":"text/html"},redirect:"follow",signal:AbortSignal.timeout(10000)});
 if(!response.ok)throw Error("http_"+response.status);
 if(!String(response.headers.get("content-type")||"").includes("html"))throw Error("not_html");
 if(!response.body)throw Error("html_body_not_streamed");
 const reader=response.body.getReader(),pieces=[];let n=0;
 try{
  while(n<360000){const v=await reader.read();if(v.done)break;if(!v.value||!v.value.length)continue;const part=v.value.subarray(0,360000-n);pieces.push(part);n+=part.length;}
 }finally{try{await reader.cancel()}catch{}}
 const buf=new Uint8Array(n);let offset=0;for(const p of pieces){buf.set(p,offset);offset+=p.length}
 return new TextDecoder("utf-8",{fatal:false}).decode(buf);
}

function pageMeta(html){
 const meta=(key)=>{const tag=html.match(new RegExp('<meta\\b(?=[^>]*(?:name|property)\\s*=\\s*["\\x27]'+key.replace(/:/g,"\\:")+'["\\x27])[^>]*>','i'));if(!tag)return"";const c=tag[0].match(/\bcontent\s*=\s*["']([^"']*)["']/i);return c?xmlDecode(c[1]).slice(0,750):""};
 const title=meta("og:title")||xmlDecode((html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)||[])[1]||"");
 return{title:title.slice(0,420),description:meta("og:description")||meta("description"),date:meta("article:published_time")||meta("datePublished")||null,has_og_image:!!meta("og:image"),preview_image:meta("og:image")};
}
async function getAicgSiteDetails(src){
 const spec=AICG_SITE_RULES[src.name];if(!spec)throw Error("source_not_whitelisted");
 const root=new URL(src.feed_url);if(root.protocol!=="https:"||root.hostname!==spec.host)throw Error("source_root_host_mismatch");
 const html=await htmlMetadata(src.feed_url),urls=[];
 const anchors=html.matchAll(/<a\b[^>]*\bhref\s*=\s*(?:"([^"]+)"|'([^']+)')/gi);
 for(const m of anchors){const ref=(m[1]||m[2]||"").replace(/&amp;/g,"&");let u;try{u=new URL(ref,root)}catch{continue}if(u.protocol!=="https:"||u.hostname!==spec.host||!spec.path.test(u.pathname))continue;u.search="";u.hash="";if(!urls.includes(u.toString()))urls.push(u.toString());if(urls.length>=3)break}
 const results=await Promise.allSettled(urls.map(async u=>{const html=await htmlMetadata(u),p=pageMeta(html);return p.title?item({url:u,title:p.title,excerpt:p.description+(p.has_og_image?"; OG image metadata only; artwork not viewed":""),published:p.date,scope:"first_party_public_aicg_detail_metadata_not_media_or_rights_verified",project_url:u,preview_image:p.preview_image}):null}));
 return{status:200,items:results.filter(x=>x.status==="fulfilled"&&x.value).map(x=>x.value)};
}

async function getFromSource(src){
 if(src.kind==="aicg_site_html")return await getAicgSiteDetails(src);
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


const COPY_P0_GATES=["audience_promise","primary_payoff","original_angle","specificity_and_completeness","truth_and_provenance","structure_and_pacing","natural_voice","platform_publishability","delivery_package","rights_and_authorization"];
const COPY_ANCHORED=new Set(["audience_promise","primary_payoff","original_angle","specificity_and_completeness","structure_and_pacing","natural_voice"]);
const COPY_EXTERNAL=new Set(["tool","news","review","benchmark","tutorial","technical","policy"]);
const COPY_PLATFORMS=new Set(["x","xiaohongshu","douyin","multi"]);
const COPY_X_FORMS=new Set(["short_text","image_post","thread","long_post","article"]);
const COPY_URL_RE=/https?:\/\/[^\s<>\u3000]+/gi;
const COPY_PLACEHOLDER=/\[(?:待补|待填|插入图片|这里放|TODO|待核)[^\]]{0,30}\]|【(?:此处插|待补|待填)[^】]{0,30}】|<\s*(?:insert|replace|placeholder)\s*>|待补链接|待核实后补上/i;
const COPY_BAIT=/(?:评论区(?:打|扣)(?:1|666)|点赞收藏关注三连)/;
function copyText(value){return typeof value==="string"?value:"";}
function copyXWeightedLength(value){return [...copyText(value).replace(COPY_URL_RE,"\uFFF0")].reduce((n,c)=>n+(c==="\uFFF0"?23:c.codePointAt(0)<128?1:2),0);}
function validateCopyRelease(packet){
 if(!packet||typeof packet!=="object"||Array.isArray(packet))return{status:"blocked",blocking_reasons:["release_packet_not_object"],warnings:[],machine_approval:false};
 const errors=[],warnings=[],block=k=>{if(!errors.includes(k))errors.push(k)};
 const platform=copyText(packet.platform),form=copyText(packet.format);
 if(!COPY_PLATFORMS.has(platform))block("invalid_or_missing_platform");
 if(platform==="x"&&!COPY_X_FORMS.has(form))block("invalid_x_format");
 if(!form)block("missing_publish_format");
 let parts,body;
 if(platform==="x"&&form==="thread"){
  parts=packet.posts;
  if(!Array.isArray(parts)||parts.length<2||parts.some(p=>typeof p!=="string"||!p.trim())){block("thread_requires_complete_posts");parts=[];}
  if(copyText(packet.draft).trim())block("thread_draft_must_use_posts_only");
  body=parts.join("\n\n");
 }else{
  body=copyText(packet.draft);
  if(packet.posts!==undefined&&packet.posts!==null)block("single_post_must_not_include_parts");
  parts=[body];
 }
 if(!body.trim())block("empty_release_body");
 if(COPY_PLACEHOLDER.test(body))block("unresolved_publish_placeholder");
 if(COPY_BAIT.test(body))warnings.push("engagement_bait_must_be_removed_or_justified");
 if(platform==="x"){
  if(["short_text","image_post","thread"].includes(form))for(let i=0;i<parts.length;i++){
   const len=copyXWeightedLength(parts[i]);
   if(len>280)block("x_post_"+(i+1)+"_over_280_conservative_weight");
   else if(len>265)warnings.push("x_post_"+(i+1)+"_close_to_limit_verify_in_composer");
  }
  if(form==="long_post"&&packet.account_long_posts_confirmed!==true)block("x_long_post_entitlement_not_confirmed");
  if(form==="article"&&packet.account_articles_confirmed!==true)block("x_article_entitlement_not_confirmed");
 }
 if((platform==="xiaohongshu"&&["image_post","carousel"].includes(form))||(platform==="douyin"&&["video","video_post","image_post","carousel"].includes(form))){
  if(packet.media_required!==true)block("visual_format_requires_real_media");
 }
 if(platform==="douyin"&&form==="video_script"&&packet.video_deliverable_requested===true)block("video_script_is_not_finished_video");
 if(packet.media_required===true){
  const assets=packet.media_assets;
  if(!Array.isArray(assets)||assets.length===0)block("required_media_unavailable");
  else for(let i=0;i<assets.length;i++)if(!assets[i]||typeof assets[i]!=="object"||assets[i].ready!==true||assets[i].rights_cleared!==true)block("required_media_"+(i+1)+"_not_ready_or_rights_uncleared");
 }
 if(packet.disclosure_required===true){
  const phrase=copyText(packet.disclosure_text).trim();
  if(!phrase||!body.includes(phrase))block("mandatory_disclosure_not_in_publish_text");
 }
 if(COPY_EXTERNAL.has(copyText(packet.genre))){
  const links=packet.sources;
  if(!Array.isArray(links)||!links.length||links.some(x=>!x||typeof x!=="object"||!copyText(x.locator).trim()||!copyText(x.supports).trim()))block("no_claim_specific_external_sources");
 }
 const scope=copyText(packet.edit_scope);
 if(scope==="review_only")block("review_only_is_not_release");
 if(["title_only","opening_only","ending_only","minimal"].includes(scope)){
  if(!copyText(packet.original).trim())block("missing_original_for_scoped_edit");
  else if(scope==="title_only"&&body!==packet.original)block("title_only_modified_body");
  else if(["opening_only","ending_only","minimal"].includes(scope))warnings.push("human_must_verify_scoped_edit_against_original");
 }
 let protectedPhrases=packet.protected_phrases===undefined?[]:packet.protected_phrases;
 if(!Array.isArray(protectedPhrases)){block("invalid_protected_phrases");protectedPhrases=[];}
 for(const phrase of protectedPhrases)if(typeof phrase!=="string"||(phrase&&!body.includes(phrase)))block("protected_phrase_lost");
 const checks=packet.acceptance&&typeof packet.acceptance==="object"&&!Array.isArray(packet.acceptance)?packet.acceptance:{};
 if(!packet.acceptance||typeof packet.acceptance!=="object"||Array.isArray(packet.acceptance))block("acceptance_record_missing");
 for(const gate of COPY_P0_GATES){
  const c=checks[gate];
  if(!c||typeof c!=="object"||Array.isArray(c)||c.status!=="pass"){block(gate+"_not_signed_off");continue;}
  if(copyText(c.evidence).trim().length<12)block(gate+"_evidence_insufficient");
  if(COPY_ANCHORED.has(gate)){
   const anchor=copyText(c.anchor).trim();
   if(anchor.length<4||!body.includes(anchor))block(gate+"_missing_real_draft_anchor");
  }
 }
 const reviewer=packet.reviewer;
 if(!reviewer||typeof reviewer!=="object"||["editorial_reviewed","facts_and_rights_checked","final_publish_previewed"].some(k=>reviewer[k]!==true))block("reviewer_attestation_incomplete");
 return{status:errors.length?"blocked":"eligible_for_delivery",blocking_reasons:errors,warnings,x_conservative_weights:platform==="x"?parts.map(copyXWeightedLength):[],machine_approval:false,user_approved:false,published:false,notice:"eligible_for_delivery requires actual human/editorial verification; this check only validates declared evidence, package shape and length. Source truth and actual account entitlements still need human verification."};
}
function copyReleaseFixture(){
 const draft="这款开源工具帮助AI网站开发者检查布局和文字层级。先说明产品受众，再检查页面设计问题。项目与安装方法见 https://example.org/tool";
 const acceptance=Object.fromEntries(COPY_P0_GATES.map(n=>[n,{status:"pass",evidence:"编辑复核了这条具体文案的相关部分；以下锚点确实存在。",anchor:COPY_ANCHORED.has(n)?"产品受众":""}]));
 return{draft,platform:"x",format:"short_text",genre:"tool",edit_scope:"new_draft",sources:[{locator:"https://example.org/tool",supports:"工具定位与基本安装说明"}],acceptance,reviewer:{editorial_reviewed:true,facts_and_rights_checked:true,final_publish_previewed:true}};
}
function copyReleaseSelfTest(){
 const check=(name,cond)=>({name,pass:!!cond});const out=[];
 const base=copyReleaseFixture();let p;
 out.push(check("complete_fixture_eligible_but_never_approved",validateCopyRelease(base).status==="eligible_for_delivery"&&!validateCopyRelease(base).machine_approval&&!validateCopyRelease(base).published));
 p=copyReleaseFixture();delete p.acceptance.original_angle;out.push(check("missing_gate",validateCopyRelease(p).blocking_reasons.includes("original_angle_not_signed_off")));
 p=copyReleaseFixture();p.acceptance.primary_payoff.evidence="好";out.push(check("short_evidence",validateCopyRelease(p).blocking_reasons.includes("primary_payoff_evidence_insufficient")));
 p=copyReleaseFixture();p.acceptance.natural_voice.anchor="此处根本不存在的句子";out.push(check("nonexistent_anchor",validateCopyRelease(p).blocking_reasons.includes("natural_voice_missing_real_draft_anchor")));
 p=copyReleaseFixture();p.reviewer.final_publish_previewed=false;out.push(check("missing_editorial_reviewer",validateCopyRelease(p).blocking_reasons.includes("reviewer_attestation_incomplete")));
 out.push(check("x_chinese_weight",copyXWeightedLength("你".repeat(140))===280&&copyXWeightedLength("你".repeat(141))===282));
 out.push(check("x_url_fixed_weight",copyXWeightedLength("链接：https://example.org/"+"a".repeat(300))===29));
 p=copyReleaseFixture();p.draft="AI网站为什么总有模板感？"+"我们用具体设计准则检查页面。".repeat(35);out.push(check("oversize_x_280",validateCopyRelease(p).blocking_reasons.includes("x_post_1_over_280_conservative_weight")));
 p=copyReleaseFixture();p.format="long_post";out.push(check("long_post_account_permission",validateCopyRelease(p).blocking_reasons.includes("x_long_post_entitlement_not_confirmed")));p.account_long_posts_confirmed=true;out.push(check("long_post_authorized_fixture",validateCopyRelease(p).status==="eligible_for_delivery"));
 p=copyReleaseFixture();p.format="article";out.push(check("articles_account_permission",validateCopyRelease(p).blocking_reasons.includes("x_article_entitlement_not_confirmed")));
 p=copyReleaseFixture();p.format="thread";out.push(check("thread_requires_parts",validateCopyRelease(p).blocking_reasons.includes("thread_requires_complete_posts")));p.draft="";p.posts=["产品受众，第一页说明产品问题。","第二页给可用的安装入口 https://example.org/tool"];out.push(check("complete_thread_fixture",validateCopyRelease(p).status==="eligible_for_delivery"));
 p=copyReleaseFixture();p.media_required=true;out.push(check("missing_media",validateCopyRelease(p).blocking_reasons.includes("required_media_unavailable")));p.media_assets=[{ready:true,rights_cleared:false}];out.push(check("uncleared_media_rights",validateCopyRelease(p).blocking_reasons.includes("required_media_1_not_ready_or_rights_uncleared")));
 p=copyReleaseFixture();p.disclosure_required=true;p.disclosure_text="广告合作";out.push(check("disclosure_missing",validateCopyRelease(p).blocking_reasons.includes("mandatory_disclosure_not_in_publish_text")));
 p=copyReleaseFixture();p.sources=[{locator:"https://example.org"}];out.push(check("claim_specific_sources",validateCopyRelease(p).blocking_reasons.includes("no_claim_specific_external_sources")));
 p=copyReleaseFixture();p.draft+="\n[待补截图]";out.push(check("unresolved_placeholder",validateCopyRelease(p).blocking_reasons.includes("unresolved_publish_placeholder")));
 p=copyReleaseFixture();p.edit_scope="review_only";out.push(check("review_only_not_release",validateCopyRelease(p).blocking_reasons.includes("review_only_is_not_release")));
 p=copyReleaseFixture();p.edit_scope="title_only";p.original="另一版本正文";out.push(check("title_scope_preserved",validateCopyRelease(p).blocking_reasons.includes("title_only_modified_body")));
 p=copyReleaseFixture();p.platform="xiaohongshu";p.format="text";p.genre="emotion";delete p.sources;out.push(check("poetry_no_forced_sources",validateCopyRelease(p).status==="eligible_for_delivery"));
 p=copyReleaseFixture();p.protected_phrases=null;out.push(check("invalid_protected_phrases",validateCopyRelease(p).blocking_reasons.includes("invalid_protected_phrases")));
 p=copyReleaseFixture();p.platform="xiaohongshu";p.format="carousel";out.push(check("xiaohongshu_media_requirement",validateCopyRelease(p).blocking_reasons.includes("visual_format_requires_real_media")));
 p=copyReleaseFixture();p.platform="douyin";p.format="video_script";p.video_deliverable_requested=true;out.push(check("douyin_script_not_video",validateCopyRelease(p).blocking_reasons.includes("video_script_is_not_finished_video")));
 p=copyReleaseFixture();delete p.reviewer;out.push(check("missing_reviewer_hard_block",validateCopyRelease(p).status==="blocked"));
 out.push(check("invalid_packet",validateCopyRelease(null).blocking_reasons.includes("release_packet_not_object")));
 return{pass:out.every(x=>x.pass),total:out.length,passed:out.filter(x=>x.pass).length,failed:out.filter(x=>!x.pass).map(x=>x.name),checks:out,public_release_authorized:false,machine_approval:false,important:"Synthetic parity checks do not verify real facts, copyright or editorial judgement."};
}


const EDITORIAL_CLICHES=["在这个飞速发展的时代","在这个信息爆炸的时代","颠覆你的认知","彻底改变行业","不看后悔","震惊全网","史上最强","真正重要的是","建议先收藏","点赞收藏关注","看完这篇你就懂了","开启全新篇章","赋能千行百业"];
const EDITORIAL_ABSOLUTES=/100\s*[%％]\s*(?:成功|准确|有效)|(?:保证|必定)(?:爆火|涨粉|变现|播放)|(?:永久免费|完全免费且无限制|随便商用|绕过平台检测|不会被平台检测)/;
const EDITORIAL_TEST=/(?:我|本人)(?:亲测|实测|实际跑通|已经跑通|都试过)|亲测有效/;
function editorialPreflight(record){
 if(!record||typeof record!=="object"||Array.isArray(record))return{status:"invalid_input",hints:[{code:"input_not_object"}],approved:false,claim_verified:false,virality_prediction:null};
 if(typeof record.draft!=="string"&&record.draft!==undefined)return{status:"invalid_input",hints:[{code:"draft_must_be_string"}],approved:false,claim_verified:false,virality_prediction:null};
 const body=record.draft||"",hints=[],add=(code,evidence,suggestion)=>hints.push({code,evidence,suggestion});
 if(!body.trim())add("empty_draft","","没有正文。此工具不代替正式出稿。");
 const paras=body.split(/\n\s*\n/).map(s=>s.replace(/\s+/g,"").replace(/^[ \t，。！？.!?：:;；]+|[ \t，。！？.!?：:;；]+$/g,"")).filter(Boolean);
 const count=new Map();for(const para of paras)if([...para].length>=18)count.set(para,(count.get(para)||0)+1);
 for(const [para,n] of count)if(n>1)add("duplicate_paragraph",para.slice(0,65),"确认是否刻意复沓；若无独立表达价值，合并重复段。");
 const missing=[];for(const f of Array.isArray(record.required_facts)?record.required_facts:[])if(typeof f==="string"&&f&&!body.toLowerCase().includes(f.toLowerCase()))missing.push(f);
 if(missing.length)add("required_facts_missing",missing,"与原始资料逐项核对；不能只靠编辑预先列出的事实清单。");
 for(const phrase of Array.isArray(record.protected_phrases)?record.protected_phrases:[])if(typeof phrase==="string"&&phrase&&!body.includes(phrase))add("protected_phrase_changed",phrase,"如果属于保真修改，请保留原话或取得用户明确授权。");
 for(const phrase of EDITORIAL_CLICHES)if(body.includes(phrase))add("generic_promo_phrase",phrase,"检查它是否增加具体事实或作者真实语气；否则用有证据的细节表达。");
 const absolute=EDITORIAL_ABSOLUTES.exec(body);if(absolute)add("absolute_claim_check",absolute[0],"核对限定条件、证据/商业条款，必要时降低绝对承诺。");
 const personal=EDITORIAL_TEST.exec(body);if(personal&&record.test_status!=="user_verified")add("first_person_test_unverified",personal[0],"仅用户本人已明确提供真实操作证据时才能使用第一人称亲测。");
 if(COPY_EXTERNAL.has(record.genre)&&!record.sources?.length)add("source_gap",record.genre,"请人工检查关键技术、时间、性能、价格和许可主张的一手来源。");
 if(typeof record.original==="string"&&["review_only","title_only"].includes(record.edit_scope)&&record.original!==body)add("edit_scope_changed_body",record.edit_scope,"纯审稿或只改标题不能修改正文；以原有质量门禁为准。");
 return{status:"editorial_hints_only",approved:false,claim_verified:false,virality_prediction:null,hints,notice:"仅做机械预检；不重写、不裁定风格或事实、不能证明传播表现。"};
}
function editorialPreflightSelfTest(){
 const check=(name,ok)=>({name,pass:!!ok});const tests=[];
 const has=(p,k)=>editorialPreflight(p).hints.some(x=>x.code===k);
 tests.push(check("empty_draft",has({draft:""},"empty_draft")));
 tests.push(check("duplicate_paragraph",has({draft:"AI信息每次出现都要核对原始发布时间。\n\nAI信息每次出现都要核对原始发布时间。"},"duplicate_paragraph")));
 tests.push(check("required_facts_missing",has({draft:"这是一则新工具新闻。",required_facts:["原始发布日期"]},"required_facts_missing")));
 tests.push(check("protected_phrase_changed",has({draft:"原文未保留",protected_phrases:["用户坚持保留的话"]},"protected_phrase_changed")));
 tests.push(check("promo_cliche",has({draft:"不看后悔"},"generic_promo_phrase")));
 tests.push(check("absolute_claim_check",has({draft:"保证涨粉"},"absolute_claim_check")));
 tests.push(check("personal_test_unverified",has({draft:"我亲测这个项目跑通"},"first_person_test_unverified")));
 tests.push(check("personal_test_verified_not_flagged",!has({draft:"我亲测这个项目跑通",test_status:"user_verified"},"first_person_test_unverified")));
 tests.push(check("source_gap",has({draft:"工具不错",genre:"tool"},"source_gap")));
 tests.push(check("scope_lock",has({draft:"已改正文",original:"未改正文",edit_scope:"title_only"},"edit_scope_changed_body")));
 const ok=editorialPreflight({draft:"可靠论断前请核查原始证据。"});
 tests.push(check("no_machine_approval",ok.approved===false&&ok.claim_verified===false&&ok.virality_prediction===null));
 return{pass:tests.every(x=>x.pass),passed:tests.filter(x=>x.pass).length,total:tests.length,tests,publication_approved:false,scope:"nonblocking editorial preflight hints"};
}


const COPY_EDIT_SCOPES=new Set(["new_draft","review_only","title_only","opening_only","ending_only","minimal","substantive_rewrite"]);
const COPY_FACT_STATUS=new Set(["user_verified","original_source","third_party_claim","proposed","unknown"]);
const COPY_PAYOFF_TYPES=new Set(["utility","learning","save","insight","decision","information","emotion","entertainment","social_expression"]);
function copyQualityPreflight(p){
 if(!p||typeof p!=="object"||Array.isArray(p))return{status:"blocked",blocking_reasons:["record_not_object"],warnings:[],preserved:{},manually_verified:false,published:false};
 const s=x=>typeof x==="string"?x:"",mode=s(p.edit_scope),original=s(p.original),body=s(p.draft),errors=[],warnings=[],block=x=>{if(!errors.includes(x))errors.push(x)};
 if(!COPY_EDIT_SCOPES.has(mode))block("invalid_or_missing_edit_scope");
 if(!["douyin","xiaohongshu","x","multi","unspecified"].includes(p.platform))warnings.push("platform_unset_or_invalid");
 if(!s(p.audience).trim())block("missing_target_audience");
 if(!s(p.central_claim).trim())block("missing_central_claim");
 if(mode!=="review_only"&&!body.trim())block("empty_draft");
 if(mode!=="new_draft"&&!original.trim())block("missing_original_for_edit");
 if(mode==="review_only"){if(body!==original)block("review_only_must_not_rewrite");if(s(p.headline_new)!==s(p.headline_original))block("review_only_must_not_change_title")}
 if(mode==="title_only"&&body!==original)block("title_only_body_changed");
 if(["opening_only","ending_only"].includes(mode)&&body!==original)warnings.push("partial_scope_requires_human_diff_review");
 let diagnostic=null;
 if(mode==="minimal"&&original){const a=[...original].length,b=[...body].length;diagnostic=Math.round((2*Math.min(a,b)/(a+b||1))*1000)/1000;if(diagnostic<0.8)block("minimal_edit_extensively_rewritten");else if(body!==original)warnings.push("minimal_edit_exact_SequenceMatcher_not_ported_manual_review_required")}
 let keep=p.protected_phrases??[],terms=p.required_terms??[];
 if(!Array.isArray(keep)||keep.some(x=>typeof x!=="string")){block("invalid_protected_phrases");keep=[]}
 if(!Array.isArray(terms)||terms.some(x=>typeof x!=="string")){block("invalid_required_terms");terms=[]}
 const missingKeep=keep.filter(x=>x&&!body.toLowerCase().includes(x.toLowerCase())),missingRequired=terms.filter(x=>x&&!body.toLowerCase().includes(x.toLowerCase()));
 if(missingKeep.length)block("protected_content_lost");
 if(missingRequired.length)block("required_content_missing");
 if(["minimal","title_only","opening_only","ending_only"].includes(mode)&&keep.length===0)warnings.push("no_explicitly_protected_author_voice_fragments");
 let claims=p.claims??[];if(!Array.isArray(claims)){block("claims_not_a_list");claims=[]}
 for(let i=0;i<claims.length;i++){const x=claims[i];if(!x||typeof x!=="object"){block("claim_"+i+"_invalid");continue}const status=x.evidence_status;if(!s(x.text).trim()||!COPY_FACT_STATUS.has(status))block("claim_"+i+"_missing_evidence_provenance");if(x.presented_as_tested&&status!=="user_verified")block("claim_"+i+"_unverified_experience_claim");if(["proposed","unknown"].includes(status)&&x.presented_as_fact)block("claim_"+i+"_unverified_statement_of_fact");if(status==="third_party_claim"&&x.first_person_experience)block("claim_"+i+"_source_laundered_as_personal_experience")}
 if(p.content_type==="tutorial"){if(!s(p.proof_plan))warnings.push("tutorial_missing_verification_plan");if(claims.length===0)warnings.push("tutorial_no_claim_inventory")}
 if(["new_draft","substantive_rewrite"].includes(mode)){
  const research=p.research;if(!research||typeof research!=="object"||Array.isArray(research))block("research_dossier_missing");else{for(const k of ["question","summary","limitations"])if(!s(research[k]).trim())block("research_"+k+"_missing");if(!Array.isArray(research.sources)||!research.sources.length)block("research_sources_missing");else for(let i=0;i<research.sources.length;i++){const a=research.sources[i];if(!a||typeof a!=="object"||!s(a.locator).trim()||!s(a.supports).trim())block("research_source_"+i+"_incomplete")}}
  const delivery=p.value_delivery;if(!delivery||typeof delivery!=="object"||Array.isArray(delivery))block("value_delivery_missing");else{for(const k of ["hook","shareability","readability","primary_payoff"])if(!s(delivery[k]).trim())block("value_"+k+"_missing");if(!s(delivery.primary_payoff_type).trim())block("value_primary_payoff_type_missing");else if(!COPY_PAYOFF_TYPES.has(delivery.primary_payoff_type))block("value_primary_payoff_type_invalid");const extra=delivery.secondary_payoffs??[];if(!Array.isArray(extra)||extra.some(x=>!COPY_PAYOFF_TYPES.has(x)))block("value_secondary_payoffs_invalid")}
 }
 if(/100%成功|百分百保证|保证(?:涨粉|播放|变现)|零失误|永久(?:免费|有效)/.test(body))warnings.push("absolute_promise_detected_check_if_supported");
 if(/评论区(?:打|扣|留下)(?:1|666|YES)|点赞(?:收藏)?关注三连|求个三连/.test(body))warnings.push("formulaic_engagement_bait");
 warnings.push("semantic_truth_author_voice_and_platform_compliance_require_human_review");
 return{case_id:s(p.case_id),status:errors.length?"blocked":"requires_editorial_review",blocking_reasons:errors,warnings:[...new Set(warnings)],preserved:{protected_count:keep.length-missingKeep.length,protected_total:keep.length,missing_protected:missingKeep,missing_required:missingRequired,minimal_similarity_diagnostic:diagnostic},manually_verified:false,published:false,note:"Structural port of copy_quality_gate.py. Python SequenceMatcher minimal-diff parity not implemented, manual/original Python review required."};
}
function copyQualitySelfTest(){
 const old="今天给豆姐安装了工具。按提示扫码授权，然后试了两分钟课程。后面的整套课程还没测。我的建议是先从第一节试。当然，如果你的课有老师手把手辅导，那当我没说。";
 const fixture=()=>({edit_scope:"minimal",platform:"xiaohongshu",content_type:"tutorial",audience:"需要学习的人",central_claim:"AI可能帮助学习",original:old,draft:old.replace("我的建议是","我建议"),headline_original:"标题",headline_new:"标题",protected_phrases:["豆姐","两分钟课程","整套课程还没测","那当我没说"],required_terms:["授权","第一节"],proof_plan:"检查课程是否一致",claims:[{text:"两分钟课程",evidence_status:"user_verified",presented_as_tested:true},{text:"完整课程",evidence_status:"proposed"}]});
 const tests=[],add=(n,ok)=>tests.push({name:n,pass:!!ok}),fails=(p,k)=>copyQualityPreflight(p).blocking_reasons.includes(k);let p;
 p=fixture();add("small_edit_requires_editorial_review",copyQualityPreflight(p).status==="requires_editorial_review"&&copyQualityPreflight(p).preserved.protected_count===4);
 p=fixture();p.edit_scope="review_only";p.draft=p.original+"修改";add("review_only_must_not_rewrite",fails(p,"review_only_must_not_rewrite"));
 p=fixture();p.edit_scope="review_only";p.draft=p.original;add("review_only_unchanged_valid",copyQualityPreflight(p).status==="requires_editorial_review");
 p=fixture();p.edit_scope="title_only";add("title_only_body_locked",fails(p,"title_only_body_changed"));
 p=fixture();p.draft="只有这一句";add("minimal_mass_deletion_blocked",fails(p,"minimal_edit_extensively_rewritten"));
 p=fixture();p.draft=p.draft.replace("那当我没说","大家一起加油");add("protected_phrase_blocked",fails(p,"protected_content_lost"));
 p=fixture();p.draft=p.draft.replace("扫码授权","扫码");add("required_terms_blocked",fails(p,"required_content_missing"));
 p=fixture();p.claims=[{text:"第三方演示",evidence_status:"third_party_claim",presented_as_tested:true,first_person_experience:true}];add("thirdparty_not_personal_test",fails(p,"claim_0_unverified_experience_claim")&&fails(p,"claim_0_source_laundered_as_personal_experience"));
 p=fixture();p.claims[1].presented_as_tested=true;add("proposed_not_verified",fails(p,"claim_1_unverified_experience_claim"));
 p=fixture();p.claims=[{text:"1000次实测",evidence_status:"unknown",presented_as_fact:true}];add("unknown_not_fact",fails(p,"claim_0_unverified_statement_of_fact"));
 p=fixture();p.edit_scope="new_draft";p.original="";p.protected_phrases=[];add("research_and_value_missing",fails(p,"research_dossier_missing")&&fails(p,"value_delivery_missing"));
 p=fixture();p.edit_scope="new_draft";p.original="";p.protected_phrases=[];p.research={question:"目标问题",summary:"归纳",limitations:"不代表实测",sources:[{locator:"https://example.org",supports:"用途"}]};p.value_delivery={hook:"价值点",shareability:"传播理由",readability:"通俗",primary_payoff:"收获学习技能",primary_payoff_type:"learning"};add("valid_research_requires_editor",copyQualityPreflight(p).status==="requires_editorial_review");
 p=fixture();p.edit_scope="new_draft";p.research={question:"问题",summary:"归纳",limitations:"边界",sources:[]};p.value_delivery={hook:"开头",shareability:"理由"};add("missing_sources_and_readability",fails(p,"research_sources_missing")&&fails(p,"value_readability_missing"));
 p=fixture();p.edit_scope="new_draft";p.research={question:"问题",summary:"归纳",limitations:"有限",sources:[{locator:"用户文字",supports:"观点"}]};p.value_delivery={hook:"钩子",shareability:"共鸣",readability:"自然",primary_payoff:"获得理解",primary_payoff_type:"emotion"};add("emotion_without_learning_valid",copyQualityPreflight(p).status==="requires_editorial_review");
 p=fixture();p.edit_scope="new_draft";p.research={question:"问题",summary:"归纳",limitations:"有限",sources:[{locator:"用户文字",supports:"观点"}]};p.value_delivery={hook:"钩子",shareability:"共鸣",readability:"自然",primary_payoff:"价值",primary_payoff_type:"fake_viral"};add("invalid_payoff_type",fails(p,"value_primary_payoff_type_invalid"));
 p=fixture();p.edit_scope="substantive_rewrite";add("major_rewrite_needs_research",fails(p,"research_dossier_missing"));
 p=fixture();p.proof_plan="";add("tutorial_proof_plan_warning",copyQualityPreflight(p).warnings.includes("tutorial_missing_verification_plan"));
 p=fixture();add("no_machine_publication",copyQualityPreflight(p).manually_verified===false&&copyQualityPreflight(p).published===false);
 add("bad_input",fails("text","record_not_object"));
 return{pass:tests.every(x=>x.pass),total:tests.length,passed:tests.filter(x=>x.pass).length,failed:tests.filter(x=>!x.pass).map(x=>x.name),tests,warning:"Minimal similarity only uses a conservative length diagnostic; exact Python difflib remains a gap."};
}

async function persist(env,src,row,now){
 const ekey=entityIdentity(row);const prev=await env.DB.prepare("SELECT source_ids_json FROM entities WHERE entity_key=?").bind(ekey).first();
 let families=[];try{families=JSON.parse(prev?.source_ids_json||"[]");if(!Array.isArray(families))families=[]}catch{families=[]}
 if(!families.includes(src.source_id))families.push(src.source_id);
 const prior=await env.DB.prepare("SELECT first_seen_utc FROM evidence WHERE source_id=? AND canonical_url=?").bind(src.source_id,row.url).first();
 await env.DB.prepare("INSERT INTO evidence(source_id,canonical_url,original_url,title,excerpt,author,published_utc,first_seen_utc,last_seen_utc,source_scope,observed_metrics_json,raw_json) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(source_id,canonical_url) DO UPDATE SET title=excluded.title,excerpt=excluded.excerpt,last_seen_utc=excluded.last_seen_utc,observed_metrics_json=excluded.observed_metrics_json,raw_json=excluded.raw_json").bind(src.source_id,row.url,row.url,row.title,row.excerpt,row.author,row.date,prior?.first_seen_utc||now,now,row.scope,JSON.stringify({metrics:row.metrics,scope:METRIC_SCOPE,checked_at:now}),JSON.stringify({url:row.url,title:row.title,excerpt:row.excerpt,project_url:row.project_url,preview_image:row.preview_image||"",media_review_status:"not_viewed",rights_status:"not_verified",lanes:lanesOf(row.title)})).run();
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
 if(u.pathname==="/copy-release-self-test")return json(copyReleaseSelfTest());
 if(u.pathname==="/editorial-preflight-self-test")return json(editorialPreflightSelfTest());
 if(u.pathname==="/copy-quality-self-test")return json(copyQualitySelfTest());
 if(u.pathname==="/copy-quality-contract")return json({source:"copy_quality_gate.py",implemented:["edit_scope","protect_original","required_terms","claims_status","research_dossier","payoff_type"],not_exact:["difflib SequenceMatcher minimal change ratio"],human_editorial_review_required:true,no_public_draft_submission:true});
 if(u.pathname==="/editorial-preflight-contract")return json({source:"Original editorial_preflight.py",mode:"nonblocking hints only",stored_drafts:false,external_submission:false,can_approve:false,can_publish:false,codes:["duplicate_paragraph","required_facts_missing","protected_phrase_changed","generic_promo_phrase","absolute_claim_check","first_person_test_unverified","source_gap","edit_scope_changed_body"]});
 if(u.pathname==="/copy-release-contract")return json({source:"Original delivery_release_gate.py v3.1.0",required_p0_gates:COPY_P0_GATES,external_genres:[...COPY_EXTERNAL],platforms:[...COPY_PLATFORMS],x_forms:[...COPY_X_FORMS],human_signoff_required:true,format_only:false,users_must_publish_manually:true,draft_submit_api:"not_publicly_exposed_without_authentication",mode:"synthetic_test_and_private_function_only"});
 if(u.pathname==="/quality-contract")return json({status:"metadata_and_human_gated",score_caps:LEGACY_SCORE_CAPS,score_minima:LEGACY_SCORE_MINS,total_required:85,dimensions:LEGACY_VALUE_LABELS,required_primary_count:1,original_source_required:true,social_pitch_required:true,human_editorial_approval:true,visual_originals_must_be_seen:true,copy_delivery_10_p0_gate:"ChatGPT ai-copy-production v3.1 original skill / release_gate.py; not executed on Cloudflare",automatic_publishing:false});
 if(u.pathname==="/coverage"){const data=(await env.DB.prepare("SELECT kind,enabled,COUNT(*) AS n,SUM(CASE WHEN last_result='retrieved' THEN 1 ELSE 0 END) AS last_success,SUM(CASE WHEN last_result='failed' THEN 1 ELSE 0 END) AS last_failed FROM sources GROUP BY kind,enabled ORDER BY kind").all()).results;return json({basis:"registered sources, not all verified accessible",sources:data,metric_scope:METRIC_SCOPE});}
 return json({error:"not_found"},404);
 },
 async scheduled(event,env,ctx){if(env.ENABLE_COLLECTION!=="true")return;ctx.waitUntil(processRun(env,"cf_cron_incremental"));}
};