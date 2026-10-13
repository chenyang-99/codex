#!/usr/bin/env python3
"""Evidence-only domestic audience question/pain-point clustering.

Inputs are actually retrieved replies from eligible public Chinese communities.
Xiaohongshu/Douyin index results contribute DISCOVERY LINKS ONLY, never fake
comment data. No AI inference or automated posting.
"""
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import json,re

HERE=Path(__file__).resolve().parent
OUT=HERE/"output"
SIGNALS={
 "价格、订阅和额度":["会员","订阅","退订","收费","付费","价格","贵","加钱","买不起",
                 "购买","额度","积分","点数","充值","成本","用量","砍半","token","资源消耗"],
 "教程、理解和上手":["怎么用","怎么做","怎么生成","如何","在哪","找不到","新手",
                   "小白","教程","步骤","不会","看不懂","求教程","怎么操作"],
 "模型效果和一致性":["不像","不一致","跑偏","失真","糊","效果不好","不准确",
                    "生成失败","硬编码","正则表达式","过度防御","目标漂移","记忆丢","记忆压缩"],
 "速度、稳定和限制":["太慢","好慢","真的慢","速度","降速","卡顿","闪退","加载",
                   "网络","服务器","不稳定","限流","封号","访问不了","报错",
                   "tps","排队","砍思考","思考强度"],
 "工具选择与替代":["替代","有没有","推荐","免费","国产","哪个好","平替",
                 "什么工具","claude","没得选","切换","想换","不满意"],
 "素材、资源及工作流获取":["求整合包","求一份","求资料","求链接","求模型",
                     "求工作流","整合包","节点包","资源包","下载地址","网盘链接"],
 "版权、商用与隐私":["版权","商用","侵权","授权","肖像","著作权","隐私泄露","数据安全","账号安全"],
 "设备和平台兼容":["安卓","ios","苹果","手机端","电脑端","网页版","桌面端",
                  "mac","windows","兼容","显存","配置要求","本地部署"]
}

def read(name):
    try:return json.loads((OUT/name).read_text(encoding="utf-8"))
    except (OSError,ValueError):return {}
def normalized(url):
    try:
        v=urlsplit(url or "")
        return urlunsplit((v.scheme,v.netloc,v.path,v.query,""))
    except ValueError:return url
def classify(comment):
    text=(comment.get("text_excerpt") or "").lower()
    # Drop pure emoji shortcode strings and non-linguistic applause.
    without_emojis=re.sub(r"\[[^\[\]]{1,35}\]", "", text).strip()
    if len(re.findall(r"[一-鿿a-zA-Z]",without_emojis)) < 2:
        return []
    # Do not classify marketing spam or low-information applause as pain points.
    promotional=("需要的自取","私信领取","免费领取","扫码领取","添加微信",
                 "联系我","可协助比对","专业度可以给到顶级","最新的gpt image2.5 flare")
    if any(m in text for m in promotional):
        return []
    applause=("三连支持","三连走起","已三连","大佬威武","打call","前排前排",
              "谢谢up","感谢up","支持支持","666","好看爱看")
    if any(m in text for m in applause) and not any(q in text for q in
                       ("求整合包","求一份","求教程","求模型","求链接","怎么","哪里")):
        return []
    return [k for k,words in SIGNALS.items() if any(w.lower() in text for w in words)]
def main():
    domestic=read("domestic-discovery.json")
    douyin=read("douyin-creator-discovery.json")
    sources=[]
    indexed=[]
    for block in domestic.get("tests",[]):
        platform=block.get("platform")
        if platform in ("xiaohongshu","douyin"):
            indexed.extend([{**x,"discovery_platform":platform}
                            for x in block.get("posts",[]) if isinstance(x,dict)])
        if platform not in ("v2ex","bilibili"):continue
        for comment in block.get("comments",[]):
            if not isinstance(comment,dict) or not comment.get("text_excerpt"):continue
            entry={"platform":platform,"url":comment.get("url"),
                   "post_url":comment.get("topic_url") or comment.get("post_url"),
                   "text_excerpt":comment.get("text_excerpt"),
                   "classification_basis":"actual reply text",
                   "is_xiaohongshu_or_douyin_comment":False}
            sources.append(entry)
    # Douyin samples are actual text returned by the public developer demo,
    # not search-engine snippets, nor Bilibili/V2EX substitutes.
    if douyin.get("comments_status")=="verified_first_level_comment_text":
        for comment in douyin.get("comment_samples",[]):
            if not isinstance(comment,dict):continue
            body=comment.get("text_excerpt")
            url=comment.get("post_url")
            if not isinstance(body,str) or not body.strip() or not isinstance(url,str) or not url.startswith("https://www.douyin.com/video/"):
                continue
            sources.append({"platform":"douyin","url":url,
                 "post_url":url,"text_excerpt":body,
                 "classification_basis":"actual first-level Douyin comment body from public demo",
                 "is_xiaohongshu_or_douyin_comment":True,
                 "second_level_retrieved":False})
    # Inline replies obtained from a permitted first-level Douyin comments
    # response. These are genuine reply previews, not complete nested threads.
    if douyin.get("actual_reply_preview_texts",0)>0:
        for child in douyin.get("reply_preview_samples",[]):
            if not isinstance(child,dict):continue
            body,url=child.get("text_excerpt"),child.get("post_url")
            if not isinstance(body,str) or not body.strip() or not isinstance(url,str) or not url.startswith("https://www.douyin.com/video/"):
                continue
            sources.append({"platform":"douyin","url":url,"post_url":url,
                "text_excerpt":body,
                "comment_level":"second_level_inline_preview",
                "parent_comment_id":child.get("parent_comment_id"),
                "classification_basis":"actual reply_comment preview inside public first-level response; partial",
                "is_xiaohongshu_or_douyin_comment":True,
                "second_level_retrieved":True,
                "is_full_thread":False})
    known=set()
    unique=[]
    for row in sources:
        key=(row["platform"],normalized(row["url"]),row["text_excerpt"])
        if key in known:continue
        known.add(key)
        unique.append(row)
    buckets=defaultdict(list)
    for row in unique:
        for topic in classify(row):
            buckets[topic].append(row)
    themes=[{"theme":key,"matched_reply_count":len(vals),
             "actual_reply_examples":vals[:5]}
             for key,vals in sorted(buckets.items(),key=lambda x:len(x[1]),reverse=True)]
    report={"created_at_utc":datetime.now(timezone.utc).isoformat(),
            "description":"Observed vocabulary, not diagnosis of a platform's entire user base",
            "actual_domestic_comment_count":len(unique),
            "comment_platforms":sorted({x["platform"] for x in unique}),
            "actual_comment_platform_counts":{p:sum(x["platform"]==p for x in unique) for p in sorted({x["platform"] for x in unique})},
            "verified_douyin_comment_count":sum(x["platform"]=="douyin" for x in unique),
            "verified_douyin_inline_reply_preview_count":sum(x.get("comment_level")=="second_level_inline_preview" for x in unique),
            "verified_xiaohongshu_comment_count":0,
            "domestic_indexed_link_count":len(indexed),
            "domestic_indexed_links":indexed[:35],
            "observed_themes":themes,
            "classified_distinct_comment_count":sum(bool(classify(x)) for x in unique),
        "unclassified_comment_count":sum(not classify(x) for x in unique),
            "limitations":["Indexed Xiaohongshu/Douyin URLs are search snippets; body/comments unverified.",
                           "Sources are only public V2EX/Bilibili replies and actual verified Douyin public-demo replies (when available); no XHS comments.",
                           "Keyword matching cannot replace contextual interpretation or verify representative prevalence.",
                           "Douyin second-level text is only inline reply previews where supplied; no complete second-level pagination has been obtained.",
                           "No Xiaohongshu comment was acquired by this script."]}
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/"domestic-painpoints.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    md=["# 国内 AI 需求痛点：真实评论证据清单","",
       f"生成时间 UTC：{report['created_at_utc']}",
       f"本轮合法读取到的国内公开社区回复：{len(unique)} 条",
       f"搜索引擎收录的小红书/抖音候选链接：{len(indexed)} 条",
       "","**注意**：B站/V2EX来源与抖音评论分别注明；没有取得小红书评论。关键词统计不代表人群占比。",""]
    for theme in themes:
        md.append(f"## {theme['theme']}（命中 {theme['matched_reply_count']} 条）")
        for x in theme["actual_reply_examples"][:3]:
            md.append(f"- [{x['platform']}] {x['text_excerpt'][:180]} — {x.get('url','')}")
        md.append("")
    if not themes:md.append("本轮尚未取得能用于判定用户痛点的真实评论，不做推断。")
    md+=["","## 已检索的公开竞品链接（仅搜索索引证据）"]
    for x in indexed[:20]:
        md.append(f"- [{x['discovery_platform']}] {x.get('title','')} — {x.get('url','')}")
    (OUT/"domestic-painpoints.md").write_text("\n".join(md),encoding="utf-8")
    print(json.dumps({"status":"domestic_painpoint_aggregation_complete",
                      "real_comment_samples":len(unique),"indexed_links":len(indexed),
                      "observed_themes":len(themes)},ensure_ascii=False))
if __name__=="__main__":main()
