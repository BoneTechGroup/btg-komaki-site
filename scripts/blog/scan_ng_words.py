# -*- coding: utf-8 -*-
"""効果保証・誇大表現のサイト全体スキャン（本文・タイトル・抜粋）"""
import json, base64, urllib.request, sys, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://sekkotsuin-komaki.com"
import os
CRED = base64.b64encode(f"{os.environ['WP_USER_KOMAKI']}:{os.environ['WP_APP_PASSWORD_KOMAKI']}".encode()).decode()  # 環境変数に設定して使用

NG_PATTERNS = [
    r"劇的",
    r"ミリ単位で治",
    r"即効",           # 即効解消/即効改善/即効性
    r"必ず(良く|改善|治)",
    r"完治",
    r"治ります",
    r"治します",
    r"絶対に(治|改善)",
    r"100%",
    r"確実に(治|改善)",
    r"どんな(症状|痛み)でも",
    r"二度と(痛|再発)",
    r"再発しない",
    r"繰り返さない",
    r"魔法のよう",
    r"奇跡",
    r"日本一|地域No\.?1|唯一",
]

def api(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Basic {CRED}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

items = []
for t in ("pages", "posts"):
    page_n = 1
    while True:
        batch = api(f"/wp-json/wp/v2/{t}?per_page=100&page={page_n}&status=publish,draft&context=edit&_fields=id,link,title,content,excerpt,type,status")
        items += batch
        if len(batch) < 100: break
        page_n += 1

print(f"検査対象: {len(items)}件（ページ+投稿、下書き含む）\n")
total = 0
for it in items:
    hits = []
    fields = {
        "TITLE": it["title"]["raw"],
        "BODY": re.sub(r"<[^>]+>", "", it["content"]["raw"]),
        "EXCERPT": re.sub(r"<[^>]+>", "", it["excerpt"]["raw"]),
    }
    for fname, text in fields.items():
        for pat in NG_PATTERNS:
            for m in re.finditer(pat, text):
                s = max(0, m.start() - 25)
                ctx = text[s:m.end() + 25].replace("\n", " ")
                hits.append(f"  [{fname}] {pat} → …{ctx}…")
    if hits:
        total += len(hits)
        print(f"### {it['id']} [{it['type']}/{it['status']}] {it['link'].replace(BASE,'')} {it['title']['raw'][:40]}")
        for h in hits:
            print(h)
        print()
print(f"合計ヒット: {total}")
