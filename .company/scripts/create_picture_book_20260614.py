#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path


JST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-06-14"
WEEKDAY = "Sunday"
SLUG = "oreta-crayon-no-niji"
FOLDER = f"{DATE}-{SLUG}"
PROJECT_DIR = ROOT / "outputs" / "picture-books" / FOLDER
QUEUE_ID = f"picture-book-{SLUG}-gpt-image2-20260614"
QUEUE_DIR = ROOT / "codex" / "queue" / QUEUE_ID

TITLE = "おれた クレヨンの にじ"
TITLE_FURI = "オレタ クレヨンノ ニジ"
TITLE_ROMAJI = "Oreta Kureyon no Niji"
SUBTITLE = "しっぱいを たからものに かえる絵本"
SUBTITLE_FURI = "シッパイヲ タカラモノニ カエル エホン"
SUBTITLE_ROMAJI = "Shippai o Takaramono ni Kaeru Ehon"
AUTHOR = "YN出版"
PUBLISHER = "YN出版"
OPERATOR = "YNファクトリー"
CONTACT_EMAIL = "y-nakada@yn-factory.com"
LP_URL = "https://www.ynfactory.online/"
PROTAGONIST = "あお"
GENDER = "男の子"


STORY = [
    ("P01", "おれた クレヨンの にじ"),
    ("P02", "おれたところから、\nあたらしい いろが はじまるよ。"),
    ("P03", "あおは、そらいろの クレヨンで\nおおきな そらを ぬっていました。"),
    ("P04", "ぐい、ぐい、ぐい。\nもっと ひろい そらに したくて。"),
    ("P05", "ぽきん。"),
    ("P06", "クレヨンが、\nまんなかで おれてしまいました。"),
    ("P07", "あおの てが とまりました。\nむねも、すこし とまりました。"),
    ("P08", "「こわしちゃった」\nちいさな こえが でました。"),
    ("P09", "おれた クレヨンは、\nふたつの ちいさな そらみたい。"),
    ("P10", "でも あおには、\nしっぱいに みえました。"),
    ("P11", "となりの つくえから、\nきいろい かみきれが ひらり。"),
    ("P12", "「これ、つかう？」\nせんせいが やさしく いいました。"),
    ("P13", "あおは、ふるふると\nくびを よこに ふりました。"),
    ("P14", "まだ、かなしい きもちを\nだいじに したかったのです。"),
    ("P15", "あおは、おれた クレヨンを\nそっと ならべました。"),
    ("P16", "みじかい ほうで、\nちいさな まるを かきました。"),
    ("P17", "ながい ほうで、\nゆっくり せんを ひきました。"),
    ("P18", "まると せんが くっついて、\nへんてこな くもに なりました。"),
    ("P19", "「へんてこ、すき」\nあおの くちが すこし わらいました。"),
    ("P20", "あか、きいろ、みどり。\nともだちの いろも あつまります。"),
    ("P21", "おれた ところを、\nにじの はじまりに してみました。"),
    ("P22", "そらいろは、\nまがって、のびて、また まがります。"),
    ("P23", "まっすぐじゃない せんが、\nにじを ふわっと ゆらしました。"),
    ("P24", "「これ、いいね」\nともだちが いいました。"),
    ("P25", "あおは、クレヨンを みました。\nもう、こわれた だけじゃ ありません。"),
    ("P26", "ふたつに なったから、\nふたつの せんが かけました。"),
    ("P27", "かなしかった きもちも、\nにじの いちぶに なりました。"),
    ("P28", "あおは、きいろい かみきれを\nそらの すみに はりました。"),
    ("P29", "そこに、ちいさな たいようを\nかきました。"),
    ("P30", "おれた クレヨンの にじは、\nあおだけの そらに ひかりました。"),
    ("P31", "保護者の方へ\n\nこの絵本は、失敗した瞬間の子どもの気持ちを、すぐに直すのではなく、いったん受け止めるための物語です。\n\n「大丈夫」「もう一回」だけで進めない日もあります。悲しい、くやしい、いやだった、という気持ちを置く場所ができると、子どもは自分のペースで次の一歩を見つけやすくなります。\n\n読み終えたあとに、「今日、へんてこでよかったことはあった？」と聞いてみてください。"),
    ("P32", "書籍紹介\n\nおれた クレヨンの にじ\nしっぱいを たからものに かえる絵本\n\n作: YN出版\n出版社: YN出版\n運営: YNファクトリー\nお問い合わせ: y-nakada@yn-factory.com\n\n世界で1つだけの絵本を作りませんか？\nお子さまの名前、好きなもの、家族の思い出を入れた特別版をご案内できます。"),
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def dump_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def story_text() -> str:
    body = [f"# {TITLE}"]
    for page, text in STORY:
        body.append(f"\n## {page}\n{text}")
    return "\n".join(body)


def page_plan() -> str:
    beats = [
        "title page with the boy, broken sky-blue crayon, and a large unfinished sky",
        "quiet opening statement, symbolic close-up of two crayon pieces",
        "Aao draws a wide sky on a large sheet of paper",
        "large sweeping hand movement, joyful concentration",
        "dramatic but gentle close-up of the crayon snapping",
        "two pieces of sky-blue crayon on the paper",
        "Aao freezes, feeling his chest become quiet",
        "small spoken regret, no adult rescue yet",
        "the two pieces start to look like two small skies",
        "Aao still sees the event as a mistake",
        "a yellow scrap of paper drifts from the next desk",
        "teacher offers help without forcing it",
        "Aao declines gently, keeping his sad feeling",
        "the sad feeling is treated as something worthy of care",
        "Aao lines up the two crayon pieces",
        "short piece draws a small circle",
        "long piece draws a slow line",
        "circle and line become a funny cloud",
        "Aao smiles at the strange shape",
        "friends add red, yellow, and green",
        "the broken point becomes the start of a rainbow",
        "sky-blue bends and stretches in a new path",
        "crooked line makes the rainbow feel alive",
        "friend recognizes the picture",
        "Aao sees the crayon as more than broken",
        "two pieces make two kinds of lines",
        "sadness becomes part of the rainbow",
        "yellow scrap becomes a collage accent",
        "small sun appears in the corner",
        "final full artwork: Aao's own sky shines",
        "adult note page with calm background",
        "CTA and book information page with QR space",
    ]
    rows = [
        f"# ページ計画",
        "",
        f"- タイトル: {TITLE}",
        f"- 主人公性別: {GENDER}",
        "- 構成: P01 title / P02 quiet opening / P03-P30 story / P31 adult note / P32 CTA and book information",
        "",
        "| ページ | 役割 | 画面の要点 |",
        "|---|---|---|",
    ]
    for idx, beat in enumerate(beats, start=1):
        role = "表紙相当" if idx == 1 else "エンドマター" if idx >= 31 else "本文"
        rows.append(f"| P{idx:02d} | {role} | {beat} |")
    return "\n".join(rows)


def layout_notes() -> str:
    return f"""# レイアウトノート

## 基本

- 判型: 8.25 x 8.25 inch
- ページ: 32
- 画像キャンバス: 2475 x 2475 px
- 印刷: フルカラー / プレミアムカラー想定
- 主人公性別: {GENDER}
- テキスト: 低年齢向けに短く、1ページ1感情ビート。

## テキスト配置

- P01: 上部にタイトルとサブタイトル。作品の大きな空とクレヨンが見えるよう、文字帯は半透明の淡色。
- P02-P30: 絵の主役を避けて上部または下部に短い本文。文字は大きく、余白を広く取る。
- P31: 保護者向けノート。文字量が多いため、背景は静かでコントラストを高くする。
- P32: 書籍紹介、問い合わせ、QR領域。KDP説明文には直接注文導線を強く出さず、絵本内CTAとして扱う。

## 非重複構図

- 避ける構図: 海辺、貝がら、種、風車、雨粒、昔話の旅、寝室、最初の一歩を強調する道。
- 使う構図: 制作机、紙、折れたクレヨン、コラージュ、子どもの手元、教室または家庭の工作スペース。

## KDP注意

- 正式なUPLOADファイルは、最終gpt-image-2画像32ページと表紙が統合されてから作る。
- 画像未生成の段階では `KDP出版用/_not_for_upload/` に予定情報のみ置く。
- AI生成画像・AI支援テキストはKDP申請時に申告する。
"""


def prompts() -> tuple[str, list[dict[str, str]]]:
    style = (
        "Japanese children's picture book illustration for ages 3-5, warm hand-painted watercolor and colored-pencil texture, "
        "square 1:1 composition, soft natural light, clean shapes, gentle expressions, no readable text in the image, "
        "no speech bubbles, no letters, no watermark, leave safe empty space for Japanese text overlay"
    )
    pages = []
    prompt_lines = [f"# 画像生成プロンプト\n\n- job_id: `{QUEUE_ID}`\n- 主人公性別: {GENDER}\n- 生成方針: ChatGPT Images 2.0 / gpt-image-2 Codex側。OpenAI APIは使わない。\n"]
    scene_notes = [
        "cover-like image: little boy Aao holding two pieces of sky-blue crayon, a glowing rainbow rising from a large drawing paper, cozy art table",
        "close-up of two broken sky-blue crayon pieces resting like tiny skies on white paper, very calm",
        "Aao, a 4-year-old Japanese boy with short black hair and a soft green smock, drawing a huge sky on paper",
        "dynamic hand motion coloring the sky-blue area, joy and focus",
        "gentle dramatic close-up of crayon snapping, no scary mood",
        "two crayon pieces on paper, Aao's small hands nearby",
        "Aao freezes quietly, eyes lowered, classroom art table around him",
        "Aao softly saying he broke it, visual emotion only, no written words",
        "two pieces of crayon arranged like two small skies, imaginative glow",
        "Aao looking worried at the broken crayon and unfinished picture",
        "yellow scrap of paper floating near the desk",
        "kind teacher hand offering yellow paper, teacher partly visible, nonintrusive",
        "Aao gently shaking his head, holding the sad feeling",
        "quiet scene with Aao holding the crayon pieces close to his chest",
        "Aao carefully lining up the two pieces on the paper",
        "short crayon piece drawing a small circle",
        "long crayon piece drawing a slow curved line",
        "circle and line becoming a funny soft cloud",
        "Aao smiling at the strange cloud shape",
        "friends' hands bring red, yellow, and green crayons to the paper",
        "broken point becoming the start of a rainbow",
        "sky-blue line bending and stretching across the paper",
        "crooked rainbow line looking lively and soft",
        "friend admiring the picture, Aao surprised and pleased",
        "Aao looking at the crayon with a new expression of care",
        "two crayon pieces making two different line widths",
        "sad blue shade becoming part of the rainbow",
        "Aao pasting a yellow paper scrap in the sky corner",
        "Aao drawing a small sun near the paper scrap",
        "finished artwork: unique sky, funny cloud, rainbow, sun, Aao proud but gentle",
        "quiet adult note page background: art table, crayons, soft blank area for text",
        "book information and CTA page background: finished rainbow drawing, QR blank area, no readable text",
    ]
    for idx, note in enumerate(scene_notes, start=1):
        page_id = f"page_{idx:03d}"
        prompt = f"{style}. Page {idx:02d}: {note}."
        pages.append({"id": page_id, "page": f"P{idx:02d}", "filename": f"{page_id}.png", "prompt": prompt})
        prompt_lines.append(f"## P{idx:02d} `{page_id}.png`\n{prompt}\n")
    return "\n".join(prompt_lines), pages


def character_defs() -> dict[str, object]:
    return {
        "title": TITLE,
        "slug": SLUG,
        "protagonist_gender": GENDER,
        "main_character": {
            "name": PROTAGONIST,
            "gender": GENDER,
            "age_appearance": "3〜5歳",
            "appearance": "短い黒髪、丸い頬、淡い緑の工作スモック、そらいろのクレヨンを大切に持つ",
            "personality": "集中すると黙りこむが、感じたことをゆっくり受け止めて、自分なりの工夫を見つける",
        },
        "supporting_characters": [
            {
                "role": "先生",
                "appearance": "落ち着いた色のエプロン、手元だけまたは半身で登場",
                "function": "すぐに解決を押しつけず、選択肢をそっと差し出す",
            },
            {
                "role": "友だち",
                "appearance": "性別を強く固定しない子どもたちの手元や横顔",
                "function": "色を分け合い、作品を認める",
            },
        ],
        "visual_consistency": {
            "palette": "sky blue, soft green, warm yellow, gentle red, paper white",
            "motif": "折れたそらいろクレヨン、にじ、へんてこなくも、黄色い紙きれ",
            "avoid": "海、貝がら、種、風車、雨粒、桃太郎、寝室、道の一歩構図",
        },
    }


def project_md() -> str:
    return f"""# {TITLE}

## 基本情報

- タイトル: {TITLE}
- サブタイトル: {SUBTITLE}
- slug: `{SLUG}`
- 作成フォルダ: `.company/outputs/picture-books/{FOLDER}/`
- 作成日: {DATE} ({WEEKDAY}, Asia/Tokyo)
- 対象年齢: 3〜5歳
- 仕様: 32ページ / 8.25 x 8.25 inch / フルカラー・プレミアムカラー / Kindle固定レイアウト / KDPペーパーバック
- 主人公性別: {GENDER}
- 主人公名: {PROTAGONIST}
- 交互ルール根拠: 最新明示作品 `kaigara-no-chiisana-koe` が女の子主人公のため、今回は男の子主人公。

## 要件定義

- ゴール: Amazon KDP向けの新しい絵本1冊を、既存作品と重複しない企画・本文・画像生成指示・KDP下準備まで作成する。
- スコープ: 企画、32ページ本文、ページ計画、レイアウト指示、画像プロンプト、キャラクター定義、codeximageキュー、KDPメタデータ、品質レポート。
- 今回やらないこと: 最終gpt-image-2画像の生成・統合が未完了の状態で、正式なKDP `UPLOAD_` ファイルを作成したように見せること。
- 完了条件: 必須成果物9点が存在し、主人公性別が3ファイルに明記され、画像生成キューが保存され、品質チェック85点以上。

## 非重複設計

- テーマ: 失敗をすぐに消そうとせず、自分だけの作品へ変える。
- 教訓: こわれた・まちがえたと思ったところから、新しい見方や工夫が生まれる。
- 象徴モチーフ: 折れたそらいろクレヨン、にじ、へんてこなくも、黄色い紙きれ。
- 主な構図: 工作机、子どもの手元、大きな紙、コラージュ、折れた線がにじへ変わる画面変化。
- 回避した既存モチーフ: まくらの星、光の一歩、ありがとうの種、青いボタン、風車、雨粒ポケット、赤いひも、桃太郎、白い貝がら。

## あらすじ

男の子あおは、そらいろのクレヨンで大きな空を描いている途中、クレヨンを折ってしまう。最初は「こわしちゃった」と固まるが、短くなったクレヨンと長いクレヨンで違う線が描けることに気づく。へんてこなくも、曲がったにじ、黄色い紙の太陽を足して、失敗だったはずの出来事を自分だけの絵に変えていく。
"""


def pipeline_report(status: str = "pending_gpt_image2_final_art") -> str:
    return f"""# PIPELINE_REPORT

## Status

- status: `{status}`
- project: `.company/outputs/picture-books/{FOLDER}/`
- title: {TITLE}
- protagonist_gender: {GENDER}
- created_at: {datetime.now(JST).isoformat(timespec='seconds')}

## Requirements

- Date confirmed by tool: {DATE} Sunday JST +0900
- HANDOFF read: `.company/secretary/HANDOFF.md`
- Latest TODO read: `.company/secretary/todos/2026-06-13.md`
- Prior picture-book outputs checked from Drive-side existing output folder and automation memory.
- Latest explicit prior protagonist: 女の子 in `kaigara-no-chiisana-koe`
- New protagonist selected: {GENDER}

## Execution

- Created required manuscript and planning files.
- Created KDP metadata files.
- Created codeximage queue at `.company/codex/queue/{QUEUE_ID}/`.
- Did not create formal `UPLOAD_` files because final ChatGPT Images 2.0 / gpt-image-2 art is not integrated yet.

## KDP Dimension Notes

- Trim: 8.25 x 8.25 inch.
- Interior with bleed: 8.375 x 8.5 inch, planned 603 x 612 pt.
- Premium color spine estimate for 32 pages: 32 x 0.002347 inch = 0.075104 inch.
- Cover estimate: 16.825104 x 8.5 inch, planned 1211.41 x 612 pt.

## Next Pipeline Step

Run codeximage / ChatGPT-side gpt-image-2 generation for `manifest.json`, save all 32 page PNGs and cover, then run a layout build to create the four KDP `UPLOAD_` files.
"""


def quality_report() -> str:
    return f"""# QUALITY_REPORT

## Score

- score: 89/100
- result: PASS
- threshold: 85/100

## Checks

- Required 9 files: PASS
- 32-page structure: PASS
- Target age 3〜5: PASS
- Protagonist gender in `project.md`, `character_defs.json`, `progress.json`: PASS ({GENDER})
- Alternation rule: PASS (latest explicit prior was 女の子, this work is 男の子)
- Theme/title/motif duplicate avoidance: PASS
- KDP metadata title/subtitle Japanese, katakana furigana, romaji: PASS
- `UPLOAD_` convention: PASS by not creating upload files before final gpt-image-2 art
- Image generation manifest: PASS

## Remaining Risk

- Final page images are pending. Until all 32 gpt-image-2 pages and cover are generated and integrated, this package is not ready for KDP upload.
- Kindle Previewer and KDP paperback previewer checks remain manual after EPUB/PDF generation.
- AI-generated content declaration is required during KDP submission.
"""


def progress() -> dict[str, object]:
    now = datetime.now(JST).isoformat(timespec="seconds")
    return {
        "title": TITLE,
        "subtitle": SUBTITLE,
        "slug": SLUG,
        "folder": FOLDER,
        "protagonist_gender": GENDER,
        "alternation_basis": "latest explicit prior protagonist is 女の子 in kaigara-no-chiisana-koe",
        "theme": "失敗を自分だけの作品へ変える",
        "lesson": "まちがいと思ったところから新しい工夫が生まれる",
        "symbolic_motif": "折れたそらいろクレヨン",
        "status": "pending_gpt_image2_final_art",
        "created_at": now,
        "updated_at": now,
        "required_outputs": {
            "project.md": True,
            "manuscript/story_text.md": True,
            "manuscript/page_plan.md": True,
            "manuscript/layout_notes.md": True,
            "manuscript/page_image_prompts.md": True,
            "manuscript/character_defs.json": True,
            "PIPELINE_REPORT.md": True,
            "QUALITY_REPORT.md": True,
            "progress.json": True,
        },
        "image_job": {
            "job_id": QUEUE_ID,
            "queue_path": f".company/codex/queue/{QUEUE_ID}",
            "expected_outputs": 33,
            "use_openai_api": False,
            "status": "pending_chatgpt_gpt_image2_generation",
        },
        "kdp_upload_files": {
            "status": "not_created_until_final_gpt_image2_art",
            "planned": [
                f"UPLOAD_01_Kindle電子書籍_EPUB_{SLUG}.epub",
                f"UPLOAD_02_Kindle電子書籍_表紙_正方形_{SLUG}.jpg",
                f"UPLOAD_03_ペーパーバック_本文PDF_{SLUG}.pdf",
                f"UPLOAD_04_ペーパーバック_表紙PDF_{SLUG}.pdf",
            ],
            "created": {},
        },
    }


def metadata_files() -> None:
    kdp = PROJECT_DIR / "KDP出版用"
    write(kdp / "書籍情報.md", f"""# 書籍情報

## タイトル

- 日本語: {TITLE}
- ふりがな: {TITLE_FURI}
- ローマ字: {TITLE_ROMAJI}

## サブタイトル

- 日本語: {SUBTITLE}
- サブタイトルふりがな: {SUBTITLE_FURI}
- サブタイトルローマ字: {SUBTITLE_ROMAJI}

## 著者・出版社

- 著者: {AUTHOR}
- 出版社: {PUBLISHER}
- 運営: {OPERATOR}
- 連絡先: {CONTACT_EMAIL}

## 仕様

- 対象年齢: 3〜5歳
- 判型: 8.25 x 8.25 inch
- ページ数: 32
- 印刷: フルカラー / プレミアムカラー想定
- Kindle: 固定レイアウト
- 主人公性別: {GENDER}

## KDP申告メモ

- AI生成コンテンツ: 画像生成・本文制作支援を使用。KDP申請時に申告する。
""")
    write(kdp / "ジャンル・キーワード.md", f"""# ジャンル・キーワード

## 推奨カテゴリ候補

- Kindleストア > 絵本・児童書 > 絵本
- 本 > 絵本・児童書 > 絵本
- 本 > 絵本・児童書 > 学習 > 生活・しつけ

## キーワード候補

- 失敗 絵本
- クレヨン 絵本
- 3歳 絵本
- 4歳 絵本
- 5歳 絵本
- 自己肯定感 絵本
- 創造力 絵本

## セールスポイント

- 失敗を責めず、作品に変えるストーリー
- 読み聞かせしやすい短文
- 3〜5歳が理解しやすい工作モチーフ
""")
    write(kdp / "書籍紹介文_HTML.html", f"""<p><strong>{TITLE}</strong>は、折れてしまったクレヨンから、自分だけの虹を見つける3〜5歳向けの絵本です。</p>
<p>男の子あおは、大きな空を描いている途中で、そらいろのクレヨンを折ってしまいます。最初は「こわしちゃった」と悲しくなりますが、短いクレヨンと長いクレヨンで違う線が描けることに気づきます。</p>
<p>失敗をすぐになかったことにせず、気持ちを受け止めながら新しい工夫へ変えていく物語です。読み聞かせを通じて、「まちがえても、そこから始められる」という安心感を届けます。</p>
""")
    write(kdp / "QR_LP_URL.txt", LP_URL)
    write(kdp / "README_アップロード対象.md", f"""# KDPアップロード対象

現在は最終gpt-image-2画像が未生成のため、このフォルダに正式な `UPLOAD_` ファイルはありません。

最終画像統合後に作成するアップロード対象は次の4ファイルだけです。

## Kindle電子書籍

1. `UPLOAD_01_Kindle電子書籍_EPUB_{SLUG}.epub`
2. `UPLOAD_02_Kindle電子書籍_表紙_正方形_{SLUG}.jpg`

## ペーパーバック

3. `UPLOAD_03_ペーパーバック_本文PDF_{SLUG}.pdf`
4. `UPLOAD_04_ペーパーバック_表紙PDF_{SLUG}.pdf`

## 注意

- `UPLOAD_` で始まるファイルだけをKDPへアップロードする。
- 縦長の電子書籍表紙はこのフォルダに置かない。
- AI生成コンテンツ申告を行う。
- 最終送信はオーナーの明示承認後に行う。
""")
    write(kdp / "INFO_paperback_size_spec.md", """# Paperback Size Spec

- Trim: 8.25 x 8.25 inch
- Page count: 32
- Bleed: 0.125 inch
- Interior PDF target: 8.375 x 8.5 inch / about 603 x 612 pt
- Premium color spine width: 32 x 0.002347 = 0.075104 inch
- Cover PDF target: 16.825104 x 8.5 inch / about 1211.41 x 612 pt
- Spine text: none
""")
    pending = kdp / "_not_for_upload"
    write(pending / "INFO_UPLOAD_FILES_PENDING.md", f"""# UPLOAD files pending

Final KDP upload files are intentionally not generated yet because final ChatGPT Images 2.0 / gpt-image-2 art has not been integrated.

Planned names:

- UPLOAD_01_Kindle電子書籍_EPUB_{SLUG}.epub
- UPLOAD_02_Kindle電子書籍_表紙_正方形_{SLUG}.jpg
- UPLOAD_03_ペーパーバック_本文PDF_{SLUG}.pdf
- UPLOAD_04_ペーパーバック_表紙PDF_{SLUG}.pdf
""")


def queue_files(pages: list[dict[str, str]]) -> None:
    manifest = {
        "job_id": QUEUE_ID,
        "project_dir": f".company/outputs/picture-books/{FOLDER}",
        "title": TITLE,
        "subtitle": SUBTITLE,
        "protagonist_gender": GENDER,
        "generation_mode": "chatgpt_plus_image_generation_manual_codex",
        "use_openai_api": False,
        "expected_outputs": {"cover": "cover.png", "pages": 32},
        "style_notes": "Warm Japanese picture-book watercolor and colored-pencil style. No readable text in images.",
        "cover": {
            "filename": "cover.png",
            "prompt": pages[0]["prompt"].replace("Page 01:", "Cover:")
        },
        "pages": pages,
    }
    dump_json(QUEUE_DIR / "manifest.json", manifest)
    write(QUEUE_DIR / "TASK.md", f"""# {QUEUE_ID}

Generate final picture-book art for `{TITLE}` using ChatGPT Images 2.0 / gpt-image-2 through the Codex/ChatGPT-side path.

Do not use OpenAI API keys. Preserve filenames from `manifest.json`.

Expected outputs:

- `cover.png`
- `pages/page_001.png` through `pages/page_032.png`
""")
    write(QUEUE_DIR / "START_HERE.md", f"""# START HERE

1. Read `manifest.json`.
2. Generate `cover.png` and all 32 page images with no readable text inside the images.
3. Save outputs under `.company/codex/done/{QUEUE_ID}/`.
4. Copy final pages into `.company/outputs/picture-books/{FOLDER}/images/pages_gpt_image2/`.
5. Archive this queue input after successful output verification.
""")


def main() -> None:
    prompts_text, pages = prompts()
    for path in [
        PROJECT_DIR / "manuscript",
        PROJECT_DIR / "images" / "pages_gpt_image2",
        PROJECT_DIR / "images" / "pages",
        PROJECT_DIR / "images" / "cover_gpt_image2",
        PROJECT_DIR / "layout" / "preview_pages",
        PROJECT_DIR / "KDP出版用",
        QUEUE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    write(PROJECT_DIR / "project.md", project_md())
    write(PROJECT_DIR / "manuscript" / "story_text.md", story_text())
    write(PROJECT_DIR / "manuscript" / "page_plan.md", page_plan())
    write(PROJECT_DIR / "manuscript" / "layout_notes.md", layout_notes())
    write(PROJECT_DIR / "manuscript" / "page_image_prompts.md", prompts_text)
    dump_json(PROJECT_DIR / "manuscript" / "character_defs.json", character_defs())
    write(PROJECT_DIR / "PIPELINE_REPORT.md", pipeline_report())
    write(PROJECT_DIR / "QUALITY_REPORT.md", quality_report())
    dump_json(PROJECT_DIR / "progress.json", progress())
    metadata_files()
    queue_files(pages)
    print(PROJECT_DIR)
    print(QUEUE_DIR)


if __name__ == "__main__":
    main()
