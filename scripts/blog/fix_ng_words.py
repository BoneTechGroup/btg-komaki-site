# -*- coding: utf-8 -*-
"""効果保証・誇大表現の一括修正（本文・タイトル・SEOメタ）"""
import json, base64, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://sekkotsuin-komaki.com"
import os
CRED = base64.b64encode(f"{os.environ['WP_USER_KOMAKI']}:{os.environ['WP_APP_PASSWORD_KOMAKI']}".encode()).decode()  # 環境変数に設定して使用

def api_get(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": f"Basic {CRED}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def api_post(path, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, method="POST",
          headers={"Authorization": f"Basic {CRED}", "Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

# ページID: [(旧, 新), ...]  本文・タイトル・メタ全てに適用
FIXES = {
  1717: [("痛みの即効改善を目指す施術", "痛みの早期改善を目指す施術"),
         ("再発しない身体づくりを設計します", "再発しにくい身体づくりを設計します")],
  235:  [("しっかり完治するまで通院することができました", "納得できるまで通院することができました")],
  302:  [("激痛を即効解消", "激痛の早期改善へ"),
         ("ぎっくり腰即効改善", "ぎっくり腰の早期改善")],
  301:  [("背中の血流が劇的に改善し", "背中の血流が促進され")],
  300:  [("ハイボルテージ施術」で即効除痛", "ハイボルテージ施術」で早期の痛み軽減を目指します")],
  299:  [("痛みを繰り返さないためのトータルケア", "痛みを繰り返しにくくするためのトータルケア")],
  297:  [("再発しない身体環境を作ります", "再発しにくい身体環境づくりを目指します"),
         ("完全回復への唯一の道です", "早期改善への近道です")],
  304:  [("神経の圧迫を即効性を持って緩和します", "神経の圧迫による症状の早期緩和を目指します")],
  305:  [("即効性のあるアプローチを行います", "早期の変化を目指すアプローチを行います")],
  307:  [("ハイボルテージによる炎症の即効ケア", "ハイボルテージによる炎症の集中ケア"),
         ("再発を繰り返さないために", "再発を予防するために")],
  310:  [("組織の修復スピードを劇的に高めます", "組織の修復を積極的にサポートします")],
  311:  [("組織の修復を劇的に早めます", "組織の回復を促します"),
         ("超音波による炎症の即効ケア", "超音波による炎症の集中ケア")],
  314:  [("筋肉の再生スピードを劇的に高めます", "筋肉の再生を積極的に促します"),
         ("完治まで数ヶ月を要する大怪我", "回復まで数ヶ月を要する大怪我")],
  296:  [("組織の修復スピードを劇的に高めます", "組織の修復を積極的にサポートします")],
  316:  [("深部の硬直を即効で緩め、アゴの痛みを劇的に和らげます", "深部の硬直にアプローチし、アゴの痛みの緩和を目指します")],
  283:  [("痛みを即効ケアします", "痛みの早期ケアを行います")],
  286:  [("深部の痛みへ即効アプローチします", "深部の痛みへ集中的にアプローチします")],
  288:  [("激しい痛みと腫れを即効性を持って鎮めます", "激しい痛みと腫れの早期沈静を目指します")],
  289:  [("完治まで集中していただけます", "改善まで集中していただけます")],
  294:  [("頭痛の頻度が劇的に減少するだけでなく", "頭痛の頻度の軽減が期待できるだけでなく")],
  293:  [("激痛を即効解消", "激痛の早期改善へ"),
         ("炎症を劇的に鎮め", "炎症の沈静を促し"),
         ("動かせる範囲を広げる即効ケアを提供しています", "動かせる範囲を広げる早期ケアを提供しています")],
  292:  [("絶妙な圧で血流を劇的に改善し", "絶妙な圧で血流を促進し"),
         ("その場で肩が軽くなる即効性を実感いただけます", "肩の軽さを実感される方が多くいます（個人差があります）"),
         ("再発しない身体作りを目指します", "再発しにくい身体作りを目指します")],
  291:  [("早期受診が完治の近道です", "早期受診が回復への近道です")],
  290:  [("完治までリハビリに専念いただけます", "回復までリハビリに専念いただけます")],
  281:  [("不調を繰り返さない身体へ", "不調を繰り返しにくい身体へ"),
         ("膝痛の劇的な改善", "膝痛の改善サポート")],
  278:  [("完治するまで、安心して治療に専念いただけます", "回復まで、安心して治療に専念いただけます")],
  236:  [("痛みの即効改善なら", "痛みの早期改善を目指すなら"),
         ("血流を劇的に改善", "血流を強力に促進"),
         ("驚きの即効性を提供しています", "早期の変化を実感される方が多い施術です（個人差があります）")],
  49:   [("筋肉の炎症を劇的に鎮めます", "筋肉の炎症の沈静を図ります")],
}

total_applied, not_found = 0, []
for pid, pairs in FIXES.items():
    p = api_get(f"/wp-json/wp/v2/pages/{pid}?context=edit")
    content = p["content"]["raw"]
    title = p["title"]["raw"]
    excerpt = p["excerpt"]["raw"]
    meta = p.get("meta") or {}
    ssp_t = meta.get("ssp_meta_description", "") or ""
    ssp_title = meta.get("ssp_meta_title", "") or ""
    changed = {"content": False, "title": False, "excerpt": False, "meta": False}
    for old, new in pairs:
        found = False
        if old in content:
            content = content.replace(old, new); changed["content"] = True; found = True
        if old in title:
            title = title.replace(old, new); changed["title"] = True; found = True
        if old in excerpt:
            excerpt = excerpt.replace(old, new); changed["excerpt"] = True; found = True
        if old in ssp_t:
            ssp_t = ssp_t.replace(old, new); changed["meta"] = True; found = True
        if old in ssp_title:
            ssp_title = ssp_title.replace(old, new); changed["meta"] = True; found = True
        if found:
            total_applied += 1
        else:
            not_found.append(f"{pid}: {old[:30]}")
    data = {}
    if changed["content"]: data["content"] = content
    if changed["title"]: data["title"] = title
    if changed["excerpt"]: data["excerpt"] = excerpt
    if changed["meta"]: data["meta"] = {"ssp_meta_description": ssp_t, "ssp_meta_title": ssp_title}
    if data:
        api_post(f"/wp-json/wp/v2/pages/{pid}", data)
        print(f"{pid}: 更新 {list(data.keys())}")

print(f"\n適用: {total_applied}件")
if not_found:
    print("見つからなかった置換:")
    for n in not_found:
        print(" ", n)
