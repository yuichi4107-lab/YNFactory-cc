#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_generator.py
====================

「無料ミニ診断」の記入済みスコアシート（CSV）と院情報（JSON）から、
顧客名入りの無料ミニ診断レポート（HTML）を生成するツール。

- Python標準ライブラリのみで動作（外部パッケージ不要）
- スコア計算ロジックは `スコア算定基準.md`（2026-07-12版。基礎点8/5/3・満点10点）に従う
- 出力の分量は無料ミニ診断のスコープ（10問・4AI・競合2〜3院・改善ポイント3つ）に固定する

使い方:
    python report_generator.py --scoresheet <記入済みスコアシートCSV> --client <院情報JSON> --out <出力HTMLパス>

    架空データ・テストデータで生成する場合は --test を付けると、
    レポート上部に「テスト生成（架空データ）」の注記バナーが表示される。
    本番（実顧客）向けに生成する場合は --test を付けないこと（バナーは出ない）。

詳細な入力フォーマットは同フォルダの `使い方.md` を参照。
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# 無料ミニ診断で対象とする4AI（この順序で表・按分計算を行う。追加・削除しない）
AI_ORDER = ["ChatGPT", "Gemini", "Perplexity", "Google AI Overviews"]

# 無料ミニ診断のスコープ上限（要件定義書のスコープ定義に厳密に一致させる）
FREE_SCOPE_QUESTIONS = 10
FREE_SCOPE_MIN_COMPETITORS = 2
FREE_SCOPE_MAX_COMPETITORS = 3
FREE_SCOPE_IMPROVEMENTS = 3

CONTACT_EMAIL = "y-nakada@yn-factory.com"
SIGNATURE = "YNファクトリー 担当: 中田"

REQUIRED_CSV_COLUMNS = [
    "院名", "AI種別", "質問No", "質問カテゴリ", "質問文", "実施日時",
    "言及有無", "推薦順位", "引用元種別", "引用元詳細", "誤情報有無",
    "誤情報内容", "質問別素点", "再実施フラグ", "再実施理由", "備考",
]


class ScoreDataError(ValueError):
    """スコアシート・院情報の内容が算定基準に合致しない場合に送出する。"""


# ---------------------------------------------------------------------------
# 正規化・点数化ロジック（スコア算定基準.md 1〜4章に対応）
# ---------------------------------------------------------------------------

def normalize_mention(raw: str) -> str:
    """「言及有無」欄を "あり" / "なし" / "AI Overview非表示" / "実測不可" / "未実施" に正規化する。"""
    s = (raw or "").strip()
    if s == "あり":
        return "あり"
    if s == "なし":
        return "なし"
    if "AI Overview非表示" in s or "非表示" in s:
        return "AI Overview非表示"
    if "実測不可" in s:
        return "実測不可"
    if s == "":
        return "未実施"
    raise ScoreDataError(f"未知の「言及有無」表記です: {raw!r}")


def normalize_rank(raw: str) -> str:
    """「推薦順位」欄を基準の3区分＋対象外に正規化する（早見表 2-5節）。"""
    s = (raw or "").strip()
    if "1位" in s:
        return "1位相当"
    if "2" in s and "3" in s:
        return "2〜3位相当"
    if "言及のみ" in s:
        return "言及のみ"
    if "対象外" in s or s == "":
        return "対象外"
    raise ScoreDataError(f"未知の「推薦順位」表記です: {raw!r}")


def normalize_citation(raw: str) -> str:
    """「引用元種別」欄を一次情報／二次情報／引用なしに正規化する（1-③節）。"""
    s = (raw or "").strip()
    if "一次" in s:
        return "一次情報"
    if "二次" in s:
        return "二次情報"
    if "引用なし" in s or s == "":
        return "引用なし"
    raise ScoreDataError(f"未知の「引用元種別」表記です: {raw!r}")


def normalize_misinfo(raw: str) -> bool:
    """「誤情報有無」欄を真偽値に正規化する（1-④節）。"""
    s = (raw or "").strip()
    if s == "あり":
        return True
    if s == "なし" or s == "":
        return False
    raise ScoreDataError(f"未知の「誤情報有無」表記です: {raw!r}")


BASE_POINTS = {"1位相当": 8, "2〜3位相当": 5, "言及のみ": 3}
CITATION_POINTS = {"一次情報": 2, "二次情報": 1, "引用なし": 0}


def compute_question_score(mention_raw: str, rank_raw: str, citation_raw: str,
                            misinfo_raw: str) -> tuple[Optional[int], str]:
    """質問1問分の素点（0〜10点）を算出する。スコア算定基準.md 2章の計算式そのもの。

    戻り値: (素点 または None(=按分対象外), 正規化済み言及有無)
    """
    mention = normalize_mention(mention_raw)

    if mention in ("実測不可", "未実施"):
        return None, mention

    if mention in ("なし", "AI Overview非表示"):
        # 言及なし、またはAI Overview非表示 → 0点（算定基準 1-①節末尾・2-1節）
        return 0, mention

    # ここに来るのは mention == "あり" のケースのみ
    rank = normalize_rank(rank_raw)
    if rank not in BASE_POINTS:
        raise ScoreDataError(
            f"言及有無が「あり」なのに推薦順位が不正です（対象外のまま）: {rank_raw!r}")
    base = BASE_POINTS[rank]

    citation = normalize_citation(citation_raw)
    cite_pt = CITATION_POINTS[citation]

    misinfo = normalize_misinfo(misinfo_raw)
    penalty = 3 if misinfo else 0

    score = base + cite_pt - penalty
    score = max(0, min(10, score))  # 算定基準 2-1節: 下限0点・上限10点でクリップ
    return score, mention


def round_half_up(value: float, ndigits: int = 0):
    """四捨五入（Pythonの round() は銀行丸めのため使わない）。"""
    quant = Decimal("1") if ndigits == 0 else Decimal("1." + "0" * ndigits)
    d = Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP)
    return int(d) if ndigits == 0 else float(d)


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------

@dataclass
class QuestionRow:
    question_no: str
    category: str
    question_text: str
    mention: str  # 正規化済み: あり/なし/AI Overview非表示/実測不可/未実施
    rank_raw: str
    citation_raw: str
    misinfo_raw: str
    score: Optional[int]  # None = 按分対象外（実測不可・未実施）


@dataclass
class AIResult:
    name: str
    rows: list = field(default_factory=list)  # list[QuestionRow]
    excluded: bool = False
    exclude_reason: str = ""

    @property
    def counted_rows(self):
        return [r for r in self.rows if r.score is not None]

    @property
    def n_conducted(self) -> int:
        return len(self.counted_rows)

    @property
    def n_mentioned(self) -> int:
        return len([r for r in self.rows if r.mention == "あり"])

    @property
    def ai_score(self) -> Optional[float]:
        if self.excluded or self.n_conducted == 0:
            return None
        total = sum(r.score for r in self.counted_rows)
        return total / (self.n_conducted * 10) * 100

    def citation_summary(self) -> str:
        mentioned = [r for r in self.rows if r.mention == "あり"]
        if not mentioned:
            return "―（言及なしのため該当なし）"
        counts = {"一次情報": 0, "二次情報": 0, "引用なし": 0}
        for r in mentioned:
            counts[normalize_citation(r.citation_raw)] += 1
        return (f"一次情報{counts['一次情報']}件 / "
                f"二次情報{counts['二次情報']}件 / "
                f"引用なし{counts['引用なし']}件")

    def rank_summary(self) -> str:
        mentioned_ranks = {normalize_rank(r.rank_raw) for r in self.rows if r.mention == "あり"}
        if "1位相当" in mentioned_ranks:
            return "1位相当あり"
        if "2〜3位相当" in mentioned_ranks:
            return "2〜3位相当"
        if "言及のみ" in mentioned_ranks:
            return "言及のみ（順位性なし）"
        return "圏外（言及なし）"


# ---------------------------------------------------------------------------
# CSV読み込み・集計
# ---------------------------------------------------------------------------

def load_scoresheet(path: Path) -> dict:
    """スコアシートCSVを読み込み、AIごとのAIResultを返す。"""
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_CSV_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ScoreDataError(
                f"スコアシートCSVに必須列が不足しています: {', '.join(missing)}")
        rows = list(reader)

    if not rows:
        raise ScoreDataError("スコアシートCSVにデータ行がありません。")

    ai_results: dict[str, AIResult] = {name: AIResult(name=name) for name in AI_ORDER}
    unknown_ai = set()

    for raw_row in rows:
        ai_name = (raw_row.get("AI種別") or "").strip()
        if not ai_name:
            continue  # 空行はスキップ
        if ai_name not in ai_results:
            unknown_ai.add(ai_name)
            continue
        score, mention = compute_question_score(
            raw_row.get("言及有無", ""),
            raw_row.get("推薦順位", ""),
            raw_row.get("引用元種別", ""),
            raw_row.get("誤情報有無", ""),
        )
        q = QuestionRow(
            question_no=(raw_row.get("質問No") or "").strip(),
            category=(raw_row.get("質問カテゴリ") or "").strip(),
            question_text=(raw_row.get("質問文") or "").strip(),
            mention=mention,
            rank_raw=raw_row.get("推薦順位", ""),
            citation_raw=raw_row.get("引用元種別", ""),
            misinfo_raw=raw_row.get("誤情報有無", ""),
            score=score,
        )
        ai_results[ai_name].rows.append(q)

    if unknown_ai:
        raise ScoreDataError(
            f"スコアシートに未知のAI種別があります（{', '.join(AI_ORDER)} のいずれかにしてください）: "
            f"{', '.join(sorted(unknown_ai))}")

    for ai_name, result in ai_results.items():
        if len(result.rows) == 0:
            raise ScoreDataError(f"「{ai_name}」の実施行が1件もありません。")
        if len(result.rows) > FREE_SCOPE_QUESTIONS:
            raise ScoreDataError(
                f"「{ai_name}」の質問行数が{len(result.rows)}件あります。"
                f"無料ミニ診断は1AIあたり{FREE_SCOPE_QUESTIONS}問までのスコープです。")
        if all(r.mention == "実測不可" for r in result.rows):
            result.excluded = True

    return ai_results


def collect_misinfo_list(ai_results: dict) -> list[dict]:
    """誤情報ありと記録された行を一覧化する（改善提案・レポート「誤情報一覧」用）。"""
    items = []
    for ai_name in AI_ORDER:
        result = ai_results[ai_name]
        for r in result.rows:
            if r.mention == "あり" and normalize_misinfo(r.misinfo_raw):
                items.append({
                    "ai": ai_name,
                    "question_no": r.question_no,
                    "category": r.category,
                })
    return items


def compute_overall_score(ai_results: dict) -> tuple[Optional[int], list[str]]:
    """総合スコア（実施できたAIのAI別スコアの単純平均・四捨五入）を算出する。"""
    included_scores = []
    excluded_names = []
    for ai_name in AI_ORDER:
        result = ai_results[ai_name]
        score = result.ai_score
        if score is None:
            excluded_names.append(ai_name)
        else:
            included_scores.append(score)
    if not included_scores:
        return None, excluded_names
    avg = sum(included_scores) / len(included_scores)
    return round_half_up(avg), excluded_names


# ---------------------------------------------------------------------------
# 院情報（クライアントJSON）読み込み・検証
# ---------------------------------------------------------------------------

def load_client_info(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    required_keys = ["院名", "地域", "強み症状", "実施日", "競合", "改善ポイント"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ScoreDataError(f"院情報JSONに必須項目が不足しています: {', '.join(missing)}")

    competitors = data["競合"]
    if not isinstance(competitors, list) or not (
            FREE_SCOPE_MIN_COMPETITORS <= len(competitors) <= FREE_SCOPE_MAX_COMPETITORS):
        raise ScoreDataError(
            f"「競合」は{FREE_SCOPE_MIN_COMPETITORS}〜{FREE_SCOPE_MAX_COMPETITORS}院で指定してください"
            f"（現在{len(competitors) if isinstance(competitors, list) else '不正な形式'}）。")
    for c in competitors:
        if "院名" not in c or "所在地" not in c:
            raise ScoreDataError("「競合」の各項目には「院名」「所在地」が必要です。")

    improvements = data["改善ポイント"]
    if not isinstance(improvements, list) or len(improvements) != FREE_SCOPE_IMPROVEMENTS:
        raise ScoreDataError(
            f"「改善ポイント」は無料ミニ診断のスコープ上、必ず{FREE_SCOPE_IMPROVEMENTS}項目にしてください"
            f"（現在{len(improvements) if isinstance(improvements, list) else '不正な形式'}）。")

    data.setdefault("実測不可AI理由", {})
    data.setdefault("送付先", "")
    return data


# ---------------------------------------------------------------------------
# HTML生成
# ---------------------------------------------------------------------------

def esc(value) -> str:
    return html.escape(str(value), quote=True)


def render_html(client: dict, ai_results: dict, overall_score: Optional[int],
                 excluded_ais: list, misinfo_items: list, test_mode: bool) -> str:
    inst = esc(client["院名"])
    region = esc(client["地域"])
    strength = esc(client["強み症状"])
    exec_date = esc(client["実施日"])

    test_banner = ""
    if test_mode:
        test_banner = (
            '<div class="test-banner">'
            '※本レポートはテストデータ（架空データ）による生成確認用です。実在の店舗とは関係ありません。'
            '</div>'
        )

    # --- 診断サマリー ---
    if overall_score is None:
        score_html = '<div class="num">集計不可</div><div class="label">全AIが実測不可のため総合スコアを算出できませんでした</div>'
        summary_text = (
            f"{inst}様について、AI検索{FREE_SCOPE_QUESTIONS}問（おすすめ／比較／料金／口コミ・評判／近くの、"
            f"の5カテゴリ×各2問）でのAI検索露出状況を確認しましたが、対象AIすべてが実測不可のため、"
            f"総合スコアの算出には至りませんでした。詳細は下記「対象AI」欄をご確認ください。")
    else:
        level = "要改善" if overall_score < 50 else ("普通" if overall_score < 75 else "良好")
        score_html = f'<div class="num">{overall_score} / 100</div><div class="label">総合AI検索露出スコア（{esc(level)}レベル）</div>'
        summary_text = (
            f"「{region}＋整体（接骨）」「{strength}＋おすすめ」等、来店前に想定される検索文脈をもとに、"
            f"AI検索{FREE_SCOPE_QUESTIONS}問（おすすめ／比較／料金／口コミ・評判／近くの、の5カテゴリ×各2問）を"
            f"主要AI検索サービスに投げかけ、{inst}様が言及・引用・推薦される状況を、"
            f"ヒアリングでお伺いした競合{len(client['競合'])}院と簡易比較しました。")

    excluded_note = ""
    if excluded_ais:
        reasons = client.get("実測不可AI理由", {})
        items = "".join(
            f"<li>{esc(name)}：{esc(reasons.get(name, '理由未記録'))}のため今回は実測不可でした。</li>"
            for name in excluded_ais
        )
        excluded_note = f'<p class="sub-note">対象AIのうち一部は実測できませんでした。</p><ul class="sub-note">{items}</ul>'

    # --- AI別スコア表 ---
    ai_rows_html = []
    for ai_name in AI_ORDER:
        result = ai_results[ai_name]
        if result.excluded:
            reason = client.get("実測不可AI理由", {}).get(ai_name, "理由未記録")
            ai_rows_html.append(
                f"<tr><td>{esc(ai_name)}</td><td colspan='4'>実測不可（{esc(reason)}）</td></tr>"
            )
            continue
        score = result.ai_score
        score_disp = round_half_up(score) if score is not None else "―"
        ai_rows_html.append(
            "<tr>"
            f"<td>{esc(ai_name)}</td>"
            f"<td>{result.n_mentioned} / {result.n_conducted}</td>"
            f"<td>{esc(result.citation_summary())}</td>"
            f"<td>{esc(result.rank_summary())}</td>"
            f"<td>{score_disp} / 100</td>"
            "</tr>"
        )
    ai_table_html = "\n".join(ai_rows_html)

    # --- 競合比較表 ---
    included_results = [r for r in ai_results.values() if not r.excluded]
    total_conducted = sum(r.n_conducted for r in included_results)
    total_mentioned = sum(r.n_mentioned for r in included_results)
    self_note = (
        f"実測できた{len(included_results)}AI・合計{total_conducted}問中 "
        f"{total_mentioned}問で言及あり")
    competitor_rows = [
        "<tr class='self-row'>"
        f"<td>{inst}（自院）</td>"
        f"<td>{region}</td>"
        f"<td>{esc(self_note)}</td>"
        "</tr>"
    ]
    for c in client["競合"]:
        note = esc(c.get("AIでの言及状況", "今回の比較質問の回答からは特筆すべき言及は確認されませんでした"))
        competitor_rows.append(
            "<tr>"
            f"<td>{esc(c['院名'])}</td>"
            f"<td>{esc(c['所在地'])}</td>"
            f"<td>{note}</td>"
            "</tr>"
        )
    competitor_table_html = "\n".join(competitor_rows)

    # --- 改善ポイント3つ ---
    improvement_html = "\n".join(
        f"<li>☐ {esc(item)}</li>" for item in client["改善ポイント"]
    )

    # --- 誤情報一覧 ---
    if misinfo_items:
        misinfo_lines = "\n".join(
            f"<li><span class='tag'>要確認</span>{esc(item['ai'])} 質問No.{esc(item['question_no'])}"
            f"（{esc(item['category'])}）の回答に、ヒアリング内容と異なる情報が含まれていました。</li>"
            for item in misinfo_items
        )
    else:
        misinfo_lines = "<li>今回の実測範囲では、誤情報は確認されませんでした。</li>"

    template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>AI検索露出 無料ミニ診断レポート｜{inst}様</title>
<style>
  :root{{
    --bg:#f7f8fb; --card:#ffffff; --ink:#1f2430; --sub:#5b6270;
    --accent:#2f6bff; --accent-dark:#1d4fd8; --warn:#c0392b; --warn-bg:#fdecea;
    --ok:#1f8a4c; --ok-bg:#e8f7ee; --line:#e3e6ee;
  }}
  *{{box-sizing:border-box;}}
  body{{
    font-family:"Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
    background:var(--bg); color:var(--ink); margin:0; padding:0 0 60px;
    line-height:1.75;
  }}
  .wrap{{max-width:900px; margin:0 auto; padding:0 20px;}}
  .test-banner{{
    background:var(--warn-bg); color:var(--warn); border:2px solid var(--warn);
    text-align:center; font-weight:bold; padding:14px; font-size:15px;
  }}
  header.hero{{
    background:linear-gradient(135deg, var(--accent) 0%, var(--accent-dark) 100%);
    color:#fff; padding:40px 20px 32px; text-align:center;
  }}
  header.hero h1{{font-size:24px; margin:0 0 8px;}}
  header.hero p{{margin:4px 0; opacity:.95; font-size:14px;}}
  .badge-free{{
    display:inline-block; background:#fff; color:var(--accent-dark); font-weight:bold;
    font-size:12px; padding:4px 12px; border-radius:999px; margin-top:10px;
  }}
  section{{margin:36px 0;}}
  .card{{
    background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:24px 28px; box-shadow:0 2px 8px rgba(20,30,60,.04);
  }}
  h2{{font-size:19px; border-left:5px solid var(--accent); padding-left:12px; margin:0 0 16px;}}
  h3{{font-size:16px; color:var(--accent-dark); margin:20px 0 10px;}}
  table{{width:100%; border-collapse:collapse; font-size:13.5px; margin:12px 0;}}
  th,td{{border:1px solid var(--line); padding:9px 10px; text-align:left; vertical-align:top;}}
  th{{background:#eef2ff; color:var(--ink); font-weight:bold;}}
  tr.self-row td{{background:#fff7e0; font-weight:bold;}}
  .score-total{{
    text-align:center; padding:20px; background:var(--ok-bg); border-radius:12px; margin:16px 0;
  }}
  .score-total .num{{font-size:44px; font-weight:bold; color:var(--warn);}}
  .score-total .label{{font-size:14px; color:var(--sub);}}
  ul.checklist li{{margin:6px 0;}}
  .tag{{
    display:inline-block; font-size:11px; padding:2px 8px; border-radius:6px;
    background:#eef2ff; color:var(--accent-dark); margin-right:6px;
  }}
  .disclaimer{{
    background:var(--warn-bg); border:1px solid var(--warn); border-radius:12px;
    padding:20px 24px; font-size:13.5px; color:#5a2a24;
  }}
  .disclaimer h2{{border-left-color:var(--warn); color:var(--warn);}}
  .upsell{{
    background:#eef2ff; border:1px solid var(--line); border-radius:12px;
    padding:20px 24px; font-size:13.5px;
  }}
  footer{{
    text-align:center; font-size:12px; color:var(--sub); margin-top:40px;
  }}
  .sub-note{{font-size:12.5px; color:var(--sub);}}
</style>
</head>
<body>

{test_banner}

<header class="hero">
  <h1>AI検索露出 無料ミニ診断レポート</h1>
  <p>対象: {inst}様／ 所在地: {region}</p>
  <p>診断実施日: {exec_date} ／ 質問数: {FREE_SCOPE_QUESTIONS}問（おすすめ・比較・料金・口コミ評判・近くの、各2問）／ 対象AI: ChatGPT・Gemini・Perplexity・Google AI Overviews</p>
  <span class="badge-free">無料ミニ診断</span>
</header>

<div class="wrap">

  <section>
    <div class="card">
      <h2>1. 診断サマリー</h2>
      <p>{summary_text}</p>
      <div class="score-total">
        {score_html}
      </div>
      <p class="sub-note">※本スコアは診断実施時点のAI回答に基づく参考値です。AI検索サービスの回答は日々変動するため、将来の表示・掲載順位を保証するものではありません。</p>
      {excluded_note}
    </div>
  </section>

  <section>
    <div class="card">
      <h2>2. AI検索露出スコア表（プラットフォーム別）</h2>
      <table>
        <thead>
          <tr><th>AI検索サービス</th><th>言及回数（実施問数中）</th><th>引用の状況</th><th>推薦順位の目安</th><th>プラットフォーム別スコア</th></tr>
        </thead>
        <tbody>
          {ai_table_html}
        </tbody>
      </table>
      <p class="sub-note">※「言及回数」は実施した質問のうち、AIの回答文中に院名（または一意に特定できる表記）が登場した回数です。実測不可のAIは分母・分子から除外し、総合スコアも実測できたAIのみで算出しています。</p>
    </div>
  </section>

  <section>
    <div class="card">
      <h2>3. 競合比較表（自院＋競合{len(client['競合'])}院）</h2>
      <table>
        <thead>
          <tr><th>院名</th><th>所在地</th><th>AI回答での言及・紹介状況</th></tr>
        </thead>
        <tbody>
          {competitor_table_html}
        </tbody>
      </table>
      <p class="sub-note">※無料ミニ診断では、ヒアリングでお伺いした競合2〜3院との簡易比較にとどめています（詳細な多項目比較は有料診断のスコープです）。</p>
    </div>
  </section>

  <section>
    <div class="card">
      <h2>4. 誤情報の確認結果</h2>
      <ul class="checklist">
        {misinfo_lines}
      </ul>
    </div>
  </section>

  <section>
    <div class="card">
      <h2>5. 改善ポイント（3つ）</h2>
      <ul class="checklist">
        {improvement_html}
      </ul>
      <p class="sub-note">※無料ミニ診断では、特に優先度が高いと考えられる改善ポイントを3つに絞ってご案内しています。</p>
    </div>
  </section>

  <section>
    <div class="upsell">
      <h3>さらに詳しく知りたい場合</h3>
      <p>本診断は無料ミニ診断（{FREE_SCOPE_QUESTIONS}問・競合{len(client['競合'])}院・改善ポイント3つ）です。
      より多くの質問セット・競合比較・改善提案項目で詳細に診断する<strong>有料ライト診断（3万円〜）</strong>もご用意しております。
      ご関心がございましたら、下記連絡先までお気軽にお問い合わせください。</p>
    </div>
  </section>

  <section>
    <div class="disclaimer">
      <h2>免責事項</h2>
      <ul>
        <li>本レポートは、診断実施時点でのAI検索サービスの回答内容の記録・分析です。AI検索サービスの回答は日々変動するため、<strong>特定の検索結果への表示・引用・推薦順位・スコアの向上を保証するものではありません。</strong></li>
        <li>本サービスでは、偽の口コミの作成・投稿、実態と異なる誇大な実績表示、その他景品表示法上の優良誤認・有利誤認につながる表現は一切行いません。改善提案は、公式情報・実績・レビュー・第三者情報を正しく整備する範囲にとどめます。</li>
        <li>施術の効果・効能について、断定的な表現（「必ず治る」「即効性がある」等）は本レポート・改善提案のいずれにおいても使用しません。</li>
      </ul>
    </div>
  </section>

  <footer>
    <p>本レポートに関するお問い合わせ: {CONTACT_EMAIL}（{SIGNATURE}）</p>
    <p>&copy; 2026 YNFactory</p>
  </footer>

</div>
</body>
</html>
"""
    return template


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="無料ミニ診断のスコアシートCSV・院情報JSONから顧客名入りHTMLレポートを生成する。")
    parser.add_argument("--scoresheet", required=True, type=Path, help="記入済みスコアシートCSVのパス")
    parser.add_argument("--client", required=True, type=Path, help="院情報JSONのパス")
    parser.add_argument("--out", required=True, type=Path, help="出力HTMLのパス")
    parser.add_argument("--test", action="store_true",
                         help="架空データによるテスト生成であることを示すバナーを表示する")
    args = parser.parse_args(argv)

    try:
        if not args.scoresheet.exists():
            raise ScoreDataError(f"スコアシートが見つかりません: {args.scoresheet}")
        if not args.client.exists():
            raise ScoreDataError(f"院情報JSONが見つかりません: {args.client}")

        ai_results = load_scoresheet(args.scoresheet)
        client = load_client_info(args.client)
        overall_score, excluded_ais = compute_overall_score(ai_results)
        misinfo_items = collect_misinfo_list(ai_results)

        html_text = render_html(client, ai_results, overall_score, excluded_ais,
                                 misinfo_items, test_mode=args.test)

        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(html_text, encoding="utf-8")

    except ScoreDataError as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[エラー] ファイルの読み込みに失敗しました: {e}", file=sys.stderr)
        return 1

    # --- 実行結果サマリーを標準出力に表示（200行制限を意識し簡潔に） ---
    print(f"レポートを生成しました: {args.out}")
    print(f"院名: {client['院名']} / 実施日: {client['実施日']}")
    if overall_score is not None:
        print(f"総合スコア: {overall_score} / 100")
    else:
        print("総合スコア: 算出不可（全AI実測不可）")
    for ai_name in AI_ORDER:
        result = ai_results[ai_name]
        if result.excluded:
            print(f"  {ai_name}: 実測不可")
        else:
            score = result.ai_score
            print(f"  {ai_name}: {round_half_up(score)} / 100"
                  f"（言及 {result.n_mentioned}/{result.n_conducted}）")
    if excluded_ais:
        print(f"実測不可AI: {', '.join(excluded_ais)}")
    print(f"誤情報検出件数: {len(misinfo_items)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
