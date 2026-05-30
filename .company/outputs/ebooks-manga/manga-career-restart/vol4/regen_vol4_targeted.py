"""
vol4 プレビューチェック（2026-04-14）で発見した不具合ページを一括再生成
- ANTI_META: ［四角枠］［ミサキ］［ナレーション］等の指示記号描画禁止
- ANTI_DUP: セリフ重複禁止
- JP_ONLY: 画像内テキストは必ず日本語
- NO_STEP_UI: 「STEP 1/2/3」UIラベル描画禁止（vol4特有の新バグ）
- NO_SHOES_INDOOR: 室内では靴を脱ぐ
- YUKARI_DEF: ママ友ゆかりの外見統一
- 各ページ固有ENHANCE辞書
"""
import os
import sys
import io
import csv
import json
import shutil
import time
from datetime import datetime
from PIL import Image as PILImage

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google import genai
from google.genai import types

API_KEY = os.environ.get("GOOGLE_AI_STUDIO_API_KEY", "")  # 旧: ハードコード→環境変数化(2026-05-30)
BASE = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart"
CSV_PATH = os.path.join(BASE, "vol4", "panels", "comicle_output.csv")
PAGES_DIR = os.path.join(BASE, "vol4", "pages")
BACKUP_DIR = os.path.join(BASE, "vol4", "pages_backup_20260414")
CHAR_DIR = os.path.join(BASE, "manuscript", "characters")
MODEL = "gemini-3.1-flash-image-preview"

os.makedirs(BACKUP_DIR, exist_ok=True)

# ========== 共通プレフィックス ==========
ANTI_META = """◆【最重要ルール・絶対厳守】以下のメタ指示ワードを画像内のテキストとして絶対に描画禁止:
- 「ナレーション」「ナレーション:」「ナレーション：」「【ナレーション】」「［ナレーション］」
- 「セリフ」「セリフ:」「オノマトペ」
- 「四角枠」「［四角枠］」「【四角枠】」「［角枠］」
- 「吹き出し」「吹き出しに」
- 「1コマ目」「2コマ目」「3コマ目」「上段」「中段」「下段」「上・大」「上・小」「下・大」「下・小」「左」「右」
- 「［ミサキ］」「［ケンタ］」「［ゆかり］」「［タクヤ］」「［山田課長］」「［ひなた］」等の［話者名］マーカー
- 「[ASP社名]」「[ASP]」等の角括弧付きプレースホルダ
- 【】［］で囲まれた全ての指示テキスト
これらは画像の構成指示であり、漫画の画像内には絶対に描画しない。
画像に描画してよいテキストは以下のみ:
- キャラクターのセリフ本文（吹き出し内部）
- ナレーション本文（枠内部、「ナレーション」ラベルは付けない）
- オノマトペの文字（擬音のみ）
"""

ANTI_DUP = """◆【セリフ・ナレーション重複禁止・最優先厳守】
- ナレーション・セリフは指定した文字列を指定箇所に1度だけ描画する
- 同じ文・同じフレーズを複数の枠に分割・重複して描かない
- 似たフレーズの言い換えや追加を勝手にしない
- セリフは必ず吹き出しの内側に収まるよう文字サイズを調整する
- CSV原文に存在しないセリフを勝手に追加しない（例:「嘘はいつか必ずバレます」等の余計な語を足さない）
"""

JP_ONLY = """◆【言語ルール・絶対厳守】画像内の全テキストは必ず日本語（ひらがな・カタカナ・漢字）で描画してください。英語・ローマ字は使用禁止。固有名詞・広告文・UI表示もすべて日本語。
"""

NO_STEP_UI = """◆【STEP UIラベル描画禁止・絶対厳守】
画像内に「STEP 1」「STEP 2」「STEP 3」「Step1」「Step2」「Step3」等の英字UIラベルや矢印インフォグラフィックを絶対に描画しない。
CSVの演出欄に「ステップ図解」の語があっても、それをUIラベル化して描画しない。
漫画のコマ内は通常のシーン描写のみ（キャラ・背景・吹き出し・ナレーション枠のみ）で構成する。
「スキル習得／ブログ活用」等の小カプセルアイコンも描画しない。
"""

NO_SHOES_INDOOR = """◆【日本の生活様式・室内では靴を脱ぐ・絶対厳守】
このシーンは室内（自宅のリビング/ダイニング/キッチン/寝室/廊下）です。ミサキは白いスニーカーを履いていません。
ミサキの足元は「素足（裸足）」または「白い靴下」のいずれかで描画してください。
CSV服装欄に「白いスニーカー」と記載されていても、このシーンでは無視してください。
"""

MISAKI_BORDER = """◆【ミサキ服装補強】ミサキのトップスは「ボーダー柄（白と紺の横縞）」で明確に描画。白地に青1本線だけの無地風にしないこと。
"""

YUKARI_DEF = """◆【ママ友・ゆかりさんキャラクター定義・統一・絶対厳守】
- ゆかり: 30代前半の女性、髪はロングストレートの明るいブラウン（肩より下・背中まで）、前髪は自然に流す、マスタード色（黄色っぽい）のカーディガンに白いインナー、穏やかな微笑み
- ページをまたいで登場するゆかりは常に全く同じ外見・同じ髪型（ロングストレートブラウン）・同じ服装（マスタードカーディガン）で描画
"""

TAKUYA_NOGLASSES = """◆【タクヤ外見統一・絶対厳守】タクヤは添付のタクヤ.pngと100%同一の外見。眼鏡は**かけていません**。黒髪ミディアム。白い無地シャツにベージュのチノパン。前後のページと完全に同じ外見で描画。
"""

# ========== 各ページの個別修正 ==========
ENHANCE = {
    # ---- 第9話 ----
    4: NO_SHOES_INDOOR + NO_STEP_UI + """◆【このページの追加指示】
- タイトルページ。ダイニングテーブルでスマホを手に目を見開くミサキ。朝の柔らかい光。
- ミサキは室内なので白スニーカーを履かない（素足または靴下）。
- 画面内の通知文「お振込がありました」は日本語のみで描画。
""",
    5: NO_STEP_UI + """◆【このページの追加指示】
- 3コマ目タクヤのセリフは「発信する力はもう身についています。次は、それをお金に変えるステップです」を完全に描画（途中で切らない）。
""",
    6: NO_STEP_UI,
    7: NO_STEP_UI + MISAKI_BORDER + """◆【このページの追加指示】
- 2コマ目タクヤのセリフはCSV原文のまま「大事なのは、本当にいいと思っているものだけを紹介すること。嘘は必ずバレます」。「いつか」という余計な語を絶対に追加しない。
""",
    9: NO_STEP_UI + """◆【このページの追加指示】
- 2コマ目は「ミサキが腕を組んで考え、頭の周りに電動鼻吸い器・ベビーモニター・抱っこ紐・冷凍離乳食のイメージが浮かぶ」構図のみ。時計・スマホ・グラフ等の余計なUI装飾は描画しない。
""",
    10: NO_SHOES_INDOOR,
    11: """◆【このページの追加指示】
- 1コマ目ナレーション本文は「Claudeと一緒に、アフィリエイトの仕組みを構築した」を完全に描画（「アフィリエイトの」を欠落させない）。
- 3コマ目の審査通過通知は「[ASP]」等の角括弧プレースホルダを使わず、「A8ネット」「バリュコマース」等の架空社名（日本語カタカナ）で具体的に描画。角括弧付きプレースホルダは絶対に残さない。
""",
    12: NO_SHOES_INDOOR + """◆【このページの追加指示】
- 2コマ目のオノマトペは「カタカタ」のみ（CSV指定）。「Hnm」等の意味不明な英字は絶対に混入させない。
""",
    13: NO_STEP_UI + """◆【このページの追加指示】
- ナレーション枠には本文「リアルだった。嘘がなかった」のみを描画。
- 「［四角枠］」というラベル文字は絶対に描画しない。
""",
    14: NO_SHOES_INDOOR + NO_STEP_UI,
    15: """◆【このページの追加指示】
- コマ配置をCSV通りに厳守:
  - 1コマ目（上段右）: ミサキのInstagram画面
  - 2コマ目（上段左）: タクヤの回想コマ（吹き出し）
  - 3コマ目（下段）: コメント欄
- 日本漫画は右→左読みなので、上段は右コマが先・左コマが後。
""",
    16: """◆【このページの追加指示】
- ひなたの服装は「ピンクのTシャツに白いズボン」を厳守。黄色・ベージュ・白系では絶対に描画しない。
- 前後ページ（page_013等）のひなたと同じピンクTシャツで統一。
""",
    17: """◆【このページの追加指示】
- スマホ銀行アプリ画面の「振込人名:」欄には、角括弧付きプレースホルダ「[ASP社名]」を絶対に残さない。
- 代わりに具体的な架空社名（日本語カタカナ、例「A8ネット」「バリュコマース」「アフィリエイト太郎」など）を描画。
- 「振込額: 1,280円」はそのまま日本語で描画。
""",
    18: """◆【このページの追加指示】
- ナレーション枠には本文のみを描画。「［ナレーション］」「［四角枠］」等のラベル文字は絶対に描画しない。
- 吹き出しには話者名マーカー（［ミサキ］［ひなた］等）を絶対に描画しない。
""",
    20: """◆【このページの追加指示】
- 1コマ目の過去シルエット3人（高校生・大学生・会社員時代のミサキ）の下にキャプション文字「高校生みさき」「大学生みさき」「会社員みさき」等を絶対に描画しない。
- CSVで「セリフ なし／ナレーション なし」指定のコマには文字を一切入れない。
""",
    21: NO_SHOES_INDOOR + """◆【このページの追加指示】
- 屋内ダイニングのシーン。椅子から伸びるミサキの足元に白いスニーカーを描かない。素足または白い靴下のみ。
""",
    23: """◆【このページの追加指示】
- ナレーション枠には本文「返信はすぐに来た」のみを描画。先頭の「[」や「［四角枠］」は絶対に描画しない。
- 3コマ目のタクヤはCSV服装指定どおり「白い無地のシャツにベージュのチノパン」。グレー系Vネックにしない。
- タクヤの顔・髪型・眼鏡の有無はタクヤ.png参照どおりで、page_024・025と完全に統一。
""",
    25: TAKUYA_NOGLASSES + """◆【このページの追加指示】
- ナレーション枠には本文「スタートライン。ここからが本番だ。」のみを描画。「［四角枠］」ラベルは絶対に描画しない。
- タクヤはpage_023・024と同じく眼鏡なし。連続シーン内で眼鏡有無を変化させない。
""",
    26: NO_STEP_UI + """◆【このページの追加指示】
- 1コマ目上部に「［ひなたが昼寝から起きた］」等の角括弧付き状況指示を絶対に描画しない。
- 2コマ目右下に「STEP 1／STEP 2／STEP 3」UIラベルを絶対に描画しない。
""",
    27: NO_STEP_UI + """◆【このページの追加指示・セリフ原文厳守】
- 1コマ目ミサキのセリフは「まだ全然ちょっとだけどね。ちょーっとだけ、稼いだんだよ」を正確に描画。文の分割・重複・語の欠落を絶対にしない。
- 3コマ目ミサキのセリフは「もっと頑張るからね。ひなたに、胸を張れるママになるからね」を正確に描画。語順を崩さない。
""",
    28: NO_SHOES_INDOOR + """◆【このページの追加指示】
- 屋内リビングでミサキが膝立ちでひなたを抱きしめるシーン。ミサキは白スニーカーを履かない。素足または白い靴下のみ。
""",
    30: NO_STEP_UI + """◆【このページの追加指示】
- 2コマ目のミサキはCSV服装指定どおり「薄いピンクのパジャマ」で描画。ボーダーカットソー＋デニムでは描画しない。
""",
    31: """◆【このページの追加指示】
- 3コマ目のナレーション枠には本文「ダイニングテーブルが、ミサキの新しいオフィスになっていた」のみを描画。「［四角枠］」ラベルは絶対に描画しない。
""",
    32: """◆【このページの追加指示・セリフ原文厳守】
- 1コマ目ミサキのセリフは「ケンタ、見て。初めて振り込まれたの」を正確に描画。「初めての振り込まれたの」等の「の」追加・文法崩れを絶対にしない。
""",
    33: NO_STEP_UI,
    34: """◆【このページの追加指示】
- 画像内には「第9話『初めての振込通知』おわり」の文言を1箇所だけ描画。同じ文言を2箇所以上に重複描画しない。
- 「［四角枠］」ラベルは絶対に描画しない。
""",

    # ---- 第10話・コラム ----
    37: NO_SHOES_INDOOR + """◆【このページの追加指示】
- 夜のリビング（室内）でミサキが窓際に立つタイトルページ。ミサキは白スニーカーを履かない（素足または靴下・ルームシューズ）。
- 大見出し「第10話 私のキャリアは、私が決める」を配置。
""",
    38: """◆【このページの追加指示・ナレーション原文厳守】
- 1コマ目のナレーションは「初めての振込から、数ヶ月が経った。ひなたは2歳になっていた」を正確に描画。
- 「ひと月あまり」等の改変を絶対にしない。「数ヶ月」の文字を含めること。
""",
    40: """◆【このページの追加指示・回想シーン】
- 2コマ目は退職日の回想シーンです。**セピア調**（茶色がかったモノトーン）で描画してください。通常カラーで描画しない。
- 2コマ目のミサキの服装は「薄いピンクのパジャマ」ではなく、**退職日のオフィスカジュアル**（白ブラウス＋ダークなスカートまたはパンツ、ローヒール、仕事用バッグ）で描画。
- CSV服装欄の「薄いピンクのパジャマ」は1コマ目（現在時制）のみの指定です。2コマ目の回想では無視してください。
""",
    45: YUKARI_DEF + """◆【このページの追加指示】
- ゆかりさんはpage_043・044と完全に同じ外見で描画: ロングストレートの**明るいブラウン髪（茶髪）**、マスタード色カーディガン、同じ顔立ち。
- 45ページで黒髪に変化させない。茶髪で統一。
""",
    46: """◆【このページの追加指示】
- ナレーション枠には本文「『事務しかできない』ではなく『事務ができるから、できた』」のみを描画。
- 枠上部の「［四角枠］」ラベルは絶対に描画しない。
""",
    48: TAKUYA_NOGLASSES + """◆【このページの追加指示】
- タクヤは**眼鏡なし**で描画（タクヤ.png参照どおり）。
- page_049のタクヤと外見・髪型・眼鏡有無を完全に統一。
""",
    49: TAKUYA_NOGLASSES + """◆【このページの追加指示】
- タクヤは**眼鏡なし**で描画（タクヤ.png参照どおり）。
- page_048のタクヤと外見・髪型・眼鏡有無を完全に統一。連続面談シーン内で外見を変化させない。
""",
    51: """◆【このページの追加指示・セリフ原文厳守】
- 3コマ目ミサキのセリフは「横にいてくれたから、変われたんですよ」を正確に描画。
- 文末の「よ」まで確実に描画し、「変われたんです」で切らない。
""",
    58: """◆【このページの追加指示】
- 2コマ目のナレーション枠には本文「小さな体が布団からはみ出している。いつものことだ。この子のために退職した」のみを描画。
- 先頭の「[」や末尾の「]」、角括弧付きの文字列を絶対に描画しない。
- ひなたの服装はピンクのTシャツ＋白いズボンで明確に描き分ける（ズボンがピンク系にならないように）。
""",
}

# ========== 対象ページ ==========
TARGET_PAGES = sorted(ENHANCE.keys())
print(f"Target pages ({len(TARGET_PAGES)}): {TARGET_PAGES}")

# ========== キャラクター参照画像 ==========
char_files = {
    "ミサキ": "ミサキ.png",
    "ケンタ": "ケンタ.png",
    "山田課長": "山田課長.png",
    "ひなた_赤ちゃん期": "ひなた_赤ちゃん期.png",
    "ひなた_2歳期": "ひなた_2歳期.png",
    "タクヤ": "タクヤ.png",
}
char_images = {}
for name, filename in char_files.items():
    path = os.path.join(CHAR_DIR, filename)
    if os.path.exists(path):
        char_images[name] = path

def detect_characters(prompt):
    detected = []
    if "ミサキ" in prompt and "ミサキ" in char_images:
        detected.append(char_images["ミサキ"])
    if "ケンタ" in prompt and "ケンタ" in char_images:
        detected.append(char_images["ケンタ"])
    if "山田" in prompt and "山田課長" in char_images:
        detected.append(char_images["山田課長"])
    if "ひなた" in prompt:
        if "赤ちゃん" in prompt or "乳" in prompt:
            if "ひなた_赤ちゃん期" in char_images:
                detected.append(char_images["ひなた_赤ちゃん期"])
        else:
            if "ひなた_2歳期" in char_images:
                detected.append(char_images["ひなた_2歳期"])
    if "タクヤ" in prompt and "タクヤ" in char_images:
        detected.append(char_images["タクヤ"])
    return detected

# ========== CSV読み込み ==========
prompts = {}
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if not row or not row[0].isdigit():
            continue
        page_num = int(row[0])
        if page_num in TARGET_PAGES:
            prompts[page_num] = row[2]

print(f"Loaded prompts for pages: {sorted(prompts.keys())}")

# ========== API呼び出し ==========
client = genai.Client(api_key=API_KEY)
log = []

for page_num in TARGET_PAGES:
    original = prompts.get(page_num)
    if not original:
        print(f"P{page_num:03d}: SKIP (no CSV prompt)")
        continue

    enhancement = ENHANCE[page_num]
    full_prompt = ANTI_META + ANTI_DUP + JP_ONLY + enhancement + "\n---\n" + original

    src_path = os.path.join(PAGES_DIR, f"page_{page_num:03d}.jpg")
    backup_path = os.path.join(BACKUP_DIR, f"page_{page_num:03d}.jpg")
    output_path = src_path

    if os.path.exists(src_path) and not os.path.exists(backup_path):
        shutil.copy(src_path, backup_path)

    char_paths = detect_characters(original)
    print(f"P{page_num:03d}: chars={len(char_paths)}", end=" ", flush=True)

    success = False
    for attempt in range(3):
        try:
            contents = []
            for cp in char_paths:
                img = PILImage.open(cp)
                contents.append(img)
            contents.append(full_prompt)

            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="9:16"),
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=config,
            )

            saved = False
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data is not None:
                        image = PILImage.open(io.BytesIO(part.inline_data.data))
                        if image.mode in ('RGBA', 'P'):
                            image = image.convert('RGB')
                        image.save(output_path, 'JPEG', quality=92)
                        saved = True
                        break
            if saved:
                print(f"OK (try{attempt+1})")
                log.append({"page": page_num, "status": "ok", "attempt": attempt+1})
                success = True
                break
            else:
                print(f"no_image(try{attempt+1})", end=" ")
        except Exception as e:
            print(f"err(try{attempt+1}):{str(e)[:50]}", end=" ")
            time.sleep(2)

    if not success:
        print("FAILED")
        log.append({"page": page_num, "status": "failed"})

log_path = os.path.join(BASE, "vol4", f"regen_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
with open(log_path, 'w', encoding='utf-8') as f:
    json.dump(log, f, ensure_ascii=False, indent=2)

ok_count = sum(1 for x in log if x["status"] == "ok")
fail_count = sum(1 for x in log if x["status"] == "failed")
print(f"\n完了: OK={ok_count}, FAILED={fail_count}")
print(f"ログ: {log_path}")
print(f"バックアップ: {BACKUP_DIR}")
