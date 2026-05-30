import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv, json

INPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\comicle_output.csv'
OUTPUT = INPUT  # overwrite

rows = []
with open(INPUT, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

header = rows[0]
data = rows[1:]

# Pages to fix and their additional text panels
# Format: page_num -> list of new panel dicts to append
fixes = {
    # P5 (57 chars): Zoom前準備
    5: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "昼寝の時間は限られている。でも今日だけは、絶対に間に合わせる。"}],

    # P7 (58 chars): よろしくお願いします
    7: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "タクヤの問いは、予想外に深かった。ミサキは少し間を置いた。"}],

    # P15 (53 chars): Claudeとの会話に驚く
    15: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "タクヤは笑顔で続けた。「その指示の感覚が、そのまま強みになります」"},
          {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "……私、なんか変なことしちゃった？"}],

    # P25 (60 chars): 止めないことが大事
    25: [{"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "止めない。それだけ覚えておこう。何があっても、止めない。"}],

    # P26 (64 chars): タクヤ「また動き出せること」
    26: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "ミサキは涙が出そうになった。でも今日は泣かない、と決めていた。"}],

    # P31 (64 chars): ひなたとZoom前の会話
    31: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "「わかってるよ」とミサキはひなたの頭を撫でた。よし、行こう。"}],

    # P32 (50 chars): AIへの最初の一言
    32: [{"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "これが始まり。私とAIの、最初の会話。"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "入力ボタンを押した瞬間、何かが変わった気がした。"}],

    # P41 (58 chars): AIが3パターン出す
    41: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "選ぶことも、仕事だ。AIに任せるだけじゃなく、自分で決める。それが大事なんだ。"}],

    # P47 (56 chars): もしかしたら確信に変わる夜
    47: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "「もしかしたら」は、今夜から「きっとできる」に変わっていた。"}],

    # P54 (60 chars): 初コメント
    54: [{"panel_id": 3, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "ありがとう。あなたのことは知らない。でも、ありがとう。"}],

    # P56 (60 chars): 比べてしまう気持ち
    56: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "嫉妬も、怒りも、全部書いた。Claudeは怒らない。だから正直に書けた。"}],

    # P66 (51 chars): フォロワー11人の孤独
    66: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "数字の向こうに「人」がいる。その人に届けるために、明日もやる。"}],

    # P78 (51 chars): ひなたの発熱を発見
    78: [{"panel_id": 4, "type": "narration", "speaker": None, "text": "ケンタには連絡しなかった。心配させたくなかった。一人でやれると思いたかった。"}],

    # P81 (57 chars): 深夜ワンオペ
    81: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "ミサキにとって、ひなたの手の温かさが、すべての原点だった。"}],

    # P84 (58 chars): 「止めない」こと
    84: [{"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "止めない。それだけが私の武器だ。完璧じゃなくても、止めなければいい。"}],

    # P91 (62 chars): 再開投稿テーマ
    91: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "ミサキは③に大きく丸をつけた。この話を書けるのは、自分しかいない。"}],

    # P96 (62 chars): 継続の形
    96: [{"panel_id": 1, "type": "narration", "speaker": None, "text": "コラム⑦：止めないことが一番の戦略。ミサキが3ヶ月で学んだ、最大の教訓。"}],

    # P100 (52 chars): フォロワー減少
    100: [{"panel_id": 3, "type": "narration", "speaker": None, "text": "でも減った分は、また増やせる。やめなければ、必ず戻せる。"},
          {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "今夜も投稿する。それだけやればいい"}],

    # P106 (50 chars): 続けることの積み重ね
    106: [{"panel_id": 2, "type": "narration", "speaker": None, "text": "一日も止まらなかった日はない。でも一度も完全にやめなかった。その差が、すべてだった。"}],
}

fixed_count = 0
for row in data:
    pg = int(row[0])
    if pg in fixes:
        try:
            panels = json.loads(row[3])
            panels.extend(fixes[pg])
            row[3] = json.dumps(panels, ensure_ascii=False)
            fixed_count += 1
        except Exception as e:
            print(f'ERROR on P{pg}: {e}')

print(f'Fixed {fixed_count} pages')

# Final stats
image_data = [r for r in data if r[1] != 'テキストページ']
image_total = len(image_data)
total_chars = 0
low90 = 0
low50 = 0
for row in image_data:
    try:
        panels = json.loads(row[3])
        chars = sum(len(p.get('text','')) for p in panels)
        total_chars += chars
        if chars < 90:
            low90 += 1
        if chars < 50:
            low50 += 1
    except:
        pass

avg = total_chars / image_total
print(f'Final average chars/page: {avg:.1f}')
print(f'Pages under 90 chars: {low90}')
print(f'Pages under 50 chars: {low50}')
print(f'Total pages: {len(data)}')

# Write
with open(OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for row in data:
        writer.writerow(row)

print(f'Saved to {OUTPUT}')
