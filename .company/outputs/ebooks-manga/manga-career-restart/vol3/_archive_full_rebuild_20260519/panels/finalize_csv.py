import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv, json, re

INPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\work_step4.csv'
OUTPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\comicle_output.csv'

# ==================
# STEP 1: Read work_step4.csv
# ==================
rows = []
with open(INPUT, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

header = rows[0]
data = rows[1:]

# ==================
# STEP 2: Fix text density on low-density pages
# Pages that need text added: 14, 16, 22, 31, 58, 64, 71, 76, 82, 87, 91, 99
# (P4 and P46 are chapter openers - empty JSON is intentional)
# ==================

def replace_json(data, page_num, new_json_str):
    for row in data:
        if int(row[0]) == page_num:
            row[3] = new_json_str
            return True
    return False

# P14: ミサキがClaudeを初めて見た瞬間 (currently 26 chars -> need 90+)
replace_json(data, 14, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "……すごい"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "画面に文字が流れ始めた。——日本語だった。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ミサキが入力したのはたった一行。なのにClaudeは、3段落もの文章を返してきた。"},
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "私の言葉を読んで……答えてくれてる"}
], ensure_ascii=False))

# P16: 指示の解像度比較ページ (currently 23 chars -> need 90+)
replace_json(data, 16, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "指示の解像度で、AIの答えはまるで別物になる。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "NG: 「SNS投稿を書いて」→ 平凡な文章。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "OK: 「元事務職の32歳ママが育児中にAIで副業を始めた体験談を書いて」→ 読まれる文章。"},
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "どれだけ自分のことを伝えるかが、カギなんだ"}
], ensure_ascii=False))

# P22: ひなたが起きてZoom中断 (currently 35 chars -> need 90+)
replace_json(data, 22, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "そのとき——。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ", "text": "あっ、すみません——！"},
    {"panel_id": 2, "type": "narration", "speaker": None, "text": "ひなたが目を覚ました。「まーまー！」という声が部屋に響く。"},
    {"panel_id": 3, "type": "dialogue", "speaker": "タクヤ", "text": "大丈夫ですよ。育児しながらのほうが、話に説得力が出ますから"},
    {"panel_id": 3, "type": "narration", "speaker": None, "text": "タクヤは笑っていた。焦るミサキをよそに、穏やかに。"}
], ensure_ascii=False))

# P31: AIの出力を見てミサキが絶句 (currently 37 chars -> need 90+)
replace_json(data, 31, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "……すごい"},
    {"panel_id": 2, "type": "dialogue", "speaker": "タクヤ", "text": "どうです？"},
    {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ", "text": "私が言いたかったこと、全部書いてある。私より上手に"},
    {"panel_id": 3, "type": "narration", "speaker": None, "text": "言葉にできなかった「何か」を、AIが形にしてくれた。"},
    {"panel_id": 3, "type": "dialogue", "speaker": "タクヤ", "text": "あなたの経験と感情があるから、出てきた文章です。AIだけでは出ない"}
], ensure_ascii=False))

# P58: 投稿ボタンを押す瞬間 (currently 49 chars -> need 90+)
replace_json(data, 58, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ミサキは投稿ボタンに指を乗せた。自分の言葉が、経験が、世界中に公開される——その瞬間。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "3秒、止まった。怖かった。でも怖いのは、届くかもしれないから。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ", "text": "……えいっ！"},
    {"panel_id": 2, "type": "narration", "speaker": None, "text": "画面が切り替わった。投稿完了。取り消せない。"}
], ensure_ascii=False))

# P64: 「佐藤さんらしさがない」の衝撃 (currently 29 chars -> need 90+)
replace_json(data, 64, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "タクヤ（回想）", "text": "これ、佐藤さんらしさが全然ないですよ"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "その言葉が、刺さった。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ミサキは「いい文章」を書こうとしていた。でもタクヤが言ったのは「あなたの文章」だった。"},
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "らしさって……何？ 私って何者なの？"}
], ensure_ascii=False))

# P71: ひなたが突然発熱 (currently 28 chars -> need 90+)
replace_json(data, 71, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "ひなた！？"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "転機のまさにその矢先——夜中に、事件が起きた。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ひなたが突然泣き出した。おでこを触ると、熱い。体温計を取り出す手が震えた。"},
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "どうして今……でも今じゃなくていい発熱なんてない"}
], ensure_ascii=False))

# P76: 看病しながら自分を責めるミサキ (currently 46 chars -> need 90+)
replace_json(data, 76, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "やっぱり育児しながらは無理なのかな……"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ひなたの額にタオルを当てながら、ミサキは自分を責め続けていた。"},
    {"panel_id": 2, "type": "narration", "speaker": None, "text": "子供は計画通りにいかない——タクヤの言葉が頭をよぎる。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "でもタクヤ先生、私は今、計画が全部崩れました"}
], ensure_ascii=False))

# P82: 発熱3日目の朝 (currently 45 chars -> need 90+)
replace_json(data, 82, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "はぁぁ、と長い息をついた。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "3日間、ひなたの看病と仕事の準備と投稿が全部止まっていた。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "……前提に立ち返ろう。私はなぜこれをやっているんだっけ"},
    {"panel_id": 2, "type": "narration", "speaker": None, "text": "答えは変わらなかった。ひなたに、胸を張れる母親でいたい。"}
], ensure_ascii=False))

# P87: コメントを何度も読む (currently 39 chars -> need 90+)
replace_json(data, 87, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "見知らぬ誰かの言葉が、画面に並んでいた。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "「私もそうだった」「共感しすぎて泣いた」「続けてください」"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "本当に……届いた"},
    {"panel_id": 2, "type": "narration", "speaker": None, "text": "何度も、何度も読んだ。スクリーンショットも撮った。スマホの中の宝物になった。"}
], ensure_ascii=False))

# P91: ひなた発熱・ケンタ出張 (currently 40 chars -> need 90+)
replace_json(data, 91, json.dumps([
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "転機のまさにその矢先だった。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ケンタが出張に出た翌朝、ひなたが37.8度を記録した。"},
    {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "……38度5分"},
    {"panel_id": 3, "type": "narration", "speaker": None, "text": "夜には38.5度まで上がった。ケンタへの電話は、かけなかった。心配させたくなかった。"},
    {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "私がやる。私がやれる"}
], ensure_ascii=False))

# P99: 第6章の締め大ゴマ (currently 22 chars -> need 90+)
replace_json(data, 99, json.dumps([
    {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "続けた。それだけで、十分だった"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "第6章　終わり"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "フォロワー40人超え、本物のコメント2件。数字は小さくても、ミサキの中では革命だった。"},
    {"panel_id": 1, "type": "narration", "speaker": None, "text": "ひなたを抱きしめながら、ミサキは空を見上げた。まだ始まったばかり——でも、もう一歩進んでいた。"}
], ensure_ascii=False))

print("Text density fixes applied.")

# ==================
# STEP 3: Add 8 more pages (T2-4 priority, high text density)
# Target spots based on narrative flow:
# All 8 come from scenario content
# ==================

COMMON_PREFIX = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。"""

STYLE_SUFFIX = """◆【出力サイズ】2:3
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現 / 演出: パソコン作業,スマホ,時計,収入の可視化,必要に応じて集中線,効果線,擬音などのマンガらしい演出"""

OUTFIT_NOTES = {
    'misaki_work_home': '◆【補足情報】服装: グレーのスウェット上下、髪を緩くまとめ、素足（深夜〜早朝のPC作業・在宅集中タイム）',
    'misaki_casual': '◆【補足情報】服装: ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー（自宅・外出・育児中の普段着）',
    'kenta_work_casual': '◆【補足情報】服装: ネイビーのポロシャツにチノパン（帰宅後のリラックス時やオフ日の外出着）',
    'takuya_zoom_mentor': '◆【補足情報】服装: ライトグレーのシャツにジャケット（Zoom・コーチング時の半フォーマルスタイル）',
}

CHAR_NOTES = {
    'misaki_work_home': 'ミサキは添付のミサキ.pngと100%同一の外見で描画',
    'misaki_casual_hinata': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
    'misaki_kenta': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, ケンタは添付のケンタ.pngと100%同一の外見で描画',
    'misaki_takuya': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, タクヤは添付のタクヤ.pngと100%同一の外見で描画',
}

TEMPLATE_NAMES = {
    'テンプレ2': 'テンプレ2: 上下2段',
    'テンプレ3': 'テンプレ3: 上小＋下大',
    'テンプレ4': 'テンプレ4: 上大＋下小',
}

def build_prompt(template, outfit_key, story_text):
    char_note = CHAR_NOTES.get(outfit_key, CHAR_NOTES['misaki_work_home'])
    outfit_note = OUTFIT_NOTES.get(outfit_key.split('_')[0] + '_' + '_'.join(outfit_key.split('_')[1:]), OUTFIT_NOTES['misaki_work_home'])
    # Find outfit note
    for k in OUTFIT_NOTES:
        if outfit_key.startswith(k) or k.startswith(outfit_key.split('_')[0]):
            outfit_note_use = OUTFIT_NOTES[k]
            break
    else:
        outfit_note_use = OUTFIT_NOTES['misaki_work_home']
    # override
    if 'misaki_work_home' in outfit_key:
        outfit_note_use = OUTFIT_NOTES['misaki_work_home']
    elif 'misaki_casual' in outfit_key:
        outfit_note_use = OUTFIT_NOTES['misaki_casual']
    elif 'kenta' in outfit_key:
        outfit_note_use = OUTFIT_NOTES['kenta_work_casual']
    elif 'takuya' in outfit_key:
        outfit_note_use = OUTFIT_NOTES['takuya_zoom_mentor']

    tmpl_name = TEMPLATE_NAMES.get(template, template)
    return f"""{COMMON_PREFIX}
◆【絶対最優先】キャラクター外見: {char_note}
{outfit_note_use}
◆【コマ構成】{tmpl_name}
{STYLE_SUFFIX}
◆【ストーリー】
{story_text}"""

# 8 additional pages: (after_page_num, template, outfit_key, story_text, json_text)
additional_pages = [
    # A1. After P19: Claudeに「私の動機」を入力する
    (19, 'テンプレ4', 'misaki_work_home',
     """1コマ目 (上大): ミサキがキーボードに向かい、真剣な表情でClaudeに入力している。入力途中の文章が画面に見える。「私は32歳の元事務職ママです。産後に退職して、今は育児しながら副業を始めようとしています。私の経験を活かしたSNS投稿のアイデアを出してください」 セリフ: なし ナレーション: ［四角枠］タクヤのアドバイスを思い出しながら、ミサキは自分のことをすべて正直に書いた。 オノマトペ: カタカタカタ
2コマ目 (下小): Claudeの応答が次々と画面に表示される。ミサキが画面をスクロールしながら目を輝かせる。 セリフ: ［ミサキ（内心）］の吹き出しに「これ、全部私のことだ」 ナレーション: なし オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "タクヤのアドバイスを思い出しながら、ミサキは自分のことをすべて正直に書いた。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "これ、全部私のことだ"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "画面に並ぶ言葉は、ミサキが言語化できなかった思いそのものだった。"}
     ], ensure_ascii=False)),

    # A2. After P26: プロフィール作成で「強み」を発見する
    (26, 'テンプレ3', 'misaki_work_home',
     """1コマ目 (上小): タクヤがZoom越しに問いかける。 セリフ: ［タクヤ］の吹き出しに「佐藤さんの強みって、何だと思いますか？」 ナレーション: なし オノマトペ: なし
2コマ目 (下大): ミサキが答えに詰まって沈黙している。でも手元のメモには「事務経験10年」「細かい作業が得意」「育児の経験」と書かれている。静かな気づきが顔に広がる。 セリフ: ［ミサキ（内心）］の吹き出しに「強みって……普通のことしかない気がする。でも、それが強みなのかな」 ナレーション: ［四角枠］「普通」だと思っていたことが、誰かには「特別」に見える。それが強みだ、とタクヤは言った。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "dialogue", "speaker": "タクヤ", "text": "佐藤さんの強みって、何だと思いますか？"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "強みって……普通のことしかない気がする。でも、それが強みなのかな"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "「普通」だと思っていたことが、誰かには「特別」に見える。それが強みだ、とタクヤは言った。"}
     ], ensure_ascii=False)),

    # A3. After P35: プロフィール完成の達成感
    (35, 'テンプレ2', 'misaki_work_home',
     """1コマ目 (上): パソコン画面アップ。SNSのプロフィール欄に「元事務職10年×産後ワンオペ×AIで副業開始中のミサキ。子育てしながら自分の可能性を広げる実録を発信中。」と書かれている。 セリフ: なし ナレーション: ［四角枠］タクヤと3回のZoomを経て、ミサキのプロフィールが完成した。 オノマトペ: なし
2コマ目 (下): ミサキが画面の前でそっと微笑む。両手を軽く胸の前で組んでいる。感慨深そうな表情。 セリフ: ［ミサキ（内心）］の吹き出しに「これが私の自己紹介。32年かけて、やっと言葉にできた」 ナレーション: ［四角枠］自分を言葉にするのが、こんなに怖くて、こんなに気持ちいいとは知らなかった。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "タクヤと3回のZoomを経て、ミサキのプロフィールが完成した。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "これが私の自己紹介。32年かけて、やっと言葉にできた"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "自分を言葉にするのが、こんなに怖くて、こんなに気持ちいいとは知らなかった。"}
     ], ensure_ascii=False)),

    # A4. After P44: ゼロ反応の中でも続ける意地
    (44, 'テンプレ4', 'misaki_work_home',
     """1コマ目 (上大): ミサキが夜中にパソコンに向かっている。投稿スケジュールをメモした紙が貼られている。今日で7日連続投稿。「いいね0」が続いているが、ミサキの表情は諦めていない。 セリフ: ［ミサキ（内心）］の吹き出しに「誰にも見られていなくても、投稿することで私は変わっている」 ナレーション: ［四角枠］7日連続投稿。いいねはまだゼロ。でもミサキは止まらなかった。 オノマトペ: カチャ
2コマ目 (下小): ミサキが投稿ボタンを押す瞬間。小さなガッツポーズ。 セリフ: ［ミサキ（内心）］の吹き出しに「よし、今日も投稿した」 ナレーション: なし オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "誰にも見られていなくても、投稿することで私は変わっている"},
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "7日連続投稿。いいねはまだゼロ。でもミサキは止まらなかった。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "よし、今日も投稿した"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "小さな達成感が、確かに積み上がっていた。"}
     ], ensure_ascii=False)),

    # A5. After P55: 自分の言葉を探す作業
    (55, 'テンプレ3', 'misaki_work_home',
     """1コマ目 (上小): ミサキが過去の投稿を見返している。スマートフォンのスクロール。 セリフ: ［ミサキ（内心）］の吹き出しに「これ……誰でも言えること。私じゃなくていい」 ナレーション: ［四角枠］タクヤに言われた言葉が頭から離れなかった。 オノマトペ: なし
2コマ目 (下大): ミサキがノートに書き出している。「産後に感じた孤独」「お金の不安を初めて夫に言えた日」「ひなたが初めて立った瞬間に仕事の話を思い出した罪悪感」。ペンが止まる。 セリフ: ［ミサキ（内心）］の吹き出しに「これは……私にしかない話だ」 ナレーション: ［四角枠］誰にでも言えることではなく、自分にしか言えないことを探す。それが「らしさ」の正体だった。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "これ……誰でも言えること。私じゃなくていい"},
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "タクヤに言われた言葉が頭から離れなかった。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "これは……私にしか言えない話だ"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "誰にでも言えることではなく、自分にしか言えないことを探す。それが「らしさ」の正体だった。"}
     ], ensure_ascii=False)),

    # A6. After P66: ひなたの熱が下がった朝
    (66, 'テンプレ2', 'misaki_casual_hinata',
     """1コマ目 (上): 朝の寝室。ひなたが目を覚まして「まーまー」と呼んでいる。顔色が戻っている。ミサキが額を確認すると——。 セリフ: ［ひなた］の吹き出しに「まーまー！まんまー！」 ナレーション: ［四角枠］3日ぶりに、ひなたが元気な声を出した。 オノマトペ: なし
2コマ目 (下): ミサキがひなたを抱きしめて目を潤ませる。ひなたはミサキの頬に手を当てている。温かい朝の光。 セリフ: ［ミサキ（内心）］の吹き出しに「よかった。本当によかった」 ナレーション: ［四角枠］熱が引いた。ひなたは戻ってきた。そしてミサキも、もう一度始められる。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "dialogue", "speaker": "ひなた", "text": "まーまー！まんまー！"},
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "3日ぶりに、ひなたが元気な声を出した。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "よかった。本当によかった"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "熱が引いた。ひなたは戻ってきた。そしてミサキも、もう一度始められる。"}
     ], ensure_ascii=False)),

    # A7. After P79: タクヤとの面談報告
    (79, 'テンプレ4', 'misaki_takuya',
     """1コマ目 (上大): Zoom面談。ミサキがタクヤに報告している。「フォロワー40人超え、本物のコメント2件」と書いたメモを見せている。タクヤが前のめりで聞いている。 セリフ: ［ミサキ］の吹き出しに「数字は小さいですが……本物の人から、初めて言葉をもらいました」 ナレーション: ［四角枠］3ヶ月間の成果を、ミサキは正直に報告した。 オノマトペ: なし
2コマ目 (下小): タクヤが目を細めて深くうなずく。 セリフ: ［タクヤ］の吹き出しに「それで十分です。最初の一人が動いてくれた。あとは続けるだけ」 ナレーション: ［四角枠］合格、とタクヤは言わなかった。でもその笑顔が、すべてを語っていた。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "dialogue", "speaker": "ミサキ", "text": "数字は小さいですが……本物の人から、初めて言葉をもらいました"},
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "3ヶ月間の成果を、ミサキは正直に報告した。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "タクヤ", "text": "それで十分です。最初の一人が動いてくれた。あとは続けるだけ"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "合格、とタクヤは言わなかった。でもその笑顔が、すべてを語っていた。"}
     ], ensure_ascii=False)),

    # A8. After P95: 第6章コラム前のブリッジ
    (95, 'テンプレ3', 'misaki_work_home',
     """1コマ目 (上小): ミサキが手帳を開いている。3ヶ月間の投稿数「87回」と書いてある。 セリフ: なし ナレーション: ［四角枠］3ヶ月で87回の投稿。全部自分の言葉で書いた。 オノマトペ: なし
2コマ目 (下大): ミサキが正面を向いて、静かな自信をたたえた表情でカメラ目線（読者目線）。背景はパソコンのある作業スペース。 セリフ: ［ミサキ（内心）］の吹き出しに「続けることが、私の証明だ」 ナレーション: ［四角枠］誰かに認められなくていい。自分が続けている事実が、答えだった。 オノマトペ: なし""",
     json.dumps([
         {"panel_id": 1, "type": "narration", "speaker": None, "text": "3ヶ月で87回の投稿。全部自分の言葉で書いた。"},
         {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "続けることが、私の証明だ"},
         {"panel_id": 2, "type": "narration", "speaker": None, "text": "誰かに認められなくていい。自分が続けている事実が、答えだった。"}
     ], ensure_ascii=False)),
]

# Build insertions dict
insertions = {}
for (after_page, template, outfit_key, story, json_text) in additional_pages:
    prompt = build_prompt(template, outfit_key, story)
    # Determine outfit_id for CSV column
    if 'kenta' in outfit_key:
        outfit_id = 'kenta_work_casual'
    elif 'takuya' in outfit_key:
        outfit_id = 'takuya_zoom_mentor'
    elif 'casual' in outfit_key:
        outfit_id = 'misaki_casual'
    else:
        outfit_id = 'misaki_work_home'

    new_row = ['PLACEHOLDER', template, prompt, json_text, outfit_id]
    if after_page not in insertions:
        insertions[after_page] = []
    insertions[after_page].append(new_row)

# Insert into data
new_data = []
for row in data:
    page_num = int(row[0])
    new_data.append(row)
    if page_num in insertions:
        for ins_row in insertions[page_num]:
            new_data.append(ins_row)

# Renumber pages
for i, row in enumerate(new_data):
    row[0] = str(i + 1)

# Verify sequential
page_nums = [int(r[0]) for r in new_data]
expected = list(range(1, len(new_data)+1))
assert page_nums == expected, f'Page number gap detected!'

print(f'After adding 8 pages: {len(new_data)} total pages')

# ==================
# STEP 4: Final stats check
# ==================
template_counts = {}
for row in new_data:
    t = row[1]
    template_counts[t] = template_counts.get(t, 0) + 1

image_data = [r for r in new_data if r[1] != 'テキストページ']
image_total = len(image_data)

print(f'Image pages: {image_total}')
print('Template distribution:')
t2_4 = sum(template_counts.get(f'テンプレ{n}', 0) for n in [2,3,4])
t5_7 = sum(template_counts.get(f'テンプレ{n}', 0) for n in [5,6,7])
t1 = template_counts.get('テンプレ1', 0)
for k in ['テンプレ1','テンプレ2','テンプレ3','テンプレ4','テンプレ5','テンプレ6','テンプレ7']:
    cnt = template_counts.get(k, 0)
    pct = cnt/image_total*100
    print(f'  {k}: {cnt} ({pct:.1f}%)')
print(f'  T2-4 total: {t2_4} ({t2_4/image_total*100:.1f}%)')
print(f'  T5-7 total: {t5_7} ({t5_7/image_total*100:.1f}%)')
print(f'  T1 total: {t1} ({t1/image_total*100:.1f}%)')

total_chars = 0
low_count = 0
low_50_count = 0
for row in image_data:
    try:
        panels = json.loads(row[3])
        chars = sum(len(p.get('text','')) for p in panels)
        total_chars += chars
        if chars < 90:
            low_count += 1
        if chars < 50:
            low_50_count += 1
    except:
        pass

avg = total_chars / image_total
print(f'Average chars/page: {avg:.1f}')
print(f'Pages under 90 chars: {low_count}')
print(f'Pages under 50 chars: {low_50_count}')

# ==================
# STEP 5: Write final output
# ==================
with open(OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for row in new_data:
        writer.writerow(row)

print(f'')
print(f'Saved to {OUTPUT}')
print('Done.')
