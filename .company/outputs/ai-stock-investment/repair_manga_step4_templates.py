#!/usr/bin/env python3
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "マンガ版" / "panels" / "comicle_output.csv"

TEXT_ROLES = {
    "導入",
    "前提整理",
    "半導体",
    "クラウド",
    "ソフトウェア",
    "分析",
    "配分",
    "下落",
    "詐欺注意",
    "結論",
    "チェック",
    "図解",
    "ナレーション",
}

TEMPLATE_DESCRIPTIONS = {
    "テンプレ1": "1コマ: ページ全体を使った大ゴマ",
    "テンプレ2": "2コマ: 上下に均等2分割",
    "テンプレ3": "2コマ: 上段小、下段大",
    "テンプレ4": "2コマ: 上段大、下段小",
    "テンプレ5": "3コマ: 上・中・下の3段構成",
    "テンプレ6": "3コマ: 上段1コマ + 下段左右2コマ。読み順は上段、下段右、下段左",
    "テンプレ7": "3コマ: 上段左右2コマ + 下段1コマ。読み順は上段右、上段左、下段",
}

SPECIAL_T1 = {1, 11, 21, 31, 41, 51, 61, 71, 81, 91, 8, 20, 40, 60, 80, 100}
TARGET_COUNTS = {
    "テンプレ1": 16,
    "テンプレ2": 12,
    "テンプレ3": 12,
    "テンプレ4": 12,
    "テンプレ5": 16,
    "テンプレ6": 16,
    "テンプレ7": 16,
}
TEMPLATE_CYCLE = ["テンプレ5", "テンプレ2", "テンプレ6", "テンプレ3", "テンプレ7", "テンプレ4"]


def parse_old_items(value):
    try:
        raw = json.loads(value)
    except json.JSONDecodeError:
        return []
    items = []
    for item in raw:
        if isinstance(item, dict):
            speaker = item.get("speaker") or "ナレーション"
            text = item.get("text") or ""
            items.append((speaker, text))
        elif isinstance(item, list):
            speaker = str(item[0]) if len(item) > 0 else "ナレーション"
            text = str(item[1]) if len(item) > 1 else ""
            items.append((speaker, text))
    return items


def choose_templates(rows):
    counts = Counter()
    assigned = {}
    for row in rows:
        page = int(row["ページ番号"])
        if page in SPECIAL_T1:
            assigned[page] = "テンプレ1"
            counts["テンプレ1"] += 1
    cycle_idx = 0
    for row in rows:
        page = int(row["ページ番号"])
        if page in assigned:
            continue
        for _ in range(len(TEMPLATE_CYCLE) * 2):
            tmpl = TEMPLATE_CYCLE[cycle_idx % len(TEMPLATE_CYCLE)]
            cycle_idx += 1
            if counts[tmpl] < TARGET_COUNTS[tmpl]:
                assigned[page] = tmpl
                counts[tmpl] += 1
                break
        if page not in assigned:
            for tmpl in TARGET_COUNTS:
                if counts[tmpl] < TARGET_COUNTS[tmpl]:
                    assigned[page] = tmpl
                    counts[tmpl] += 1
                    break
    return assigned


def panel_count(template):
    if template == "テンプレ1":
        return 1
    if template in {"テンプレ2", "テンプレ3", "テンプレ4"}:
        return 2
    return 3


def item_type(speaker):
    return "narration" if speaker in TEXT_ROLES else "dialogue"


def to_standard_json(items, template):
    count = panel_count(template)
    if count == 1:
        panel_ids = [1 for _ in items]
    elif count == 2:
        panel_ids = [1 if i < max(1, len(items) // 2) else 2 for i in range(len(items))]
    else:
        panel_ids = [min(3, i + 1) for i in range(len(items))]
        if len(items) >= 4:
            panel_ids[-1] = 3
    out = []
    for (speaker, text), panel_id in zip(items, panel_ids):
        typ = item_type(speaker)
        out.append({
            "panel_id": panel_id,
            "type": typ,
            "speaker": None if typ == "narration" else speaker,
            "text": text.replace('"', "〝"),
        })
    return out


def prompt_for(template, json_items):
    lines = [
        "◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください",
        "◆【絶対最優先】必ずフルカラーにしてください",
        "◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。",
        "◆【出力サイズ】2:3",
        "◆【補足情報】上下左右に50ピクセルの余白を設けてください",
        f"◆【コマ構成】{template}: {TEMPLATE_DESCRIPTIONS[template]}",
        "◆【作画】日本のビジネスマンガ調。清潔感のある線、落ち着いた色調、投資判断を煽らない実務的な演出。",
        "◆【ストーリー】",
    ]
    for item in json_items:
        pos = item["panel_id"]
        text = item["text"]
        if item["type"] == "dialogue":
            lines.append(f"{pos}コマ目: ミナミと高橋がAI株投資の判断軸を会話する。セリフ: {item['speaker']}の吹き出しに「{text}」")
        else:
            lines.append(f"{pos}コマ目: 投資判断の要点を図解・情景で見せる。ナレーション: ［四角枠］{text}")
    return "\n".join(lines)


def main():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    backup = CSV_PATH.with_suffix(".pre_template_repair.csv")
    if not backup.exists():
        shutil.copy2(CSV_PATH, backup)
    assigned = choose_templates(rows)
    out_rows = []
    for row in rows:
        page = int(row["ページ番号"])
        template = assigned[page]
        items = parse_old_items(row["コマ別テキストJSON"])
        json_items = to_standard_json(items, template)
        out_rows.append({
            "ページ番号": page,
            "使用するコマ割りテンプレ": template,
            "漫画作成のプロンプト": prompt_for(template, json_items),
            "コマ別テキストJSON": json.dumps(json_items, ensure_ascii=False),
            "outfit_id": row.get("outfit_id") or "business_default",
        })
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ページ番号", "使用するコマ割りテンプレ", "漫画作成のプロンプト", "コマ別テキストJSON", "outfit_id"])
        writer.writeheader()
        writer.writerows(out_rows)
    counts = Counter(row["使用するコマ割りテンプレ"] for row in out_rows)
    report = ROOT / "MANGA_STEP4_TEMPLATE_REPAIR_REPORT.md"
    report.write_text(
        "# マンガStep 4コマ割り修正レポート\n\n"
        "ebook-to-manga Step 4仕様に合わせ、`4コマ基本` 固定を廃止し、"
        "`テンプレ1〜7` と標準 `コマ別テキストJSON` スキーマへ修正しました。\n\n"
        + "\n".join(f"- {tmpl}: {counts[tmpl]}ページ" for tmpl in sorted(TARGET_COUNTS))
        + f"\n\nバックアップ: `{backup.relative_to(ROOT)}`\n",
        encoding="utf-8",
    )
    print(json.dumps({"rows": len(out_rows), "counts": dict(counts), "backup": str(backup)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
