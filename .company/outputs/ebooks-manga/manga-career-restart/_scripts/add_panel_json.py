"""
add_panel_json.py
=================
manga-career-restart 全4巻の comicle_output.csv（3列）に
4列目「コマ別テキストJSON」を自動生成して追記するスクリプト。

LLM 呼び出しなし。正規表現パースのみ。

usage:
    python add_panel_json.py
"""

import csv
import json
import re
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

# -------------------------------------------------------
# パス設定
# -------------------------------------------------------
BASE_DIR = Path(r"g:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart")
SCRIPTS_DIR = BASE_DIR / "_scripts"
VOLS = ["vol1", "vol2", "vol3", "vol4"]

# -------------------------------------------------------
# 正規表現パターン
# -------------------------------------------------------
# 注意: CSVデータ内では「[」「]」が全角 ［ (U+FF3B) と ］ (U+FF3D) で表記されている。
# 正規表現の \[ \] は半角にしかマッチしないため、
# ブラケット部分は [\\[\\u{FF3B}] ... [\\]\\u{FF3D}] のように
# 半角・全角両方にマッチするクラスを使用する。

# ブラケット文字クラス（半角 [ ] + 全角 ［ ］）
_LB = r'[\[［]'   # [ または ［
_RB = r'[\]］]'   # ] または ］
_CHAR_IN_BRACKET = r'[^\]］]+'  # 括弧内文字（終端ブラケットを除く任意文字）

# コマ区切り（パターン1: 位置あり）
PANEL_WITH_POS = re.compile(r'(\d+)コマ目\s*\(([^)]+)\)[：:]')
# コマ区切り（パターン2: 位置なし）
PANEL_NO_POS = re.compile(r'(\d+)コマ目[：:]')

# ストーリーセクション取得
STORY_SECTION = re.compile(r'◆【ストーリー】(.+?)(?=◆【|$)', re.DOTALL)

# コマブロック全体分割用（コマ番号でスプリット）
PANEL_SPLIT = re.compile(r'(?=\d+コマ目[\s\(])')

# セリフなし
SERIF_NASHI = re.compile(r'セリフ[：:]\s*なし')
# セリフパターン1: [キャラ名]の吹き出しに「テキスト」（半角・全角ブラケット対応）
SERIF_P1 = re.compile(rf'セリフ[：:]\s*{_LB}({_CHAR_IN_BRACKET}){_RB}の吹き出しに「([^」]+)」')
# セリフパターン2: [キャラ名]「テキスト」（括弧省略形）
SERIF_P2 = re.compile(rf'セリフ[：:]\s*{_LB}({_CHAR_IN_BRACKET}){_RB}「([^」]+)」')
# セリフパターン3: [キャラ名]の声を出しに「テキスト」（古い書式）
SERIF_P3 = re.compile(rf'セリフ[：:]\s*{_LB}({_CHAR_IN_BRACKET}){_RB}の声を出しに「([^」]+)」')
# セリフパターン4: 「テキスト」のみ（speaker=null）
SERIF_P4 = re.compile(r'セリフ[：:]\s*「([^」]+)」')

# 複数セリフ対応: コマブロック内から全セリフをまとめて抽出（半角・全角ブラケット対応）
SERIF_MULTI_P1 = re.compile(rf'{_LB}({_CHAR_IN_BRACKET}){_RB}の吹き出しに「([^」]+)」')
SERIF_MULTI_P2 = re.compile(rf'{_LB}({_CHAR_IN_BRACKET}){_RB}「([^」]+)」')
SERIF_MULTI_P3 = re.compile(rf'{_LB}({_CHAR_IN_BRACKET}){_RB}の声を出しに「([^」]+)」')

# ナレーションなし
NARA_NASHI = re.compile(r'ナレーション[：:]\s*なし')
# ナレーションパターン1: [四角枠]テキスト（半角・全角ブラケット対応）
NARA_P1 = re.compile(rf'ナレーション[：:]\s*{_LB}四角枠{_RB}(.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)', re.DOTALL)
# ナレーションパターン2: [ノート]テキスト（古い書式）
NARA_P2 = re.compile(rf'ナレーション[：:]\s*{_LB}ノート{_RB}(.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)', re.DOTALL)
# ナレーションパターン3: 括弧なし
NARA_P3 = re.compile(r'ナレーション[：:]\s*(?!\s*なし)(.+?)(?=\s*オノマトペ[：:]|\s*\d+コマ目|$)', re.DOTALL)

# -------------------------------------------------------
# パネルブロックからコマ番号を取得
# -------------------------------------------------------

def get_panel_id(panel_block: str) -> int:
    """コマブロックの先頭からコマ番号を取得"""
    m = PANEL_WITH_POS.match(panel_block.strip())
    if m:
        return int(m.group(1))
    m = PANEL_NO_POS.match(panel_block.strip())
    if m:
        return int(m.group(1))
    return -1


# -------------------------------------------------------
# セリフ抽出
# -------------------------------------------------------

def extract_dialogues(panel_block: str, panel_id: int, warn_lines: list, page_num: int) -> list:
    """1コマブロックからセリフエントリのリストを返す"""
    entries = []

    # セリフなし
    if SERIF_NASHI.search(panel_block):
        return entries

    # セリフ行を含むか
    has_serif = bool(re.search(r'セリフ[：:]', panel_block))
    if not has_serif:
        return entries

    # パターン1（吹き出し形式）を複数マッチで全件取得
    matches_p1 = SERIF_MULTI_P1.findall(panel_block)
    if matches_p1:
        for speaker, text in matches_p1:
            entries.append({
                "panel_id": panel_id,
                "type": "dialogue",
                "speaker": speaker.strip(),
                "text": text.strip()
            })
        return entries

    # パターン3（声を出しに形式）
    matches_p3 = SERIF_MULTI_P3.findall(panel_block)
    if matches_p3:
        for speaker, text in matches_p3:
            entries.append({
                "panel_id": panel_id,
                "type": "dialogue",
                "speaker": speaker.strip(),
                "text": text.strip()
            })
        return entries

    # パターン2（[キャラ名]「テキスト」括弧省略形）
    matches_p2 = SERIF_MULTI_P2.findall(panel_block)
    if matches_p2:
        for speaker, text in matches_p2:
            entries.append({
                "panel_id": panel_id,
                "type": "dialogue",
                "speaker": speaker.strip(),
                "text": text.strip()
            })
        return entries

    # パターン4: 「テキスト」のみ
    m4 = SERIF_P4.search(panel_block)
    if m4:
        entries.append({
            "panel_id": panel_id,
            "type": "dialogue",
            "speaker": None,
            "text": m4.group(1).strip()
        })
        return entries

    # パターン未ヒット、警告
    warn_lines.append(f"p{page_num} コマ{panel_id}: セリフ記述あるがパース失敗。ブロック={panel_block[:80]!r}")
    return entries


# -------------------------------------------------------
# ナレーション抽出
# -------------------------------------------------------

def extract_narrations(panel_block: str, panel_id: int) -> list:
    """1コマブロックからナレーションエントリのリストを返す"""
    entries = []

    # ナレーションなし
    if NARA_NASHI.search(panel_block):
        return entries

    has_nara = bool(re.search(r'ナレーション[：:]', panel_block))
    if not has_nara:
        return entries

    # パターン1: [四角枠]
    m = NARA_P1.search(panel_block)
    if m:
        text = m.group(1).strip()
        if text:
            entries.append({
                "panel_id": panel_id,
                "type": "narration",
                "speaker": None,
                "text": text
            })
        return entries

    # パターン2: [ノート]
    m = NARA_P2.search(panel_block)
    if m:
        text = m.group(1).strip()
        if text:
            entries.append({
                "panel_id": panel_id,
                "type": "narration",
                "speaker": None,
                "text": text
            })
        return entries

    # パターン3: 括弧なし
    m = NARA_P3.search(panel_block)
    if m:
        text = m.group(1).strip()
        if text:
            entries.append({
                "panel_id": panel_id,
                "type": "narration",
                "speaker": None,
                "text": text
            })
        return entries

    return entries


# -------------------------------------------------------
# 1ページのプロンプト → JSON配列
# -------------------------------------------------------

def parse_prompt_to_json(prompt: str, page_num: int, template: str,
                         warn_lines: list, stats: dict) -> str:
    """
    プロンプト本文からコマ別テキストJSONを生成。
    テキストページは "[]" を返す。
    """
    # テキストページ
    if template.strip() == "テキストページ":
        return "[]"

    # ストーリーセクション取得
    m = STORY_SECTION.search(prompt)
    if not m:
        # ストーリーセクションなし → [] で処理
        stats["no_story"] = stats.get("no_story", 0) + 1
        warn_lines.append(f"p{page_num}: ◆【ストーリー】セクション未検出。[]=設定。")
        return "[]"

    story_text = m.group(1).strip()

    # コマブロックに分割
    # PANEL_SPLIT でコマ番号の前でスプリット
    raw_blocks = PANEL_SPLIT.split(story_text)
    # 空ブロックを除去
    raw_blocks = [b.strip() for b in raw_blocks if b.strip()]

    if not raw_blocks:
        stats["no_panel"] = stats.get("no_panel", 0) + 1
        warn_lines.append(f"p{page_num}: コマブロック0件。[]=設定。")
        return "[]"

    entries = []
    panel_count = 0

    for block in raw_blocks:
        panel_id = get_panel_id(block)
        if panel_id == -1:
            # コマ番号取得失敗
            warn_lines.append(f"p{page_num}: コマ番号取得失敗。ブロック={block[:60]!r}")
            continue

        panel_count += 1

        # セリフ抽出
        dialogue_entries = extract_dialogues(block, panel_id, warn_lines, page_num)
        entries.extend(dialogue_entries)

        # ナレーション抽出
        narration_entries = extract_narrations(block, panel_id)
        entries.extend(narration_entries)

    if panel_count == 0:
        stats["no_panel"] = stats.get("no_panel", 0) + 1

    # 統計更新
    dialogue_count = sum(1 for e in entries if e["type"] == "dialogue")
    narration_count = sum(1 for e in entries if e["type"] == "narration")
    stats["total_dialogue"] = stats.get("total_dialogue", 0) + dialogue_count
    stats["total_narration"] = stats.get("total_narration", 0) + narration_count

    return json.dumps(entries, ensure_ascii=False)


# -------------------------------------------------------
# バックアップ処理
# -------------------------------------------------------

def backup_csv(csv_path: Path) -> Path:
    """
    comicle_output.csv を comicle_output_before_4col.csv にコピー。
    既に存在する場合は _bak2, _bak3 のサフィックスをつける。
    """
    backup_name = csv_path.parent / "comicle_output_before_4col.csv"
    if not backup_name.exists():
        shutil.copy2(csv_path, backup_name)
        print(f"  [backup] {backup_name.name} を作成")
        return backup_name
    else:
        # すでに存在する場合はサフィックス付きで保存
        suffix = 2
        while True:
            alt_name = csv_path.parent / f"comicle_output_before_4col_bak{suffix}.csv"
            if not alt_name.exists():
                shutil.copy2(csv_path, alt_name)
                print(f"  [backup] 既存バックアップあり → {alt_name.name} を作成")
                return alt_name
            suffix += 1


# -------------------------------------------------------
# 1巻処理
# -------------------------------------------------------

def process_vol(vol: str, warn_lines_all: list) -> dict:
    """
    1巻分のCSVを処理して4列化する。
    stats dictを返す。
    """
    csv_path = BASE_DIR / vol / "panels" / "comicle_output.csv"
    warn_log_path = BASE_DIR / vol / "panels" / "parse_warnings.log"

    print(f"\n=== {vol} 処理開始 ===")
    print(f"  CSV: {csv_path}")

    if not csv_path.exists():
        print(f"  [ERROR] CSVが見つかりません: {csv_path}")
        return {}

    # バックアップ
    backup_csv(csv_path)

    # 既存CSVを読み込む
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print(f"  [ERROR] CSVが空です")
        return {}

    header = rows[0]
    data_rows = rows[1:]
    total_pages = len(data_rows)
    print(f"  ページ数: {total_pages}")

    stats = {
        "vol": vol,
        "total_pages": total_pages,
        "text_pages": 0,
        "parsed_ok": 0,
        "parsed_fail": 0,
        "no_panel_pages": [],
        "total_dialogue": 0,
        "total_narration": 0,
        "fail_pages": [],
    }

    warn_lines = []
    new_rows = []

    for row in data_rows:
        if len(row) < 3:
            # 不正な行はスキップ
            new_rows.append(row + ["[]"])
            continue

        page_num = row[0]
        template = row[1]
        prompt = row[2]

        try:
            json_val = parse_prompt_to_json(prompt, page_num, template, warn_lines, stats)
            if template.strip() == "テキストページ":
                stats["text_pages"] += 1
            else:
                # パース結果を確認
                arr = json.loads(json_val)
                # セリフ行があるか確認（プロンプトに「セリフ: なし」以外の記述があるページ）
                # 全てのセリフ記述を取得して、1つでも「なし」以外があればTrue
                all_serif_mentions = re.findall(r'セリフ[：:]\s*(.+?)(?=\s*ナレーション[：:]|\s*オノマトペ[：:]|\s*\d+コマ目|$)', prompt, re.DOTALL)
                has_actual_serif = any(
                    s.strip() and not s.strip().startswith('なし')
                    for s in all_serif_mentions
                )
                if has_actual_serif and len(arr) == 0:
                    stats["parsed_fail"] += 1
                    stats["fail_pages"].append(page_num)
                else:
                    stats["parsed_ok"] += 1

            new_rows.append(row + [json_val])
        except Exception as e:
            warn_lines.append(f"p{page_num}: 例外発生 {e}")
            new_rows.append(row + ["[]"])
            stats["parsed_fail"] += 1
            stats["fail_pages"].append(page_num)

    # ヘッダー処理
    if len(header) == 3:
        new_header = header + ["コマ別テキストJSON"]
    elif len(header) >= 4:
        new_header = header[:4]
        new_header[3] = "コマ別テキストJSON"
    else:
        new_header = header + ["コマ別テキストJSON"]

    # 書き込み（UTF-8、クオート全フィールド）
    with open(csv_path, encoding="utf-8", newline="") as f:
        # 改行スタイルを確認
        raw = f.read(1024)
        if "\r\n" in raw:
            line_terminator = "\r\n"
        else:
            line_terminator = "\n"

    with open(csv_path, encoding="utf-8", newline="", mode="w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator=line_terminator)
        writer.writerow(new_header)
        writer.writerows(new_rows)

    # 警告ログ出力
    with open(warn_log_path, encoding="utf-8", mode="w") as f:
        f.write(f"# parse_warnings.log - {vol} - {datetime.now().isoformat()}\n\n")
        if warn_lines:
            for line in warn_lines:
                f.write(line + "\n")
        else:
            f.write("警告なし\n")

    # 全体警告リストにも追加
    warn_lines_all.extend(warn_lines)

    # パース失敗率
    non_text = total_pages - stats["text_pages"]
    fail_rate = stats["parsed_fail"] / non_text if non_text > 0 else 0

    print(f"  テキストページ: {stats['text_pages']}")
    print(f"  通常ページ: {non_text} (パース成功: {stats['parsed_ok']}, 失敗: {stats['parsed_fail']})")
    print(f"  パース失敗率: {fail_rate:.1%}")
    print(f"  セリフ抽出総数: {stats['total_dialogue']}")
    print(f"  ナレーション抽出総数: {stats['total_narration']}")
    if stats["fail_pages"]:
        print(f"  失敗ページ: {stats['fail_pages']}")

    if fail_rate >= 0.05:
        print(f"  [WARNING] パース失敗率が5%以上です ({fail_rate:.1%}) - 確認が必要")

    return stats


# -------------------------------------------------------
# 検証
# -------------------------------------------------------

def verify_vol(vol: str) -> dict:
    """4列化されたCSVを検証する"""
    csv_path = BASE_DIR / vol / "panels" / "comicle_output.csv"

    result = {
        "vol": vol,
        "total_rows": 0,
        "ok_4col": 0,
        "json_parse_ok": 0,
        "text_page_ok": 0,
        "has_entry_pages": 0,
        "errors": []
    }

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = rows[0]
    data_rows = rows[1:]
    result["total_rows"] = len(data_rows)

    for row in data_rows:
        if len(row) != 4:
            result["errors"].append(f"p{row[0] if row else '?'}: 列数={len(row)}")
            continue
        result["ok_4col"] += 1

        page_num, template, prompt, json_val = row

        # JSONパース
        try:
            arr = json.loads(json_val)
            result["json_parse_ok"] += 1
        except Exception as e:
            result["errors"].append(f"p{page_num}: JSON parse error: {e}")
            continue

        # テキストページ確認
        if template.strip() == "テキストページ":
            if arr == []:
                result["text_page_ok"] += 1
            else:
                result["errors"].append(f"p{page_num}: テキストページだが[]でない: {json_val[:50]}")
            continue

        # セリフ有ページの抽出チェック
        if len(arr) > 0:
            result["has_entry_pages"] += 1

        # スキーマチェック
        for entry in arr:
            required_keys = {"panel_id", "type", "speaker", "text"}
            if not required_keys.issubset(entry.keys()):
                result["errors"].append(f"p{page_num}: スキーマ不正 {entry}")
            if entry.get("type") not in ("dialogue", "narration"):
                result["errors"].append(f"p{page_num}: type不正 {entry.get('type')}")

    return result


# -------------------------------------------------------
# サンプルCSV出力（vol1冒頭10ページ）
# -------------------------------------------------------

def save_sample_vol1():
    csv_path = BASE_DIR / "vol1" / "panels" / "comicle_output.csv"
    sample_path = SCRIPTS_DIR / "sample_vol1_head10.csv"

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # ヘッダー + 最初の10データ行
    sample_rows = rows[:11]

    with open(sample_path, encoding="utf-8", newline="", mode="w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(sample_rows)

    print(f"\nサンプルCSV保存: {sample_path}")


# -------------------------------------------------------
# レポート保存
# -------------------------------------------------------

def save_report(all_stats: list, all_verify: list):
    report_path = SCRIPTS_DIR / "4col_conversion_report.md"

    lines = []
    lines.append(f"# 4列化変換レポート")
    lines.append(f"実行日時: {datetime.now().isoformat()}\n")

    # 全体サマリー
    total_pages = sum(s.get("total_pages", 0) for s in all_stats)
    total_text = sum(s.get("text_pages", 0) for s in all_stats)
    total_ok = sum(s.get("parsed_ok", 0) for s in all_stats)
    total_fail = sum(s.get("parsed_fail", 0) for s in all_stats)
    total_dialogue = sum(s.get("total_dialogue", 0) for s in all_stats)
    total_narration = sum(s.get("total_narration", 0) for s in all_stats)
    non_text_total = total_pages - total_text
    overall_fail_rate = total_fail / non_text_total if non_text_total > 0 else 0

    lines.append("## 全体サマリー\n")
    lines.append(f"| 項目 | 値 |")
    lines.append(f"|---|---|")
    lines.append(f"| 総ページ数 | {total_pages} |")
    lines.append(f"| テキストページ | {total_text} |")
    lines.append(f"| 通常ページ | {non_text_total} |")
    lines.append(f"| パース成功 | {total_ok} |")
    lines.append(f"| パース失敗 | {total_fail} |")
    lines.append(f"| 失敗率 | {overall_fail_rate:.1%} |")
    lines.append(f"| セリフ抽出総数 | {total_dialogue} |")
    lines.append(f"| ナレーション抽出総数 | {total_narration} |")
    lines.append("")

    if overall_fail_rate >= 0.05:
        lines.append(f"**[警告] 全体パース失敗率が5%以上です ({overall_fail_rate:.1%})**\n")

    lines.append("## 巻別詳細\n")
    for s in all_stats:
        vol = s.get("vol", "unknown")
        tp = s.get("total_pages", 0)
        txt = s.get("text_pages", 0)
        non_txt = tp - txt
        ok = s.get("parsed_ok", 0)
        fail = s.get("parsed_fail", 0)
        rate = fail / non_txt if non_txt > 0 else 0
        dl = s.get("total_dialogue", 0)
        na = s.get("total_narration", 0)
        fail_pages = s.get("fail_pages", [])

        lines.append(f"### {vol}\n")
        lines.append(f"| 項目 | 値 |")
        lines.append(f"|---|---|")
        lines.append(f"| 総ページ数 | {tp} |")
        lines.append(f"| テキストページ | {txt} |")
        lines.append(f"| 通常ページ | {non_txt} |")
        lines.append(f"| パース成功 | {ok} |")
        lines.append(f"| パース失敗 | {fail} |")
        lines.append(f"| 失敗率 | {rate:.1%} |")
        lines.append(f"| セリフ抽出数 | {dl} |")
        lines.append(f"| ナレーション抽出数 | {na} |")
        lines.append("")
        if fail_pages:
            lines.append(f"失敗ページ番号: {fail_pages}\n")
        else:
            lines.append(f"失敗ページ: なし\n")

    lines.append("## 検証結果\n")
    for v in all_verify:
        vol = v.get("vol", "unknown")
        total_r = v.get("total_rows", 0)
        ok_4col = v.get("ok_4col", 0)
        json_ok = v.get("json_parse_ok", 0)
        txt_ok = v.get("text_page_ok", 0)
        has_entry = v.get("has_entry_pages", 0)
        errors = v.get("errors", [])

        lines.append(f"### {vol}\n")
        lines.append(f"| 検証項目 | 結果 |")
        lines.append(f"|---|---|")
        lines.append(f"| 総行数 | {total_r} |")
        lines.append(f"| 4列完備 | {ok_4col}/{total_r} |")
        lines.append(f"| JSONパース成功 | {json_ok}/{total_r} |")
        lines.append(f"| テキストページ[]確認 | {txt_ok} |")
        lines.append(f"| 1エントリ以上のページ | {has_entry} |")
        lines.append("")
        if errors:
            lines.append(f"エラー件数: {len(errors)}")
            for e in errors[:20]:
                lines.append(f"- {e}")
            if len(errors) > 20:
                lines.append(f"- ... 他 {len(errors)-20} 件")
            lines.append("")
        else:
            lines.append(f"エラーなし\n")

    report_text = "\n".join(lines)
    with open(report_path, encoding="utf-8", mode="w") as f:
        f.write(report_text)

    print(f"\nレポート保存: {report_path}")
    return report_path


# -------------------------------------------------------
# メイン
# -------------------------------------------------------

def main():
    print("=" * 60)
    print("manga-career-restart CSV 4列化スクリプト")
    print(f"実行日時: {datetime.now().isoformat()}")
    print("=" * 60)

    warn_lines_all = []
    all_stats = []
    all_verify = []

    # 全巻処理
    for vol in VOLS:
        stats = process_vol(vol, warn_lines_all)
        if stats:
            all_stats.append(stats)

    # 全体パース失敗率チェック
    total_pages_all = sum(s.get("total_pages", 0) for s in all_stats)
    total_text_all = sum(s.get("text_pages", 0) for s in all_stats)
    total_fail_all = sum(s.get("parsed_fail", 0) for s in all_stats)
    non_text_all = total_pages_all - total_text_all
    overall_fail_rate = total_fail_all / non_text_all if non_text_all > 0 else 0

    if overall_fail_rate >= 0.05:
        print(f"\n[CRITICAL WARNING] 全巻合計パース失敗率 {overall_fail_rate:.1%} >= 5%")
        print("処理は続行しますが、失敗ページを確認してください。")

    # 検証
    print("\n" + "=" * 60)
    print("検証フェーズ")
    print("=" * 60)
    for vol in VOLS:
        print(f"\n--- {vol} 検証 ---")
        verify_result = verify_vol(vol)
        all_verify.append(verify_result)
        print(f"  4列: {verify_result['ok_4col']}/{verify_result['total_rows']}")
        print(f"  JSON OK: {verify_result['json_parse_ok']}/{verify_result['total_rows']}")
        print(f"  テキストページ[]: {verify_result['text_page_ok']}")
        print(f"  エントリ有ページ: {verify_result['has_entry_pages']}")
        if verify_result["errors"]:
            print(f"  エラー: {len(verify_result['errors'])}件")
            for e in verify_result["errors"][:5]:
                print(f"    - {e}")

    # サンプルCSV保存
    save_sample_vol1()

    # レポート保存
    report_path = save_report(all_stats, all_verify)

    print("\n" + "=" * 60)
    print("完了")
    print(f"総ページ: {total_pages_all}, 失敗率: {overall_fail_rate:.1%}")
    print("=" * 60)


if __name__ == "__main__":
    main()
