import sys
sys.stdout.reconfigure(encoding='utf-8')
import csv
import copy

INPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\work_step3.csv'
OUTPUT = r'G:\マイドライブ\YNFactory-cc\.company\outputs\ebooks-manga\manga-career-restart\vol3\panels\work_step4.csv'

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
    'misaki_casual': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
    'kenta_work_casual': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, ケンタは添付のケンタ.pngと100%同一の外見で描画',
    'takuya_zoom_mentor': 'ミサキは添付のミサキ.pngと100%同一の外見で描画, タクヤは添付のタクヤ.pngと100%同一の外見で描画',
}

TEMPLATE_NAMES = {
    'テンプレ1': 'テンプレ1: ページ全体1コマ',
    'テンプレ2': 'テンプレ2: 上下2段',
    'テンプレ3': 'テンプレ3: 上小＋下大',
    'テンプレ4': 'テンプレ4: 上大＋下小',
    'テンプレ5': 'テンプレ5: 上中下3段',
    'テンプレ6': 'テンプレ6: 上1コマ＋下左右2コマ',
    'テンプレ7': 'テンプレ7: 上左右2コマ＋下1コマ',
}

def build_prompt(template, outfit_id, char_override, story_text):
    char_note = char_override if char_override else CHAR_NOTES.get(outfit_id, 'ミサキは添付のミサキ.pngと100%同一の外見で描画')
    outfit_note = OUTFIT_NOTES.get(outfit_id, '')
    tmpl_name = TEMPLATE_NAMES.get(template, template)
    return f"""{COMMON_PREFIX}
◆【絶対最優先】キャラクター外見: {char_note}
{outfit_note}
◆【コマ構成】{tmpl_name}
{STYLE_SUFFIX}
◆【ストーリー】
{story_text}"""

# Define 18 new pages as (after_page_num, template, outfit_id, char_override, story_text, json_text)
new_pages = [
    # 1. After P4: Zoom前準備（昼寝タイムリミット）
    (4, 'テンプレ4', 'misaki_work_home', None,
     """1コマ目 (上大): ミサキがスマートフォンを見て目を見開く。画面には「昼寝タイマー あと3分」と表示されている。焦りと興奮が混じった表情。効果線で緊張感を演出。 セリフ: ［ミサキ（内心）］の吹き出しに「あと3分しかない……！」 ナレーション: ［四角枠］Zoom前夜、ミサキは何度もシミュレーションしていた。 オノマトペ: ドキドキ
2コマ目 (下小): ミサキがノートパソコンを素早く開く。画面がパッと点灯する演出。 セリフ: なし ナレーション: ［四角枠］ひなたが目を覚ます前に、絶対につなぐ。 オノマトペ: カチャッ""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "あと3分しかない……！"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "Zoom前夜、ミサキは何度もシミュレーションしていた。"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "ひなたが目を覚ます前に、絶対につなぐ。"}]'),

    # 2. After P9: Claudeの実演（タクヤが実際に操作）
    (9, 'テンプレ2', 'takuya_zoom_mentor', None,
     """1コマ目 (上): Zoom画面上のタクヤがノートパソコンを傾けてミサキに画面を見せている。「ここに入力するだけです」と指差している。 セリフ: ［タクヤ］の吹き出しに「実際にやってみましょう。ここに〝私は元事務職のママです〟って入れるだけでいい」 ナレーション: ［四角枠］タクヤがClaudeの画面を共有してみせた。 オノマトペ: カタカタカタ
2コマ目 (下): ミサキの目が大きく見開かれる。Zoom画面に映るClaudeの応答テキストを食い入るように見ている。 セリフ: ［ミサキ（内心）］の吹き出しに「一瞬で、こんなに長い文章が……」 ナレーション: なし オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "タクヤ", "text": "実際にやってみましょう。ここに〝私は元事務職のママです〟って入れるだけでいい"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "タクヤがClaudeの画面を共有してみせた。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "一瞬で、こんなに長い文章が……"}]'),

    # 3. After P13: 「良い指示」の衝撃
    (13, 'テンプレ1', 'misaki_work_home', None,
     """1コマ目 (全面): ノートパソコンの画面アップ。Claudeの返答が2つ並んでいる。左側「NG例」は短く的外れな文章。右側「OK例」は具体的で読みやすい文章。ミサキの手が画面を指差している。ナレーションで対比を強調。 セリフ: なし ナレーション: ［四角枠］指示の解像度で、AIの答えはまるで別物になる。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "narration", "speaker": null, "text": "指示の解像度で、AIの答えはまるで別物になる。"}]'),

    # 4. After P21: 「また動き出せること」の重み
    (21, 'テンプレ3', 'takuya_zoom_mentor', None,
     """1コマ目 (上小): タクヤが静かな表情でミサキに話しかける。 セリフ: ［タクヤ］の吹き出しに「完璧じゃなくていい。動き続けることが一番難しいんです」 ナレーション: なし オノマトペ: なし
2コマ目 (下大): ミサキが目に涙をためながらも口角を上げる。「また動き出せている」という実感が顔全体に広がっている。集中線で感情を強調。 セリフ: ［ミサキ（内心）］の吹き出しに「私、ちゃんと動けてる」 ナレーション: ［四角枠］産後、ずっと止まっていた何かが、少しずつ動き始めていた。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "タクヤ", "text": "完璧じゃなくていい。動き続けることが一番難しいんです"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "私、ちゃんと動けてる"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "産後、ずっと止まっていた何かが、少しずつ動き始めていた。"}]'),

    # 5. After P33: AIが3パターン、選ぶのは人間
    (33, 'テンプレ5', 'takuya_zoom_mentor', None,
     """1コマ目 (上段): パソコン画面アップ。Claudeが出した3パターンのSNS投稿文が並んでいる。①②③とナンバリングされた吹き出し風のテキストボックス。 セリフ: なし ナレーション: ［四角枠］Claudeは3パターン出してくれた。 オノマトペ: なし
2コマ目 (中段): ミサキが画面を見ながら顎に手を当てて考えている。 セリフ: ［ミサキ（内心）］の吹き出しに「どれが私らしいんだろう」 ナレーション: なし オノマトペ: うーん
3コマ目 (下段): タクヤがZoom越しに微笑む。 セリフ: ［タクヤ］の吹き出しに「選ぶのは佐藤さんです。AIはアシスタントで、主役はあなた」 ナレーション: なし オノマトペ: なし""",
     '[{"panel_id": 1, "type": "narration", "speaker": null, "text": "Claudeは3パターン出してくれた。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "どれが私らしいんだろう"}, {"panel_id": 3, "type": "dialogue", "speaker": "タクヤ", "text": "選ぶのは佐藤さんです。AIはアシスタントで、主役はあなた"}]'),

    # 6. After P38: 「もしかしたら」が確信に変わりつつある夜
    (38, 'テンプレ2', 'misaki_work_home', None,
     """1コマ目 (上): 夜のリビング。ひなたが寝た後、ミサキがパソコン画面の前でノートを開いている。「今日学んだこと」を書き留めている。ページには〝指示の言葉で結果が変わる〟と書かれている。 セリフ: ［ミサキ（内心）］の吹き出しに「もしかしたら……私にもできるかもしれない」 ナレーション: ［四角枠］第5章 コラム⑥ 前ページへ続く オノマトペ: カリカリ
2コマ目 (下): 窓の外に夜景。ミサキの横顔が画面の光に照らされている。表情は静かな決意。 セリフ: なし ナレーション: ［四角枠］もしかしたら、が確信に変わり始めていた。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "もしかしたら……私にもできるかもしれない"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "第5章 コラム⑥ 前ページへ続く"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "もしかしたら、が確信に変わり始めていた。"}]'),

    # 7. After P42: 投稿後の眠れない夜
    (42, 'テンプレ3', 'misaki_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
     """1コマ目 (上小): ベッドの中でスマートフォンを見るミサキ。画面の光だけが暗い部屋に浮かぶ。横にはひなたが寝ている。 セリフ: ［ミサキ（内心）］の吹き出しに「投稿して……5時間。いいね、ゼロ」 ナレーション: ［四角枠］初投稿から一晩が経っていた。 オノマトペ: なし
2コマ目 (下大): ミサキの顔アップ。笑えているが目は泣きそう。スマホ画面が反射して瞳に映っている。 セリフ: ［ミサキ（内心）］の吹き出しに「恥ずかしいだけだったかな。でも……消す気にはなれない」 ナレーション: ［四角枠］削除ボタンに指が触れて、止まった。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "投稿して……5時間。いいね、ゼロ"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "初投稿から一晩が経っていた。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "恥ずかしいだけだったかな。でも……消す気にはなれない"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "削除ボタンに指が触れて、止まった。"}]'),

    # 8. After P47: ケンタと副業の話
    (47, 'テンプレ6', 'kenta_work_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ケンタは添付のケンタ.pngと100%同一の外見で描画',
     """1コマ目 (上): 夕食後のリビング。ミサキとケンタが向き合って座っている。テーブルにはお茶のカップ。 セリフ: ［ケンタ］の吹き出しに「SNSって毎日投稿してるの？大変じゃない？」 ナレーション: ［四角枠］ケンタに話すのはこれが初めてだった。 オノマトペ: なし
2コマ目 (下左): ミサキが少し照れながら答える。 セリフ: ［ミサキ］の吹き出しに「大変だけど……なんか、楽しいんだよね」 ナレーション: なし オノマトペ: なし
3コマ目 (下右): ケンタが穏やかに笑う。 セリフ: ［ケンタ］の吹き出しに「そっか。応援してるよ」 ナレーション: ［四角枠］たったひと言なのに、胸があたたかくなった。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ケンタ", "text": "SNSって毎日投稿してるの？大変じゃない？"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "ケンタに話すのはこれが初めてだった。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ", "text": "大変だけど……なんか、楽しいんだよね"}, {"panel_id": 3, "type": "dialogue", "speaker": "ケンタ", "text": "そっか。応援してるよ"}, {"panel_id": 3, "type": "narration", "speaker": null, "text": "たったひと言なのに、胸があたたかくなった。"}]'),

    # 9. After P52: 誰にも届いていない孤独感
    (52, 'テンプレ2', 'misaki_work_home', None,
     """1コマ目 (上): ミサキがスマートフォンの画面を見ている。フォロワー数「11」。いいね0が並ぶ投稿一覧。 セリフ: ［ミサキ（内心）］の吹き出しに「13日間、毎日投稿した。フォロワー11人……全員知り合い」 ナレーション: ［四角枠］数字は正直だった。 オノマトペ: なし
2コマ目 (下): ミサキが机に肘をついて俯いている。窓の外は夜。ノートパソコンの画面が白く光っている。 セリフ: ［ミサキ（内心）］の吹き出しに「私の声は、誰にも届いていない」 ナレーション: なし オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "13日間、毎日投稿した。フォロワー11人……全員知り合い"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "数字は正直だった。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "私の声は、誰にも届いていない"}]'),

    # 10. After P54: 「佐藤さんらしさがない」の衝撃
    (54, 'テンプレ1', 'misaki_work_home', None,
     """1コマ目 (全面): ミサキが固まった表情でZoom画面を見ている。タクヤの言葉が頭の中に響いている演出。画面中央にタクヤの言葉がフォント大きめで表示される。集中線で衝撃を表現。 セリフ: ［タクヤ（回想）］の吹き出しに「これ、佐藤さんらしさが全然ないですよ」 ナレーション: ［四角枠］その言葉が、刺さった。 オノマトペ: ドキッ""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "タクヤ（回想）", "text": "これ、佐藤さんらしさが全然ないですよ"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "その言葉が、刺さった。"}]'),

    # 11. After P57: 「私の言葉を見つける」決意の夜
    (57, 'テンプレ3', 'misaki_work_home', None,
     """1コマ目 (上小): 深夜のリビング。ミサキがノートにびっしり書き込んでいる。「自分の言葉」「誰かに届く言葉」「ミサキらしさって何？」 セリフ: なし ナレーション: ［四角枠］夜中の1時、ひなたが寝てから3時間。 オノマトペ: カリカリカリ
2コマ目 (下大): ミサキが顔を上げ、決然とした表情でパソコンのキーボードに手を置く。強い目つき。 セリフ: ［ミサキ（内心）］の吹き出しに「私の言葉を見つける。借り物じゃなく、私だけの言葉を」 ナレーション: ［四角枠］それは宣言だった。誰にも聞こえない、でも確かな宣言。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "narration", "speaker": null, "text": "夜中の1時、ひなたが寝てから3時間。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "私の言葉を見つける。借り物じゃなく、私だけの言葉を"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "それは宣言だった。誰にも聞こえない、でも確かな宣言。"}]'),

    # 12. After P63: 深夜ワンオペの孤独と決意
    (63, 'テンプレ4', 'misaki_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
     """1コマ目 (上大): 暗い寝室。ミサキがひなたの額に濡れタオルを当てている。ひなたは苦しそうに眠っている。デジタル時計が「AM 2:47」を示す。 セリフ: ［ミサキ（内心）］の吹き出しに「ひとりで乗り切る。それしかない」 ナレーション: ［四角枠］ひなたの熱は、まだ下がらなかった。 オノマトペ: なし
2コマ目 (下小): ひなたの小さな手をミサキが両手で包んでいる。温かい手の温度が伝わるような描写。 セリフ: なし ナレーション: ［四角枠］でも、この手を握っていれば、何でもできる気がした。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "ひとりで乗り切る。それしかない"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "ひなたの熱は、まだ下がらなかった。"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "でも、この手を握っていれば、何でもできる気がした。"}]'),

    # 13. After P68: タクヤの最後の問い
    (68, 'テンプレ6', 'takuya_zoom_mentor', None,
     """1コマ目 (上): タクヤがZoom越しに真剣な目でミサキを見る。 セリフ: ［タクヤ］の吹き出しに「最後に聞かせてください。あなたがこれをやめたくない理由は何ですか？」 ナレーション: ［四角枠］その問いはストレートで、ミサキの胸に刺さった。 オノマトペ: なし
2コマ目 (下左): ミサキが黙って考える。目を閉じて、何かを探している表情。 セリフ: なし ナレーション: なし オノマトペ: なし
3コマ目 (下右): ミサキが静かに、でも確かな声で答える。 セリフ: ［ミサキ］の吹き出しに「やめたくない……それだけで、十分な理由になりますか」 ナレーション: ［四角枠］やめたくない、が最強の動機だと、タクヤは言った。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "タクヤ", "text": "最後に聞かせてください。あなたがこれをやめたくない理由は何ですか？"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "その問いはストレートで、ミサキの胸に刺さった。"}, {"panel_id": 3, "type": "dialogue", "speaker": "ミサキ", "text": "やめたくない……それだけで、十分な理由になりますか"}, {"panel_id": 3, "type": "narration", "speaker": null, "text": "やめたくない、が最強の動機だと、タクヤは言った。"}]'),

    # 14. After P70: 再開投稿テーマを決める過程
    (70, 'テンプレ4', 'misaki_work_home', None,
     """1コマ目 (上大): ミサキが大きなノートに箇条書きで投稿テーマを書き出している。「①38.5度でひとりで看病した夜」「②ゼロ反応でも続けた13日間」「③AIに最初に言った言葉」ペンが走る速さが伝わるように。 セリフ: ［ミサキ（内心）］の吹き出しに「リアルな話を書こう。かっこいい話じゃなく」 ナレーション: ［四角枠］「自分の経験」を投稿の源泉にする。それがタクヤのアドバイスだった。 オノマトペ: サラサラ
2コマ目 (下小): ミサキが3番目の項目に丸をつける。 セリフ: なし ナレーション: ［四角枠］これだ、と思った。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "リアルな話を書こう。かっこいい話じゃなく"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "「自分の経験」を投稿の源泉にする。それがタクヤのアドバイスだった。"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "これだ、と思った。"}]'),

    # 15. After P72: コメントを何度も読む
    (72, 'テンプレ2', 'misaki_work_home', None,
     """1コマ目 (上): スマートフォン画面アップ。SNS投稿へのコメント欄。見知らぬアカウントから「私もそうだった」「共感しすぎて泣いた」という文字が見える。 セリフ: なし ナレーション: ［四角枠］見知らぬ誰かの言葉が、画面に並んでいた。 オノマトペ: なし
2コマ目 (下): ミサキがスマホを両手で持ち、画面を何度も上下スクロールしている。目が潤んでいる。 セリフ: ［ミサキ（内心）］の吹き出しに「本当に……届いた」 ナレーション: ［四角枠］何度も、何度も読んだ。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "narration", "speaker": null, "text": "見知らぬ誰かの言葉が、画面に並んでいた。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "本当に……届いた"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "何度も、何度も読んだ。"}]'),

    # 16. After P74: ケンタとひなたとの夕食
    (74, 'テンプレ5', 'kenta_work_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画, ケンタは添付のケンタ.pngと100%同一の外見で描画',
     """1コマ目 (上段): 夕食のテーブル。ケンタとひなたとミサキの3人。ひなたがご飯を食べながら「まーまー！」とミサキを呼んでいる。温かい家族の食卓。 セリフ: ［ひなた］の吹き出しに「まーまー！まんまー！」 ナレーション: ［四角枠］フォロワーが40人を超えた日。 オノマトペ: なし
2コマ目 (中段): ミサキがスマートフォンを取り出してケンタに見せる。画面に「フォロワー数: 43」の数字。 セリフ: ［ミサキ］の吹き出しに「ねえ、フォロワー40人超えたんだけど」 ナレーション: なし オノマトペ: なし
3コマ目 (下段): ケンタが目を丸くして驚く。ひなたはよくわからないままケンタを真似て驚いた顔。 セリフ: ［ケンタ］の吹き出しに「えっ、マジで！すごいじゃん！」 ナレーション: ［四角枠］小さな数字が、今夜は大きく輝いて見えた。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ひなた", "text": "まーまー！まんまー！"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "フォロワーが40人を超えた日。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ", "text": "ねえ、フォロワー40人超えたんだけど"}, {"panel_id": 3, "type": "dialogue", "speaker": "ケンタ", "text": "えっ、マジで！すごいじゃん！"}, {"panel_id": 3, "type": "narration", "speaker": null, "text": "小さな数字が、今夜は大きく輝いて見えた。"}]'),

    # 17. After P77: 面談前夜の自問自答
    (77, 'テンプレ3', 'misaki_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
     """1コマ目 (上小): 夜のリビング。ひなたが寝た後、ミサキがソファで膝を抱えている。スマートフォンを持っているが画面は暗い。 セリフ: ［ミサキ（内心）］の吹き出しに「明日の面談……何を話せばいいんだろう」 ナレーション: ［四角枠］進捗報告の日が明日に迫っていた。 オノマトペ: なし
2コマ目 (下大): ミサキが顔を上げて窓の外を見る。夜の街が見える。目に強い光が宿っている。 セリフ: ［ミサキ（内心）］の吹き出しに「失敗じゃない。続けてきた。それが私の報告だ」 ナレーション: ［四角枠］どんな数字を持っていくより、正直に話すことを選んだ。 オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "明日の面談……何を話せばいいんだろう"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "進捗報告の日が明日に迫っていた。"}, {"panel_id": 2, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "失敗じゃない。続けてきた。それが私の報告だ"}, {"panel_id": 2, "type": "narration", "speaker": null, "text": "どんな数字を持っていくより、正直に話すことを選んだ。"}]'),

    # 18. After P81: 第6章の締め大ゴマ
    (81, 'テンプレ1', 'misaki_casual',
     'ミサキは添付のミサキ.pngと100%同一の外見で描画, ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画',
     """1コマ目 (全面): 昼間の公園。ミサキがひなたを抱っこしながら、空を見上げている。ひなたはミサキの肩にもたれて眠っている。青空にはふわりとした雲。ミサキの顔には穏やかな笑顔。集中線で光と希望を演出。 セリフ: ［ミサキ（内心）］の吹き出しに「続けた。それだけで、十分だった」 ナレーション: ［四角枠］第6章　終わり オノマトペ: なし""",
     '[{"panel_id": 1, "type": "dialogue", "speaker": "ミサキ（内心）", "text": "続けた。それだけで、十分だった"}, {"panel_id": 1, "type": "narration", "speaker": null, "text": "第6章　終わり"}]'),
]

# Read existing CSV
rows = []
with open(INPUT, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

header = rows[0]
data = rows[1:]  # 84 data rows, page nums 1-84

# Build a dict: page_num -> list of rows to insert AFTER that page
insertions = {}
for (after_page, template, outfit_id, char_override, story, json_text) in new_pages:
    prompt = build_prompt(template, outfit_id, char_override, story)
    new_row = ['PLACEHOLDER', template, prompt, json_text, outfit_id]
    if after_page not in insertions:
        insertions[after_page] = []
    insertions[after_page].append(new_row)

# Build new data list with insertions
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

print(f'Original pages: {len(data)}')
print(f'New pages: {len(new_data)}')
print(f'Insertions made: {len(new_pages)}')

# Verify no gaps in page numbers
page_nums = [int(r[0]) for r in new_data]
expected = list(range(1, len(new_data)+1))
assert page_nums == expected, f'Page number gap detected! {page_nums[:10]}'

# Write output
with open(OUTPUT, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(header)
    for row in new_data:
        writer.writerow(row)

print(f'Saved to {OUTPUT}')
print('All page numbers sequential: OK')
