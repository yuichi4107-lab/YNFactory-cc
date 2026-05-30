"""
Instagram Stories 残り13枚（post_01〜09, 27〜30）を生成するスクリプト
DALL-E 3 API で正方形（1024x1024）画像を生成
"""

import os
import time
import requests
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 残り13枚のプロンプト（post番号: プロンプト）
PROMPTS = {
    1: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, set in a cozy, sunlit cafe. The background is a close-up of a rustic wooden table with a latte with beautiful latte art in a white ceramic cup. There is a blurred view of a street outside a window in the background. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements (no profile pictures, no usernames, no reply bars). The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 年収を上げたい、スキルを磨きたい。\nそんな転職も、もちろん大切だ。 Middle block: だが、この年齢になると...\n「平日の夜、家族とゆっくり食卓を囲みたい」\n「週末は仕事から完全に離れたい」 Bottom block: そんな『心のゆとり』を取り戻すための、\n転職。それだって、\n十分に立派なキャリアの選択肢だ。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 結局のところ、そこが\n一番の悩み、だな。☕️',

    2: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, set in a modern office break room. The background shows a simple white desk with a black coffee in a minimalist mug, a smartphone face-down beside it, and soft natural light from a large window. The entire background image has a slight, cool-toned fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 「転職したいけど、\n今の会社に不満があるわけじゃない」 Middle block: そういう人、実はすごく多い。\n不満じゃなくて『違和感』なんだ。\n「このまま、ここで、あと20年？」 Bottom block: その違和感に気づけたことが、\nもう立派な一歩目だと思う。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 不満がないから動けない、\nという矛盾。🤔',

    3: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, set at a quiet bar counter in the evening. The background shows a glass of whiskey on a dark wooden counter, with warm amber lighting and blurred bottles in the background. The entire background image has a slight, warm dark fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 20代の転職は「挑戦」。\n30代の転職は「成長」。 Middle block: じゃあ40代の転職は？\n俺は『選択』だと思っている。 Bottom block: 何を手に入れるかじゃなく、\n何を大切にして生きるか。\nそれを自分で選ぶための転職だ。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 年齢で意味が、\n変わるんだよな。🌙',

    4: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a morning scene of a train platform with soft golden sunrise light. A few commuters are seen as blurred silhouettes. The platform is clean and modern, with a hint of mist. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 毎朝この電車に乗って、\nもう何年になるだろう。 Middle block: ふと思う。\n「この通勤を、あと何年続ける？」\nそう考えた瞬間が、\n転職のスタートラインだ。 Bottom block: 焦らなくていい。\nでも、その問いは\n忘れないでほしい。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 今朝、何を考えながら\n電車に乗りましたか？🚃',

    5: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a lunch scene at a casual Japanese restaurant. The background shows a simple set meal (teishoku) on a wooden tray, with miso soup and rice, in warm natural lighting. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 面接で「なぜ転職を？」と聞かれて、\n本音を言えない人が多い。 Middle block: 「成長環境を求めて」なんて建前じゃなく、\n「子どもの行事に出たいから」\n「親の介護が始まるから」\nそれでいいじゃないか。 Bottom block: 人生の事情で動く転職は、\n逃げじゃない。\nむしろ一番誠実な選択だ。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 本音で転職理由を\n語れる時代へ。🍚',

    6: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing an evening home office scene. A warm desk lamp illuminates a notebook and pen on a wooden desk, with a window showing a dusky blue sky outside. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 転職サイトを開いて、\n眺めて、閉じる。\nこれを繰り返していませんか？ Middle block: 大丈夫、それは普通のことだ。\n40代の転職は「衝動」で動かない方がいい。\n時間をかけて、自分の中の\n優先順位を整理するフェーズも大事。 Bottom block: ただ、「見ているだけ」と\n「考えている」は違う。\n今夜、紙に書き出してみよう。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 書くと、見えてくるものが\nあるんだ。📝',

    7: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a serene morning park scene with a wooden bench under cherry blossom trees with fresh green leaves. Soft morning sunlight filters through the branches. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 「今の会社で管理職になれた」\n「部下もついてきてくれている」 Middle block: でも心のどこかで、\n「本当にやりたかったこと、\nこれだっけ？」と思うことがある。 Bottom block: 成功しているのに迷う。\nそれは贅沢な悩みじゃない。\n人生の後半戦を真剣に考えている証拠だ。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 成功と充実は、\n別物なんだよな。🌿',

    8: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a conference room with a long white table and empty chairs. Natural light streams through large windows, and there is a whiteboard with faded writing in the background. The entire background image has a slight, cool-toned fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 40代の転職で一番大事なのは、\n「何ができるか」じゃない。 Middle block: 「何をしたくないか」を\nはっきりさせることだ。\n\n長時間労働はもう嫌だ。\n意味のない会議はもう嫌だ。\nそれは立派な判断軸になる。 Bottom block: やりたいことが分からなくても、\n「これは嫌だ」が分かれば、\n転職の方向は見えてくる。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 消去法だって、\n立派な戦略だ。💡',

    9: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a quiet Japanese izakaya scene. A small ceramic sake cup and a plate of edamame on a dark counter, with warm, moody lighting and a blurred red lantern in the background. The entire background image has a slight, warm dark fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 同期が転職して、\nうまくいっている話を聞くと、\n正直、焦る。 Middle block: でもな、他人の成功パターンは\n参考にはなっても、正解にはならない。\n家族構成も、価値観も、\n体力も、全部違うから。 Bottom block: 比べるのは他人じゃなく、\n「半年前の自分」でいい。\nあの頃より、少しでも前に進んでいれば\nそれで十分だ。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 自分のペースで、\nいいんだよ。🍶',

    27: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a night scene of a Japanese family restaurant (famiresu) booth. A drink bar glass and a dessert plate on the table, warm fluorescent lighting. A slightly nostalgic, everyday atmosphere. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 学生時代の友人と久しぶりに会うと、\n「お前、疲れてない？」と言われた。 Middle block: 自分では気づかないんだ。\n毎日少しずつ削られていくから。\n他人の目に映る自分の方が、\n真実に近いことがある。 Bottom block: 周りの人が心配してくれているなら、\nそれは「大丈夫じゃないサイン」だ。\n素直に受け取ってみよう。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 他人の方が、\n見えている。🍫',

    28: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a bright morning airport terminal. Large windows showing an airplane on the tarmac, morning sunlight flooding the waiting area. Empty seats and a carry-on suitcase. The entire background image has a slight, warm fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 40代のキャリアは「飛行機」に似ている。\n離陸はとっくに終わった。 Middle block: 今は巡航高度。\n安定しているが、\nこのまま着陸地点を変えないのか、\nそれとも新しい目的地に進路を変えるのか。 Bottom block: 燃料はまだ十分ある。\n着陸するには早すぎる。\nだからこそ、今、\n行き先を考え直す価値がある。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: あなたの燃料は、\nまだ残っている。✈️',

    29: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a business card holder open on a desk, with several business cards visible (text on cards is blurred and unreadable). A fountain pen lies beside it. Clean, professional atmosphere. The entire background image has a slight, neutral fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 名刺交換した数だけ、\n人脈があると思っていた。 Middle block: でも40代になって分かった。\n本当に頼れるのは、\n「何かあったら連絡してね」と\n言い合える数人だけだ。 Bottom block: 転職でもそう。\n大量応募より、信頼できる人からの\n一本の紹介の方が、\n圧倒的に強い。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 人脈は量じゃなく、\n深さだ。🤝',

    30: 'A photorealistic square image (1024x1024 pixels), suitable for Instagram Stories, showing a night scene of a window with raindrops on the glass. A warm room interior is reflected faintly. City lights are blurred through the wet window. A contemplative, quiet atmosphere. The entire background image has a slight, warm dark fade to make the text easily readable. Do not include any social media UI elements. The main text consists of three separate, left-aligned, block-shaped text boxes with rounded corners and a white, slightly opaque fill. The text inside the blocks is Japanese Gothic font: Top block: 最後に、一つだけ伝えたい。 Middle block: 転職しても、しなくても、\nどちらでもいい。\n大事なのは\n「自分で選んだ」という実感だ。 Bottom block: 流されるまま今の会社にいるのと、\n考え抜いた上で残ることを選ぶのは、\n全く違う。\nあなたの人生は、あなたが決めていい。 Below the main text, aligned to the bottom right, without a background block, in smaller, regular Japanese font: 選んだ道を、\n正解にすればいい。🌧️',
}


def generate_image(post_num, prompt):
    """DALL-E 3 APIで画像生成し保存"""
    print(f"[Post {post_num:02d}] 生成中...")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url
        # 画像をダウンロード
        img_data = requests.get(image_url).content
        timestamp = int(time.time() * 1000)
        filename = f"post_{post_num:02d}_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(img_data)
        print(f"[Post {post_num:02d}] 保存完了: {filename}")
        return filename
    except Exception as e:
        print(f"[Post {post_num:02d}] エラー: {e}")
        return None


def main():
    print(f"=== Instagram Stories 残り13枚 生成開始 ===")
    print(f"出力先: {OUTPUT_DIR}\n")

    results = []
    for post_num in sorted(PROMPTS.keys()):
        filename = generate_image(post_num, PROMPTS[post_num])
        results.append((post_num, filename))
        # レート制限対策（DALL-E 3は1分5リクエスト制限あり）
        if filename:
            time.sleep(15)

    print(f"\n=== 完了 ===")
    success = sum(1 for _, f in results if f)
    print(f"成功: {success}/13")
    for post_num, filename in results:
        status = filename if filename else "失敗"
        print(f"  Post {post_num:02d}: {status}")


if __name__ == "__main__":
    main()
