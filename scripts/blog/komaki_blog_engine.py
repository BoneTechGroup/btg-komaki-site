#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小牧院ブログ量産エンジン: Gemini図解・アイキャッチ生成 → WPメディア → 下書き作成"""
import json, base64, urllib.request, urllib.error, os, io, sys, time, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8")
SCRIPT_DIR = Path(__file__).parent
OUT_DIR = SCRIPT_DIR / "blog_images"
OUT_DIR.mkdir(exist_ok=True)

# ── 認証 ─────────────────────────────────────
for line in Path(r"C:\Users\ag09z\Documents\work\seo-automation\.env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.startswith("#"):
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

WP_URL = "https://sekkotsuin-komaki.com"
CRED = base64.b64encode(f"{os.environ['WP_USER_KOMAKI']}:{os.environ['WP_APP_PASSWORD_KOMAKI']}".encode()).decode()  # .envにWP_USER_KOMAKI/WP_APP_PASSWORD_KOMAKIを追加して使用
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
FONT = "C:/Windows/Fonts/NotoSansJP-VF.ttf"
ILLUST = Path(r"C:\Users\ag09z\Documents\work\小牧公式サイトリニューアル\assets\illust")

# ── Gemini 画像生成 ───────────────────────────
def _refs(names):
    parts = []
    for n in names:
        p = ILLUST / n
        if p.exists():
            parts.append({"inlineData": {"mimeType": "image/png",
                          "data": base64.b64encode(p.read_bytes()).decode()}})
    return parts

CHAR_REFS = _refs(["iwai3.png", "natumi2.png", "uketuke1.png", "murase1.png"])

def gemini_image(prompt, use_refs=False, retries=2):
    parts = []
    if use_refs:
        parts += CHAR_REFS
    parts.append({"text": prompt})
    payload = json.dumps({"contents": [{"parts": parts}],
                          "generationConfig": {"responseModalities": ["IMAGE"]}}).encode()
    for model in ["gemini-3-pro-image-preview", "gemini-2.5-flash-image"]:
        for attempt in range(retries):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
            req = urllib.request.Request(url, data=payload,
                  headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    result = json.loads(r.read())
                for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        img = Image.open(io.BytesIO(base64.b64decode(part["inlineData"]["data"]))).convert("RGB")
                        print(f"    [{model}] {img.size}", flush=True)
                        return img
                print(f"    [{model}] no image, retry", flush=True)
            except Exception as e:
                print(f"    [{model}] {str(e)[:120]}", flush=True)
                time.sleep(5)
    raise RuntimeError("gemini image generation failed")

def resize_crop(img, tw, th):
    scale = max(tw / img.width, th / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    l = (img.width - tw) // 2; t = (img.height - th) // 2
    return img.crop((l, t, l + tw, t + th))

def add_title_text(img, lines):
    draw = ImageDraw.Draw(img)
    W, H = img.size
    size = 72 if len(lines) <= 2 else 62
    font = ImageFont.truetype(FONT, size)
    lh = font.getbbox("あ")[3] - font.getbbox("あ")[1] + 14
    total_h = lh * len(lines)
    max_w = max(draw.textbbox((0, 0), l, font=font)[2] for l in lines)
    mx, sy = 52, (H - total_h) // 2 - 8
    bg = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle(
        [(mx - 28, sy - 20), (mx + max_w + 28, sy + total_h + 20)], radius=16, fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img.convert("RGBA"), bg).convert("RGB")
    draw = ImageDraw.Draw(img)
    y = sy
    for line in lines:
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx or dy:
                    draw.text((mx + dx, y + dy), line, font=font, fill=(255, 255, 255))
        draw.text((mx, y), line, font=font, fill=(38, 48, 56))
        y += lh
    return img

# ── WordPress ────────────────────────────────
def wp_upload(img, filename, alt):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/media", data=buf.getvalue(),
          headers={"Authorization": f"Basic {CRED}",
                   "Content-Disposition": f"attachment; filename={filename}",
                   "Content-Type": "image/jpeg"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        res = json.loads(r.read())
    # alt text
    body = json.dumps({"alt_text": alt}).encode()
    req2 = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/media/{res['id']}", data=body,
           headers={"Authorization": f"Basic {CRED}", "Content-Type": "application/json; charset=utf-8"}, method="POST")
    urllib.request.urlopen(req2, timeout=60).read()
    return res["id"], res["source_url"]

def wp_create_draft(article, content, featured_id):
    data = {
        "title": article["title"], "slug": article["slug"], "status": "draft",
        "content": content, "excerpt": article["description"],
        "categories": article.get("categories", [8]),
        "featured_media": featured_id,
        "meta": {"ssp_meta_description": article["description"],
                 "ssp_meta_keyword": article["keywords"]},
    }
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/posts", data=body,
          headers={"Authorization": f"Basic {CRED}", "Content-Type": "application/json; charset=utf-8"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read()), True
    except urllib.error.HTTPError as e:
        if e.code == 400:  # metaが未登録の場合はmeta無しで再試行
            data.pop("meta")
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(f"{WP_URL}/wp-json/wp/v2/posts", data=body,
                  headers={"Authorization": f"Basic {CRED}", "Content-Type": "application/json; charset=utf-8"}, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read()), False
        raise

# ── 図解スタイル共通プロンプト ──────────────────
FIG_STYLE = (
    "Clean, modern medical illustration for a Japanese osteopathic clinic blog. "
    "Flat vector style with soft shading, palette: teal (#0abab5), dark slate (#20313a), "
    "warm coral accent (#ef8a80) for pain/highlight areas, off-white background (#fbfaf8). "
    "Anatomically accurate, easy to understand at a glance, professional and stylish. "
    "Wide 16:9 landscape composition. STRICTLY NO TEXT, no letters, no numbers, "
    "no labels, no watermark, no signature anywhere in the image. "
)

EYE_STYLE = (
    "Cute anime chibi style illustration matching the reference character art exactly. "
    "Same character design: friendly staff in dark navy medical scrubs / patient characters. "
    "Soft pastel watercolor background, warm gentle colors, clean lineart. "
    "Wide 16:9 landscape, main character on the RIGHT side, "
    "left half kept light and uncluttered for text placement. "
    "STRICTLY NO TEXT, no letters, no watermark. "
)

# ── 共通パーツHTML ───────────────────────────
DISCLAIMER = '<p style="font-size:12px;color:#888">※本記事は一般的な情報提供を目的としたもので、効果には個人差があります。強い痛み・しびれ・発熱などがある場合は、医療機関の受診をおすすめします。</p>'

def cta_block(text):
    return (
        f'<p>{text}</p>'
        '<div style="display:flex;gap:12px;flex-wrap:wrap;margin:24px 0">'
        '<a href="https://lin.ee/XQNXiXQ" target="_blank" rel="noopener" style="display:inline-block;background:#06c755;color:#fff;font-weight:700;padding:14px 30px;border-radius:4px;text-decoration:none;letter-spacing:.08em">LINEで相談・予約する</a>'
        '<a href="tel:0568901841" style="display:inline-block;background:linear-gradient(135deg,#079490,#0abab5);color:#fff;font-weight:700;padding:14px 30px;border-radius:4px;text-decoration:none;letter-spacing:.08em">0568-90-1841に電話する</a>'
        '</div>'
        '<p style="font-size:13px;color:#5f7078">受付時間 9:30〜12:30／15:00〜19:30（土曜は13:30まで・日曜と第2/4月曜は休み）｜駐車場完備・国道41号沿い</p>'
    )

def related_block(links):
    lis = "".join(f'<li><a href="{u}">{t}</a></li>' for t, u in links)
    return (
        '<h2>関連ページ</h2>'
        f'<ul>{lis}</ul>'
        '<div style="text-align:center;margin:36px 0 8px">'
        '<a href="https://sekkotsuin-komaki.com/" style="display:inline-block;background:linear-gradient(135deg,#079490,#0abab5,#4fd6c9);color:#fff;font-weight:700;padding:16px 46px;border-radius:999px;text-decoration:none;letter-spacing:.14em;box-shadow:0 8px 22px rgba(10,186,181,.3)">トップページへ戻る</a>'
        '</div>'
    )

def faq_block(faqs):
    html = "<h2>よくある質問（FAQ）</h2>"
    for q, a in faqs:
        html += f"<h3>Q. {q}</h3><p>A. {a}</p>"
    return html

def jsonld_block(article, faqs):
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    art_ld = {"@context": "https://schema.org", "@type": "BlogPosting",
              "headline": article["title"],
              "description": article["description"],
              "author": {"@type": "Organization", "name": "BTG接骨院 小牧院"},
              "publisher": {"@type": "Organization", "name": "BTG接骨院 小牧院",
                            "logo": {"@type": "ImageObject", "url": "https://sekkotsuin-komaki.com/wp/wp-content/uploads/2026/04/btg-logo.png"}},
              "mainEntityOfPage": f"https://sekkotsuin-komaki.com/blog/{article['slug']}/"}
    return (f'<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>'
            f'<script type="application/ld+json">{json.dumps(art_ld, ensure_ascii=False)}</script>')

# ── メイン処理 ────────────────────────────────
def process(article):
    print(f"\n=== {article['slug']} ===", flush=True)
    body = article["body"]

    # 図解生成 → アップロード → 差し込み
    for fig in article.get("figures", []):
        print(f"  fig: {fig['name']}", flush=True)
        img = gemini_image(FIG_STYLE + fig["prompt"])
        img = resize_crop(img, 1200, 675)
        local = OUT_DIR / f"{article['slug']}_{fig['name']}.jpg"
        img.save(local, "JPEG", quality=88)
        mid, url = wp_upload(img, f"{article['slug']}-{fig['name']}.jpg", fig["alt"])
        fig_html = (f'<figure class="wp-block-image size-large"><img src="{url}" alt="{fig["alt"]}" loading="lazy"/>'
                    f'<figcaption>{fig["caption"]}</figcaption></figure>')
        body = body.replace("{{FIG:" + fig["name"] + "}}", fig_html)

    # アイキャッチ生成
    print("  eyecatch", flush=True)
    eye = gemini_image(EYE_STYLE + article["eyecatch"]["scene"], use_refs=True)
    eye = resize_crop(eye, 1280, 720)
    eye = add_title_text(eye, article["eyecatch"]["lines"])
    eye.save(OUT_DIR / f"{article['slug']}_eyecatch.jpg", "JPEG", quality=88)
    eid, _ = wp_upload(eye, f"{article['slug']}-eyecatch.jpg", article["title"])

    # 本文組み立て
    content = (body
               + faq_block(article["faqs"])
               + DISCLAIMER
               + cta_block(article["cta"])
               + related_block(article["related"])
               + jsonld_block(article, article["faqs"]))

    if "{{FIG:" in content:
        raise RuntimeError(f"unresolved figure marker in {article['slug']}")

    res, meta_ok = wp_create_draft(article, content, eid)
    chars = len(re.sub(r"<[^>]+>", "", body))
    print(f"  -> draft id={res['id']} meta={'OK' if meta_ok else 'SKIP'} 本文文字数(タグ除く)≈{chars}", flush=True)
    return res["id"]

if __name__ == "__main__":
    from komaki_articles_a import ARTICLES_A
    from komaki_articles_b import ARTICLES_B
    ids = []
    for a in ARTICLES_A + ARTICLES_B:
        try:
            ids.append(process(a))
        except Exception as e:
            print(f"  !!! FAILED {a['slug']}: {e}", flush=True)
    print(f"\n完了: {len(ids)}/10 drafts: {ids}", flush=True)
