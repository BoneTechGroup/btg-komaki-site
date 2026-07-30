# -*- coding: utf-8 -*-
"""症状ページ(/contents/配下)にメリハリCSS＋スクロール出現を footer widget 経由で注入"""
import json, base64, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://sekkotsuin-komaki.com"
import os
CRED = base64.b64encode(f"{os.environ['WP_USER_KOMAKI']}:{os.environ['WP_APP_PASSWORD_KOMAKI']}".encode()).decode()  # 環境変数に設定して使用

INJECT = """
<style id="btg-article-style">
/* ===== 症状ページのメリハリ強化（/contents/配下のみJSで発動） ===== */
.btgax .post_content h2{background:linear-gradient(135deg,#079490,#0abab5 70%,#2cc8c3);color:#fff!important;padding:16px 22px;border-radius:10px;border:none;box-shadow:0 8px 20px rgba(10,186,181,.22);letter-spacing:.06em;line-height:1.6}
.btgax .post_content h2::before,.btgax .post_content h2::after{display:none!important}
.btgax .post_content h3{background:transparent;border:none;border-left:5px solid #0abab5;border-bottom:2px solid #e2f7f6;padding:6px 2px 8px 14px;color:#20313a;letter-spacing:.05em}
.btgax .post_content h3::before,.btgax .post_content h3::after{display:none!important}
.btgax .post_content ul:not([class]), .btgax .post_content ul.wp-block-list{list-style:none;padding:22px 26px;background:#f8fbfb;border:1px solid #dde6e4;border-radius:10px}
.btgax .post_content ul:not([class])>li, .btgax .post_content ul.wp-block-list>li{position:relative;padding:7px 0 7px 34px;margin:0;border-bottom:1px dashed #dde6e4}
.btgax .post_content ul:not([class])>li:last-child, .btgax .post_content ul.wp-block-list>li:last-child{border-bottom:none}
.btgax .post_content ul:not([class])>li::before, .btgax .post_content ul.wp-block-list>li::before{content:"";position:absolute;left:4px;top:13px;width:18px;height:18px;background:#0abab5;clip-path:polygon(14% 44%,0 65%,50% 100%,100% 16%,80% 0,43% 62%)}
.btgax .post_content strong{background:linear-gradient(transparent 62%,rgba(255,233,168,.85) 62%);padding:0 2px}
.btgax .post_content table{border-radius:10px;overflow:hidden;box-shadow:0 4px 14px rgba(32,49,58,.08)}
.btgax .post_content th{background:#e2f7f6;color:#20313a}
/* スクロール出現（JSがaxr付与→発動。JS無効時は非表示にならない） */
.btgax .axr{opacity:0;transform:translateY(22px);transition:opacity .7s cubic-bezier(.2,.6,.2,1),transform .7s cubic-bezier(.2,.6,.2,1)}
.btgax .axr.axin{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.btgax .axr{opacity:1;transform:none;transition:none}}
</style>
<script id="btg-article-script">
(function(){
  try{
    if(!/^\\/contents\\/.+/.test(location.pathname)) return;      // 症状ページのみ（/contents/一覧は除外）
    if(document.querySelector('.btgtop')) return;                 // btgtopデザインページは除外
    var pc = document.querySelector('.post_content');
    if(!pc) return;
    document.body.classList.add('btgax');
    var els = pc.querySelectorAll(':scope > h2, :scope > h3, :scope > figure, :scope > table, :scope > ul, :scope > ol, :scope > blockquote, :scope > .wp-block-image, :scope > .wp-block-columns, :scope > .wp-block-media-text');
    if(!('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('axin'); io.unobserve(e.target); } });
    }, {threshold: 0.08, rootMargin: '0px 0px -4% 0px'});
    els.forEach(function(el){ el.classList.add('axr'); io.observe(el); });
    setTimeout(function(){ els.forEach(function(el){ el.classList.add('axin'); }); }, 3000);  // 安全フォールバック
  }catch(e){}
})();
</script>
"""

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {CRED}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

w = get(BASE + "/wp-json/wp/v2/widgets/custom_html-2?context=edit")
content = w["instance"]["raw"]["content"]
if "btg-article-style" in content:
    print("既に注入済み → 置き換え")
    import re
    content = re.sub(r'<style id="btg-article-style">[\s\S]*?</script>\s*$', "", content)
content = content + "\n" + INJECT

body = json.dumps({"instance": {"raw": {"title": "", "content": content}}}, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(BASE + "/wp-json/wp/v2/widgets/custom_html-2", data=body, method="POST",
      headers={"Authorization": f"Basic {CRED}", "Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=60) as r:
    json.loads(r.read())
print("footer widget 注入OK")
