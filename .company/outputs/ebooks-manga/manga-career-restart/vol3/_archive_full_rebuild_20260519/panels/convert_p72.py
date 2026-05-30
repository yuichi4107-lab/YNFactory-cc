import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv, json

INPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\comicle_output.csv'

rows = []
with open(INPUT, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

header = rows[0]
data = rows[1:]

new_prompt_p72 = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画
◆【補足情報】服装: ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー（自宅・外出・育児中の普段着）
◆【コマ構成】テンプレ1: ページ全体1コマ
◆【出力サイズ】2:3
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現 / 演出: パソコン作業,スマホ,時計,収入の可視化,必要に応じて集中線,効果線,擬音などのマンガらしい演出
◆【ストーリー】
1コマ目 (全面): 朝の寝室。ミサキがひなたをぎゅっと抱きしめている。ひなたは顔色が戻り、ミサキの頬に小さな手を当てている。窓から朝の光が差し込む。ミサキの目から涙がこぼれている。温かく、優しい光と構図で。集中線で感情を強調。 セリフ: ［ミサキ（内心）］の吹き出しに「よかった……本当によかった」 ナレーション: ［四角枠］3日ぶりに、ひなたが元気な声を出した。熱が引いた。ひなたは戻ってきた。そしてミサキも、もう一度始められる。 オノマトペ: なし"""

new_json_p72 = json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "よかった……本当によかった"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "3日ぶりに、ひなたが元気な声を出した。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "熱が引いた。ひなたは戻ってきた。そしてミサキも、もう一度始められる。"}
], ensure_ascii=False)

for row in data:
    if row[0] == '72':
        row[1] = 'テンプレ1'
        row[2] = new_prompt_p72
        row[3] = new_json_p72
        print('P72 converted to テンプレ1')

# Save
with open(INPUT, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for row in data:
        writer.writerow(row)

# Final count
image_data = [r for r in data if r[1] != 'テキストページ']
image_total = len(image_data)
template_counts = {}
for row in image_data:
    t = row[1]
    template_counts[t] = template_counts.get(t, 0) + 1

t1 = template_counts.get('テンプレ1', 0)
t2_4 = sum(template_counts.get('テンプレ' + str(n), 0) for n in [2,3,4])
t5_7 = sum(template_counts.get('テンプレ' + str(n), 0) for n in [5,6,7])
print(f'T1: {t1} ({t1/image_total*100:.1f}%)')
print(f'T2-4: {t2_4} ({t2_4/image_total*100:.1f}%) [goal: 30-40%]')
print(f'T5-7: {t5_7} ({t5_7/image_total*100:.1f}%) [goal: 40-50%]')

total_chars = 0
for row in image_data:
    try:
        panels = json.loads(row[3])
        chars = sum(len(p.get('text','')) for p in panels)
        total_chars += chars
    except:
        pass
avg = total_chars / image_total
print(f'Average chars: {avg:.1f}')
print('Saved.')
