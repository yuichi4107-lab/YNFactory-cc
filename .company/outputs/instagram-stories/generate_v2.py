"""
Instagram Stories 残り13枚生成（v2）
Step 1: DALL-E 3で背景のみ生成
Step 2: Pillowでテキストブロックを重ねる
"""

import os
import time
import requests
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# フォント設定
FONT_MAIN_PATH = "C:/Windows/Fonts/meiryob.ttc"
FONT_SMALL_PATH = "C:/Windows/Fonts/meiryo.ttc"
FONT_MAIN_SIZE = 42
FONT_SMALL_SIZE = 26

# レイアウト設定
IMG_SIZE = 1024
BLOCK_MARGIN_LEFT = 30
BLOCK_MARGIN_TOP = 30
BLOCK_PADDING_X = 24
BLOCK_PADDING_Y = 18
BLOCK_RADIUS = 18
BLOCK_GAP = 20
BLOCK_BG_COLOR = (255, 255, 255, 210)  # 白・やや透明
TEXT_COLOR = (30, 30, 30)
SMALL_TEXT_COLOR = (60, 60, 60)
SMALL_TEXT_MARGIN_RIGHT = 30
SMALL_TEXT_MARGIN_BOTTOM = 30


# --- テキストデータ ---
POSTS = {
    1: {
        "bg_prompt": "A photorealistic square image of a cozy, sunlit cafe. Close-up of a rustic wooden table with a latte with beautiful latte art in a white ceramic cup. Blurred view of a street outside a window in the background. Warm tones, soft lighting. No text, no UI elements, no people.",
        "blocks": [
            "年収を上げたい、スキルを磨きたい。\nそんな転職も、もちろん大切だ。",
            "だが、この年齢になると...\n「平日の夜、家族とゆっくり食卓を囲みたい」\n「週末は仕事から完全に離れたい」",
            "そんな『心のゆとり』を取り戻すための、\n転職。それだって、\n十分に立派なキャリアの選択肢だ。",
        ],
        "small": "結局のところ、そこが\n一番の悩み、だな。☕️",
    },
    2: {
        "bg_prompt": "A photorealistic square image of a modern office break room. Simple white desk with black coffee in a minimalist mug, a smartphone face-down beside it, soft natural light from a large window. Cool tones. No text, no UI elements, no people.",
        "blocks": [
            "「転職したいけど、\n今の会社に不満があるわけじゃない」",
            "そういう人、実はすごく多い。\n不満じゃなくて『違和感』なんだ。\n「このまま、ここで、あと20年？」",
            "その違和感に気づけたことが、\nもう立派な一歩目だと思う。",
        ],
        "small": "不満がないから動けない、\nという矛盾。🤔",
    },
    3: {
        "bg_prompt": "A photorealistic square image of a quiet bar counter in the evening. Glass of whiskey on a dark wooden counter, warm amber lighting, blurred bottles in background. Moody atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "20代の転職は「挑戦」。\n30代の転職は「成長」。",
            "じゃあ40代の転職は？\n俺は『選択』だと思っている。",
            "何を手に入れるかじゃなく、\n何を大切にして生きるか。\nそれを自分で選ぶための転職だ。",
        ],
        "small": "年齢で意味が、\n変わるんだよな。🌙",
    },
    4: {
        "bg_prompt": "A photorealistic square image of a morning train platform with soft golden sunrise light. A few commuters as blurred silhouettes. Clean modern platform with a hint of mist. No text, no UI elements.",
        "blocks": [
            "毎朝この電車に乗って、\nもう何年になるだろう。",
            "ふと思う。\n「この通勤を、あと何年続ける？」\nそう考えた瞬間が、\n転職のスタートラインだ。",
            "焦らなくていい。\nでも、その問いは\n忘れないでほしい。",
        ],
        "small": "今朝、何を考えながら\n電車に乗りましたか？🚃",
    },
    5: {
        "bg_prompt": "A photorealistic square image of a lunch scene at a casual Japanese restaurant. Simple set meal (teishoku) on a wooden tray with miso soup and rice, warm natural lighting. No text, no UI elements, no people.",
        "blocks": [
            "面接で「なぜ転職を？」と聞かれて、\n本音を言えない人が多い。",
            "「成長環境を求めて」なんて建前じゃなく、\n「子どもの行事に出たいから」\n「親の介護が始まるから」\nそれでいいじゃないか。",
            "人生の事情で動く転職は、\n逃げじゃない。\nむしろ一番誠実な選択だ。",
        ],
        "small": "本音で転職理由を\n語れる時代へ。🍚",
    },
    6: {
        "bg_prompt": "A photorealistic square image of an evening home office scene. Warm desk lamp illuminating a notebook and pen on a wooden desk, window showing a dusky blue sky outside. Cozy atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "転職サイトを開いて、\n眺めて、閉じる。\nこれを繰り返していませんか？",
            "大丈夫、それは普通のことだ。\n40代の転職は「衝動」で動かない方がいい。\n時間をかけて、自分の中の\n優先順位を整理するフェーズも大事。",
            "ただ、「見ているだけ」と\n「考えている」は違う。\n今夜、紙に書き出してみよう。",
        ],
        "small": "書くと、見えてくるものが\nあるんだ。📝",
    },
    7: {
        "bg_prompt": "A photorealistic square image of a serene morning park scene with a wooden bench under trees with fresh green leaves. Soft morning sunlight filtering through branches. Peaceful atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "「今の会社で管理職になれた」\n「部下もついてきてくれている」",
            "でも心のどこかで、\n「本当にやりたかったこと、\nこれだっけ？」と思うことがある。",
            "成功しているのに迷う。\nそれは贅沢な悩みじゃない。\n人生の後半戦を真剣に考えている証拠だ。",
        ],
        "small": "成功と充実は、\n別物なんだよな。🌿",
    },
    8: {
        "bg_prompt": "A photorealistic square image of a conference room with a long white table and empty chairs. Natural light through large windows, whiteboard with faded writing in background. Cool corporate atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "40代の転職で一番大事なのは、\n「何ができるか」じゃない。",
            "「何をしたくないか」を\nはっきりさせることだ。\n長時間労働はもう嫌だ。\n意味のない会議はもう嫌だ。\nそれは立派な判断軸になる。",
            "やりたいことが分からなくても、\n「これは嫌だ」が分かれば、\n転職の方向は見えてくる。",
        ],
        "small": "消去法だって、\n立派な戦略だ。💡",
    },
    9: {
        "bg_prompt": "A photorealistic square image of a quiet Japanese izakaya scene. Small ceramic sake cup and plate of edamame on a dark counter, warm moody lighting, blurred red lantern in background. No text, no UI elements, no people.",
        "blocks": [
            "同期が転職して、\nうまくいっている話を聞くと、\n正直、焦る。",
            "でもな、他人の成功パターンは\n参考にはなっても、正解にはならない。\n家族構成も、価値観も、\n体力も、全部違うから。",
            "比べるのは他人じゃなく、\n「半年前の自分」でいい。\nあの頃より、少しでも前に進んでいれば\nそれで十分だ。",
        ],
        "small": "自分のペースで、\nいいんだよ。🍶",
    },
    27: {
        "bg_prompt": "A photorealistic square image of a Japanese family restaurant (famiresu) booth at night. Drink bar glass and dessert plate on table, warm fluorescent lighting. Slightly nostalgic everyday atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "学生時代の友人と久しぶりに会うと、\n「お前、疲れてない？」と言われた。",
            "自分では気づかないんだ。\n毎日少しずつ削られていくから。\n他人の目に映る自分の方が、\n真実に近いことがある。",
            "周りの人が心配してくれているなら、\nそれは「大丈夫じゃないサイン」だ。\n素直に受け取ってみよう。",
        ],
        "small": "他人の方が、\n見えている。🍫",
    },
    28: {
        "bg_prompt": "A photorealistic square image of a bright morning airport terminal. Large windows showing an airplane on the tarmac, morning sunlight flooding the waiting area, empty seats and a carry-on suitcase. No text, no UI elements, no people.",
        "blocks": [
            "40代のキャリアは「飛行機」に似ている。\n離陸はとっくに終わった。",
            "今は巡航高度。\n安定しているが、\nこのまま着陸地点を変えないのか、\nそれとも新しい目的地に進路を変えるのか。",
            "燃料はまだ十分ある。\n着陸するには早すぎる。\nだからこそ、今、\n行き先を考え直す価値がある。",
        ],
        "small": "あなたの燃料は、\nまだ残っている。✈️",
    },
    29: {
        "bg_prompt": "A photorealistic square image of a business card holder open on a desk with several business cards (text blurred). Fountain pen beside it. Clean professional atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "名刺交換した数だけ、\n人脈があると思っていた。",
            "でも40代になって分かった。\n本当に頼れるのは、\n「何かあったら連絡してね」と\n言い合える数人だけだ。",
            "転職でもそう。\n大量応募より、信頼できる人からの\n一本の紹介の方が、\n圧倒的に強い。",
        ],
        "small": "人脈は量じゃなく、\n深さだ。🤝",
    },
    30: {
        "bg_prompt": "A photorealistic square image of a window at night with raindrops on the glass. Warm room interior reflected faintly. City lights blurred through wet window. Contemplative quiet atmosphere. No text, no UI elements, no people.",
        "blocks": [
            "最後に、一つだけ伝えたい。",
            "転職しても、しなくても、\nどちらでもいい。\n大事なのは\n「自分で選んだ」という実感だ。",
            "流されるまま今の会社にいるのと、\n考え抜いた上で残ることを選ぶのは、\n全く違う。\nあなたの人生は、あなたが決めていい。",
        ],
        "small": "選んだ道を、\n正解にすればいい。🌧️",
    },
}


def load_fonts():
    """フォントをロード"""
    font_main = ImageFont.truetype(FONT_MAIN_PATH, FONT_MAIN_SIZE)
    font_small = ImageFont.truetype(FONT_SMALL_PATH, FONT_SMALL_SIZE)
    return font_main, font_small


def get_text_size(draw, text, font):
    """テキストのバウンディングボックスサイズを取得"""
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_rounded_rect(draw, xy, radius, fill):
    """角丸の矩形を描画"""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def overlay_text(bg_image, blocks, small_text, font_main, font_small):
    """背景画像にテキストブロックを重ねる"""
    # RGBA に変換
    img = bg_image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    y_cursor = BLOCK_MARGIN_TOP

    for block_text in blocks:
        # テキストサイズを計算
        tw, th = get_text_size(draw, block_text, font_main)

        # ブロックの矩形
        bx0 = BLOCK_MARGIN_LEFT
        by0 = y_cursor
        bx1 = bx0 + tw + BLOCK_PADDING_X * 2
        by1 = by0 + th + BLOCK_PADDING_Y * 2

        # 画像幅を超えないようにクランプ
        if bx1 > IMG_SIZE - BLOCK_MARGIN_LEFT:
            bx1 = IMG_SIZE - BLOCK_MARGIN_LEFT

        # 角丸白背景
        draw_rounded_rect(draw, (bx0, by0, bx1, by1), BLOCK_RADIUS, BLOCK_BG_COLOR)

        # テキスト描画
        draw.multiline_text(
            (bx0 + BLOCK_PADDING_X, by0 + BLOCK_PADDING_Y),
            block_text,
            font=font_main,
            fill=TEXT_COLOR,
        )

        y_cursor = by1 + BLOCK_GAP

    # 右下の小テキスト
    if small_text:
        stw, sth = get_text_size(draw, small_text, font_small)
        sx = IMG_SIZE - stw - SMALL_TEXT_MARGIN_RIGHT
        sy = IMG_SIZE - sth - SMALL_TEXT_MARGIN_BOTTOM
        draw.multiline_text(
            (sx, sy),
            small_text,
            font=font_small,
            fill=SMALL_TEXT_COLOR,
            align="right",
        )

    # 合成
    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


def generate_background(prompt):
    """DALL-E 3 で背景画像を生成"""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1,
    )
    image_url = response.data[0].url
    img_data = requests.get(image_url).content
    return Image.open(BytesIO(img_data))


def main():
    font_main, font_small = load_fonts()

    print(f"=== Instagram Stories v2: 背景生成 + テキスト合成 ===")
    print(f"出力先: {OUTPUT_DIR}\n")

    results = []
    for post_num in sorted(POSTS.keys()):
        data = POSTS[post_num]
        print(f"[Post {post_num:02d}] 背景生成中...")

        try:
            bg = generate_background(data["bg_prompt"])
            print(f"[Post {post_num:02d}] テキスト合成中...")
            final = overlay_text(bg, data["blocks"], data["small"], font_main, font_small)

            timestamp = int(time.time() * 1000)
            filename = f"post_{post_num:02d}_{timestamp}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            final.save(filepath, "PNG")
            print(f"[Post {post_num:02d}] 完了: {filename}")
            results.append((post_num, filename))
        except Exception as e:
            print(f"[Post {post_num:02d}] エラー: {e}")
            results.append((post_num, None))

        time.sleep(15)

    print(f"\n=== 完了 ===")
    success = sum(1 for _, f in results if f)
    print(f"成功: {success}/13")
    for post_num, filename in results:
        status = filename if filename else "失敗"
        print(f"  Post {post_num:02d}: {status}")


if __name__ == "__main__":
    main()
