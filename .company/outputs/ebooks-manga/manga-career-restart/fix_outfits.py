import re

csv_path = r"G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\panels\comicle_output.csv"

with open(csv_path, "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")

# Outfit variations
MISAKI_OFFICE = "ミサキ: 白いブラウスにグレーのタイトスカート、黒いパンプス（オフィス服装）"
MISAKI_DAY = "ミサキ: ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー"
MISAKI_NIGHT = "ミサキ: ピンクのスウェットトレーナーにグレーのルームパンツ、裸足（部屋着）"
MISAKI_OUT = "ミサキ: ベージュのカーディガンに白Tシャツ、デニムパンツ、白いスニーカー（外出着）"
MISAKI_SUIT = "ミサキ: 紺のジャケットに白ブラウス、グレーのタイトスカート、黒いパンプス（最終出社日スーツ）"

KENTA_WORK = "ケンタ: 紺のスーツに白ワイシャツ、ネクタイを緩めた帰宅直後の姿"
KENTA_HOME = "ケンタ: グレーのTシャツにネイビーのスウェットパンツ、黒い靴下"

TAKUYA = "タクヤ: 白い無地のシャツにベージュのチノパン、茶色の革靴"

night_words = ["夜中", "授乳", "夜泣き", "暗い部屋", "スマホの光", "深夜", "寝顔", "午前2時",
               "寝かしつけ", "布団", "ベッド", "天井", "目が覚め", "SNS", "検索", "画面だけ",
               "窓ガラス", "パソコンを開く", "DM"]
office_words = ["上司", "課長", "報告", "オフィス", "給湯室", "同僚", "出社"]
suit_words = ["最終出社", "スーツを着", "入館証", "段ボール", "デスクを片付", "オフィスビル", "見上げ"]
out_words = ["ATM", "通帳を記帳", "銀行", "支援センター", "ママ友", "ベビーカー", "帰り道", "ゆかり"]
kenta_work_words = ["帰宅", "帰って", "おかえり", "ただいま", "22時", "23時"]


def has_any(text, words):
    return any(w in text for w in words)


def get_misaki_outfit(page_num, story):
    # プロローグ P1-11
    if page_num <= 11:
        if has_any(story, office_words):
            return MISAKI_OFFICE
        if has_any(story, night_words):
            return MISAKI_NIGHT
        return MISAKI_DAY

    # 第1章 P12-21
    if page_num <= 21:
        if has_any(story, night_words):
            return MISAKI_NIGHT
        if has_any(story, out_words):
            return MISAKI_OUT
        return MISAKI_DAY

    # 第2章 P22-34
    if page_num <= 34:
        if has_any(story, suit_words):
            return MISAKI_SUIT
        if has_any(story, night_words):
            return MISAKI_NIGHT
        if has_any(story, ["退職届", "便箋", "封筒"]):
            return MISAKI_DAY
        return MISAKI_DAY

    # 第3章 P35-45
    if page_num <= 45:
        if has_any(story, out_words):
            return MISAKI_OUT
        if has_any(story, night_words):
            return MISAKI_NIGHT
        return MISAKI_DAY

    # 第4章 P46-59
    if page_num <= 59:
        if has_any(story, night_words + ["ウェビナー", "Zoom", "広告", "ブログ", "申し込み"]):
            return MISAKI_NIGHT
        return MISAKI_HOME_DAY if False else MISAKI_DAY

    # 第5章 P60-70
    if page_num <= 70:
        return MISAKI_DAY

    # 第6章 P71-80
    if page_num <= 80:
        if has_any(story, night_words):
            return MISAKI_NIGHT
        return MISAKI_DAY

    # 第7章 P81-93
    if page_num <= 93:
        if has_any(story, night_words):
            return MISAKI_NIGHT
        return MISAKI_DAY

    # 第8章 P94-106
    if page_num <= 106:
        if has_any(story, night_words):
            return MISAKI_NIGHT
        return MISAKI_DAY

    # エピローグ P107-120
    if has_any(story, out_words):
        return MISAKI_OUT
    if has_any(story, night_words + ["窓", "パソコン", "Claude"]):
        return MISAKI_NIGHT
    return MISAKI_DAY


def get_kenta_outfit(story):
    if has_any(story, kenta_work_words):
        return KENTA_WORK
    return KENTA_HOME


# Process
current_page = 0
page_story_buffer = []
modified = 0
new_lines = []

# First pass: collect story text per page
page_stories = {}
cur_page = 0
cur_text = []
for line in lines:
    m = re.match(r'^"(\d+)","', line)
    if m:
        if cur_page > 0:
            page_stories[cur_page] = "\n".join(cur_text)
        cur_page = int(m.group(1))
        cur_text = [line]
    else:
        cur_text.append(line)
if cur_page > 0:
    page_stories[cur_page] = "\n".join(cur_text)

print(f"Parsed {len(page_stories)} pages")

# Second pass: modify outfit lines
cur_page = 0
for line in lines:
    m = re.match(r'^"(\d+)","', line)
    if m:
        cur_page = int(m.group(1))

    if line.startswith("\u25c6\u3010\u88dc\u8db3\u60c5\u5831\u3011\u670d\u88c5:"):
        story = page_stories.get(cur_page, "")
        parts = []

        if "\u30df\u30b5\u30ad" in story:
            parts.append(get_misaki_outfit(cur_page, story))
        if "\u30bf\u30af\u30e4" in story:
            parts.append(TAKUYA)
        if "\u30b1\u30f3\u30bf" in story:
            parts.append(get_kenta_outfit(story))

        if parts:
            new_line = "\u25c6\u3010\u88dc\u8db3\u60c5\u5831\u3011\u670d\u88c5: " + " / ".join(parts)
            if new_line != line:
                modified += 1
                print(f"  P{cur_page}: {new_line[:80]}...")
            new_lines.append(new_line)
            continue

    new_lines.append(line)

with open(csv_path, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

print(f"\nDone. Modified {modified} pages")
