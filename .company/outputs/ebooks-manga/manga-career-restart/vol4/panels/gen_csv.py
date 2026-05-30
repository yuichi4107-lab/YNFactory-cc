import csv
import json
import sys

# === outfit_presets ===
OUTFIT_PRESETS = {
    "misaki_casual": "ボーダー柄（白と紺）のカットソーにデニムパンツ、白いスニーカー（自宅・外出・育児中の普段着）",
    "misaki_work_home": "グレーのスウェット上下、髪を緩くまとめ、素足（深夜〜早朝のPC作業・在宅集中タイム）",
    "misaki_formal": "紺のジャケットに白ブラウス、黒いスラックス、パンプス（OL時代・退職日・過去回想シーン）",
    "takuya_zoom_mentor": "白い無地のTシャツ、自室の白い壁を背景（Zoom・ウェビナー画面越しの指導シーン）",
    "takuya_casual": "薄いグレーのカジュアルシャツにチノパン、黒い革靴（対面・外出時の普段着）",
    "kenta_work_casual": "白い無地のシャツにベージュのチノパン、茶色の革靴（仕事帰り・夜の帰宅シーン）",
    "kenta_casual": "ネイビーのカジュアルシャツにグレーのスラックス、スニーカー（休日自宅・早帰り・家族の時間）",
    "yamada_suit": "紺色のスーツに白いYシャツ、紺ストライプネクタイ（OL時代の上司として過去回想シーンに登場）",
}

COMMON_HEADER = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画、ケンタは添付のケンタ.pngと100%同一の外見で描画、ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画、タクヤは添付のタクヤ.pngと100%同一の外見で描画
◆【出力サイズ】画像は縦長（高さ:幅＝1:1.4）で生成してください
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現
◆【演出】パソコン作業,スマホ,収入の可視化,必要に応じて集中線,効果線,擬音などのマンガらしい演出"""

CHARACTER_PAGE_HEADER = """◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください
◆【絶対最優先】必ずフルカラーにしてください
◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。
◆【絶対最優先】キャラクター外見: ミサキは添付のミサキ.pngと100%同一の外見で描画、ケンタは添付のケンタ.pngと100%同一の外見で描画、ひなた（2歳期）は添付のひなた_2歳期.pngと100%同一の外見で描画、タクヤは添付のタクヤ.pngと100%同一の外見で描画
◆【出力サイズ】2:3
◆【補足情報】上下左右に50ピクセルの余白を設けてください
◆【作画】ジャンル: 副業に最適化した統一スタイル / 作画スタイル: 親しみやすく実践的,現代的なライフスタイル表現 / 色調: 明るく前向きな色調,オレンジ・青・黄色基調,活力ある配色 / 線画: 親しみやすい柔らかな線,カジュアルで読みやすい表現
◆【補足情報】演出: キャラクター紹介ページ"""


def outfit_block(outfit_id):
    desc = OUTFIT_PRESETS.get(outfit_id, "")
    char_map = {
        "misaki_casual": "ミサキ",
        "misaki_work_home": "ミサキ",
        "misaki_formal": "ミサキ",
        "takuya_zoom_mentor": "タクヤ",
        "takuya_casual": "タクヤ",
        "kenta_work_casual": "ケンタ",
        "kenta_casual": "ケンタ",
        "yamada_suit": "山田課長",
    }
    char = char_map.get(outfit_id, "")
    return f"◆【補足情報】服装: {char}の服装 — {desc}"


def manga_prompt(template_name, template_desc, story_text, costume_block, extra=""):
    lines = [COMMON_HEADER]
    if extra:
        lines.append(extra)
    lines.append(f"◆【コマ構成】{template_name}: {template_desc}")
    lines.append(costume_block)
    lines.append(f"◆【ストーリー】\n{story_text}")
    return "\n".join(lines)


def panels_json(*panels):
    result = []
    for pid, ptype, speaker, text in panels:
        result.append({"panel_id": pid, "type": ptype, "speaker": speaker, "text": text})
    return json.dumps(result, ensure_ascii=False)


rows = []  # (page, template, prompt, panels_json, outfit_id)

# ---- P1: 目次 ----
rows.append((
    1,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【目次】\n出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第4巻\n\n【目次】\n\n　第8話　フォロワー100人の夜\n　　コラム⑧\n　第9話　1,280円の重み\n　　コラム⑨\n　第10話　私のキャリアは、私が決める\n　　コラム⑩\n　著者紹介\n　奥付",
    "[]",
    ""
))

# ---- P2: 前巻あらすじ ----
rows.append((
    2,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【前巻までのあらすじ】\n【前巻（第1〜3巻）までのあらすじ】\n\n佐藤ミサキ（32歳）は出産を機に退職後、メンターのタクヤに出会い、AIツールClaudeを使い始めた。Instagramで育児×キャリアの発信を始め、フォロワー70人まで成長。さらに成長を続けるミサキの前に、新しい挑戦が待っていた——。",
    "[]",
    ""
))

# ---- P3: 登場人物紹介 ----
rows.append((
    3,
    "テンプレ5",
    CHARACTER_PAGE_HEADER + "\n◆【コマ構成】テンプレ5: 上・中・下3段\n" + outfit_block("misaki_casual") + "\n◆【ストーリー】\n1コマ目(上段): ミサキとひなたのイラスト。 ナレーション: ミサキ 32歳 主人公 / ひなた 2歳 ミサキの娘\n2コマ目(中段): ケンタのイラスト。 ナレーション: ケンタ 34歳 ミサキの夫\n3コマ目(下段): タクヤのイラスト。 ナレーション: タクヤ 42歳 メンター",
    panels_json(
        (1, "narration", None, "ミサキ 32歳 主人公"),
        (2, "narration", None, "ひなた 2歳 ミサキの娘"),
        (3, "narration", None, "ケンタ 34歳 ミサキの夫"),
        (4, "narration", None, "タクヤ 42歳 メンター"),
    ),
    "misaki_casual"
))

# ===== 第8話: フォロワー100人の夜 =====

# P4: 扉絵
rows.append((
    4,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "夜の静かな部屋。ミサキがスマホを見つめている。集中線演出。",
        outfit_block("misaki_work_home")),
    panels_json((1, "narration", None, "第8話「フォロワー100人の夜」")),
    "misaki_work_home"
))

# P5: 2ヶ月フォロワー停滞
rows.append((
    5,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): カレンダー2ヶ月分にバツ印が並んでいる。\n2コマ目(中段): スマホ画面にフォロワー70人と表示されている。\n3コマ目(下段): ミサキがソファに座り考え込んでいる。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "投稿を続けて2ヶ月——毎日続けた。"),
        (2, "narration", None, "フォロワー70人——数字が伸び悩んでいた。"),
        (3, "monologue", None, "何かが足りない——でも何が足りないか分からない。"),
    ),
    "misaki_casual"
))

# P6: スマホで悩むミサキ
rows.append((
    6,
    "テンプレ4",
    manga_prompt("テンプレ4", "2コマ（左・右）",
        "1コマ目(左): ミサキが暗い表情でスマホを見ている。\n2コマ目(右): スマホのフォロワー数画面のアップ。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "monologue", None, "毎日投稿してきた——それでもこの数字。"),
        (2, "monologue", None, "このまま続けても意味があるのか——"),
    ),
    "misaki_casual"
))

# P7: Claude分析依頼
rows.append((
    7,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがパソコンを開いている。\n2コマ目(中段): Claudeのチャット画面。\n3コマ目(下段): ミサキが2ヶ月分の投稿データを入力している。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "ミサキはClaudeに分析を依頼することにした。"),
        (2, "narration", None, "2ヶ月分の投稿データを全部入力した。"),
        (3, "narration", None, "エンゲージメント率、保存数、コメント数——"),
    ),
    "misaki_work_home"
))

# P8: 分析結果
rows.append((
    8,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): Claudeが分析中の画面。\n2コマ目(下段大): 分析結果が表示される。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "Claudeが全データを丁寧に分析していく。"),
        (2, "narration", None, "失敗体験を正直に書いた投稿が上位を占めていた。"),
    ),
    "misaki_work_home"
))

# P9: 衝撃の気づき
rows.append((
    9,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが目を見開いている。\n2コマ目(中段): 分析グラフ——感情が正直な投稿が高反応。\n3コマ目(下段): ミサキが考え込んでいる。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "感情が剥き出しで書かれた投稿——それが最も高い反応。"),
        (2, "monologue", None, "私が一番隠してきた部分が——一番求められていた。"),
        (3, "monologue", None, "恥ずかしいことを書くのが正解なのか。"),
    ),
    "misaki_work_home"
))

# P10: 方向転換の決意
rows.append((
    10,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが投稿スケジュールを書き直している。\n2コマ目(中段): 育児ハックを週1に減らす計画が見える。\n3コマ目(下段): 実体験ベースのテーマ一覧を書き出している。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "育児ハック投稿は週1に減らすことにした。"),
        (2, "narration", None, "代わりに実体験ベースの投稿を増やす——"),
        (3, "narration", None, "「恥ずかしくても書く」がルールになった。"),
    ),
    "misaki_work_home"
))

# P11: ひなた離乳食ぶちまけエピソード
rows.append((
    11,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ひなたが離乳食をぶちまけている場面。\n2コマ目(中段): ミサキが5秒間完全に無の顔で座っている。\n3コマ目(下段): ミサキがスマホで投稿文を書いている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ひなたが離乳食をぶちまけた。テーブルも床も全部。"),
        (2, "narration", None, "5秒間だけ、完全に無になった。"),
        (3, "narration", None, "その話もそのまま書いた——全部正直に。"),
    ),
    "misaki_casual"
))

# P12: 「大丈夫?」と聞かれた夜
rows.append((
    12,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキとケンタが夜の食卓に座っている。\n2コマ目(中段): ケンタが心配そうにミサキを見ている。\n3コマ目(下段): ミサキが「大丈夫」と答えた夜の回想。",
        outfit_block("kenta_work_casual")),
    panels_json(
        (1, "dialogue", "ケンタ", "大丈夫？最近疲れてるんじゃない？"),
        (2, "narration", None, "大丈夫——そう答えた。でも全然大丈夫じゃなかった。"),
        (3, "narration", None, "その正直な気持ちを、投稿に書いた。"),
    ),
    "kenta_work_casual"
))

# P13: 名刺がなくなった日の投稿
rows.append((
    13,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがパソコンで考えている。夜のシーン。\n2コマ目(中段): 段ボールを抱えてビルを出るミサキの記憶が浮かぶ（回想）。\n3コマ目(下段): ミサキが投稿文を真剣に書いている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "ある夜、テーマが浮かんだ——名刺がなくなった日。"),
        (2, "narration", None, "退職した日。段ボール一つに5年分を詰めた。"),
        (3, "narration", None, "何者でもない自分に怯えた——そう書いて投稿した。"),
    ),
    "misaki_work_home"
))

# P14: 投稿後の夜——眠れない
rows.append((
    14,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが投稿後スマホを置いている。\n2コマ目(中段): 夜の部屋で布団に入っているミサキ。\n3コマ目(下段): 眠れないまま天井を見つめている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "投稿して——後悔が来た。"),
        (2, "monologue", None, "こんな投稿、恥ずかしかったんじゃないか——"),
        (3, "monologue", None, "朝が怖くて、でも朝が来るのを待っていた。"),
    ),
    "misaki_casual"
))

# P15: 翌朝・通知が止まらない
rows.append((
    15,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "スマホ画面に通知が溢れている演出。数十件の通知バッジ。ミサキが固まっている。集中線。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "翌朝——スマホを見た瞬間、息が止まった。")),
    "misaki_casual"
))

# P16: バズの実感
rows.append((
    16,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが目を見開いてスマホを見ている。\n2コマ目(中段): スマホ画面にいいね200超の数字。\n3コマ目(下段): コメント欄に次々と書き込まれている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "いいね200超——コメント20件以上——"),
        (2, "narration", None, "リポストもされている——夢を見ているみたいだった。"),
        (3, "narration", None, "「泣きました」「今辞めるか迷ってる」——"),
    ),
    "misaki_casual"
))

# P17: コメントが刺さる
rows.append((
    17,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): コメント欄のアップ。\n2コマ目(中段): 別のコメントのアップ。\n3コマ目(下段): ミサキが涙をこらえながらスマホを読んでいる。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "「名刺がない自分に慣れるのに2年かかった」"),
        (2, "narration", None, "「今まさに辞めるか迷ってる。保存した」"),
        (3, "narration", None, "知らない誰かの痛みが、ミサキの痛みと重なった。"),
    ),
    "misaki_casual"
))

# P18: 感動のコマ
rows.append((
    18,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキが涙をこらえながら画面を見ている。涙の滴が頬を伝う。暖かな光の演出。",
        outfit_block("misaki_casual")),
    panels_json((1, "monologue", None, "私の言葉が、誰かの心に届いている——")),
    "misaki_casual"
))

# P19: フォロワー急増
rows.append((
    19,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): フォロワーカウンターが増えていく演出。グラフが急上昇。\n2コマ目(中段): スマホの数字がどんどん増えていく。\n3コマ目(下段): ミサキが固まって画面を見ている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "小バズをきっかけにフォロワーが急増した——"),
        (2, "narration", None, "70人から——80人、90人——"),
        (3, "narration", None, "そして——フォロワー100人。"),
    ),
    "misaki_casual"
))

# P20: フォロワー100達成の瞬間
rows.append((
    20,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "スマホ画面に大きく「フォロワー100」という数字。ミサキが完全に固まっている。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "フォロワー100人——本物の100人だ。")),
    "misaki_casual"
))

# P21: 100人という重さ
rows.append((
    21,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがスマホを持ったまま動けない。\n2コマ目(中段): 100人の人々が各自の生活をしているイメージ。\n3コマ目(下段): ミサキの手が震えている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "monologue", None, "ゼロから積み上げた100人——"),
        (2, "narration", None, "一人一人が実在する人間だ。"),
        (3, "narration", None, "その事実が重くて、しばらく動けなかった。"),
    ),
    "misaki_casual"
))

# P22: タクヤに報告
rows.append((
    22,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが震える手でタクヤにメッセージを送っている。\n2コマ目(中段): タクヤが嬉しそうに返信している。\n3コマ目(下段): タクヤの言葉が画面に映っている。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "narration", None, "ミサキは震える手でタクヤに報告した。"),
        (2, "dialogue", "タクヤ", "最初の100人が一番大変なんですよ。"),
        (3, "dialogue", "タクヤ", "おめでとうございます——"),
    ),
    "takuya_zoom_mentor"
))

# P23: タクヤの言葉が届く
rows.append((
    23,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): タクヤのメッセージのアップ。\n2コマ目(下段大): ミサキが目を潤ませてスマホを見ている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "おめでとうという言葉を——"),
        (2, "narration", None, "こんなに大切に受け取ったのは久しぶりだった。"),
    ),
    "misaki_casual"
))

# P24: 夜のDM
rows.append((
    24,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): 夜、ひなたが寝ている横でミサキがスマホを見ている。\n2コマ目(中段): DMの着信通知が表示されている。\n3コマ目(下段): ミサキがDMを読んでいる。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "夜、DMが届いた。同じ境遇のママからだった。"),
        (2, "dialogue", None, "ミサキさんの投稿に救われました。"),
        (3, "dialogue", None, "一人じゃないんだって思えて——"),
    ),
    "misaki_casual"
))

# P25: 感動・退職後初の実感
rows.append((
    25,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが涙を拭いながら微笑んでいる。\n2コマ目(中段): 暖かな光が広がる演出。\n3コマ目(下段): ミサキが前を向いている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "monologue", None, "私の経験が、誰かの役に立ってる——"),
        (2, "narration", None, "発信を続けてきて、本当に良かった——"),
        (3, "monologue", None, "退職以来初めて感じた——自分が誰かの力になれてる実感。"),
    ),
    "misaki_casual"
))

# P26: ケンタに見せる
rows.append((
    26,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがケンタにスマホを見せている。\n2コマ目(中段): ケンタが驚いた表情でスマホを見ている。\n3コマ目(下段): 二人が久しぶりに笑い合っている。",
        outfit_block("kenta_work_casual")),
    panels_json(
        (1, "narration", None, "ケンタにDMを見せた。"),
        (2, "dialogue", "ケンタ", "すごいじゃん——本当に？どんな人から？"),
        (3, "dialogue", "ミサキ", "同じ境遇のママから。久しぶりに笑えた。"),
    ),
    "kenta_work_casual"
))

# P27: 次へ・ケンタの応援
rows.append((
    27,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキが決意している。\n2コマ目(下段大): ケンタが静かに頷いている。",
        outfit_block("kenta_work_casual")),
    panels_json(
        (1, "dialogue", "ミサキ", "もっとやりたい。もっと届けたい。"),
        (2, "dialogue", "ケンタ", "うん。やれば——"),
    ),
    "kenta_work_casual"
))

# P28: コラム⑧テキスト(1)
rows.append((
    28,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【コラム原文】\nコラム⑧：承認と自己効力感の回復\n——キャリアコンサルタントの視点から\n\nフォロワー100人。\n\n数字だけ見れば小さい。でもミサキにとっては、退職以来初めての「外からの承認」でした。\n\n■自己効力感とは\n\n「自分はやればできる」という感覚のことを、心理学では自己効力感と呼びます。退職後のミサキは、この感覚をすっかり失っていました。\n\n■会社に依存しない承認\n\n会社員のとき、承認は上司から来るものでした。「よくやった」「昇進」「昇給」——全部会社経由。でも今、ミサキが得た承認は、見ず知らずの100人から直接届いた言葉です。\n\n小さな成功体験の積み重ねが、自信を作る。ミサキはその入り口に立ちました。",
    "[]",
    ""
))

# P29: コラム⑧テキスト(2)
rows.append((
    29,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【コラム原文】\n■小さな成功体験の積み重ねが自信を作る\n\n「フォロワー100人」は小さな数字です。でも、ゼロから積み上げた100人は、どんな評価より重い。\n\n■発信を続けることがキャリアの再構築\n\nキャリアの再構築は、大きな転換より小さな成功の連鎖で起きます。「できた」という実感が、次の「やってみよう」を生む。ミサキは今、そのループの中にいます。\n\n「完璧じゃなくていい」「止めないことが最強の戦略」——ミサキが実証した通り、育児中のキャリア再構築に「毎日完璧にやること」は必要ない。細く長く、止めないこと。それだけで十分だと、ミサキは証明しています。",
    "[]",
    ""
))

# ===== 第9話: 1,280円の重み =====

# P30: 第9話扉
rows.append((
    30,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "朝の台所。ミサキがひなたに朝ごはんを食べさせている。穏やかな日常。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "第9話「1,280円の重み」")),
    "misaki_casual"
))

# P31: フォロワー200人超
rows.append((
    31,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): スマホ画面にフォロワー200人超が表示されている。\n2コマ目(中段): ミサキが嬉しそうにしている。\n3コマ目(下段): タクヤとのビデオ通話が始まる。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "フォロワーが200人を超えた。"),
        (2, "narration", None, "続けていれば増えていく——そのことが分かってきた。"),
        (3, "dialogue", "タクヤ", "収益化の話をしましょう"),
    ),
    "misaki_casual"
))

# P32: タクヤがアフィリエイト説明
rows.append((
    32,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): タクヤが真剣な表情で話している。\n2コマ目(中段): ミサキが真剣に聞いている。\n3コマ目(下段): アフィリエイトの仕組みが図解されている。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "dialogue", "タクヤ", "アフィリエイトです——"),
        (2, "narration", None, "自分が本当に良いと思うものだけを紹介する。"),
        (3, "narration", None, "紹介して購入されたら報酬を受け取る仕組みだ。"),
    ),
    "takuya_zoom_mentor"
))

# P33: ミサキの商品リスト
rows.append((
    33,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが手帳に商品候補を書き出している。\n2コマ目(中段): 電動鼻吸い器、ベビーモニター、抱っこ紐のリスト。\n3コマ目(下段): タクヤが頷いている。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "narration", None, "電動鼻吸い器、ベビーモニター、抱っこ紐——"),
        (2, "narration", None, "そしてClaude——本当に使って良かったものだけ。"),
        (3, "dialogue", "タクヤ", "それが一番大事です。嘘のない紹介だから届く。"),
    ),
    "takuya_zoom_mentor"
))

# P34: 紹介商品選び
rows.append((
    34,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがClaudeと一緒にASP登録している画面。\n2コマ目(中段): 商品リンクの自然な入れ方を考えている。\n3コマ目(下段): ミサキが実体験ベースの紹介文を作っている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "Claudeと一緒にASP登録、商品選定を進めた。"),
        (2, "narration", None, "リンクの自然な入れ方も一緒に構築した。"),
        (3, "monologue", None, "本当に使って良かったものだけ、正直に書く。"),
    ),
    "misaki_work_home"
))

# P35: 紹介文の工夫
rows.append((
    35,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキがパソコンで文章を書いている。\n2コマ目(下段大): 画面に実体験の紹介文が表示されている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "実体験ベースの紹介文を作った——嘘がない。"),
        (2, "narration", None, "「5,000円は高い。でも夜中の鼻水バトルが3分で終わる」"),
    ),
    "misaki_work_home"
))

# P36: 1週目〜3週目成約ゼロ
rows.append((
    36,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): 1週間経過——クリック3、成約0のグラフ。\n2コマ目(中段): 2週間経過——クリック11、成約0。\n3コマ目(下段): ミサキが不安そうにしている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "1週間。クリック3、成約0。"),
        (2, "narration", None, "2週間。クリック11、成約0。"),
        (3, "monologue", None, "3週間目、フォロワー300人超——でも成約がない。"),
    ),
    "misaki_casual"
))

# P37: 4週目の朝・振込通知
rows.append((
    37,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ひなたに朝ごはんを食べさせているミサキ。\n2コマ目(下段大): 突然スマホから「お振込がありました」の通知。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "4週間目のある朝——ひなたに朝ごはんを食べさせているとき"),
        (2, "narration", None, "銀行アプリから通知。「お振込がありました」"),
    ),
    "misaki_casual"
))

# P38: 1,280円
rows.append((
    38,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "銀行アプリの振込画面——「1,280円」の数字が大きく映っている。集中線。ミサキの手が震えている。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "振込額：1,280円。千二百八十円。")),
    "misaki_casual"
))

# P39: 震える手
rows.append((
    39,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキの手が震えている。\n2コマ目(中段): ミサキがテーブルに突っ伏している。\n3コマ目(下段): ひなたがミサキを心配そうに見ている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ランチ一回分にも満たない。でもミサキの手は震えた。"),
        (2, "narration", None, "会社以外から、初めて得たお金だった。"),
        (3, "narration", None, "テーブルに突っ伏して泣いた。"),
    ),
    "misaki_casual"
))

# P40: タクヤに報告
rows.append((
    40,
    "テンプレ4",
    manga_prompt("テンプレ4", "2コマ（左・右）",
        "1コマ目(左): タクヤのZoom画面。タクヤが嬉しそうに聞いている。\n2コマ目(右): ミサキが報告している。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "dialogue", "タクヤ", "おめでとうございます。これがスタートラインです"),
        (2, "dialogue", "ミサキ", "タクヤさんの初めての振込はいくらでしたか？"),
    ),
    "takuya_zoom_mentor"
))

# P41: タクヤの初収益
rows.append((
    41,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): タクヤが答えている。\n2コマ目(下段大): ミサキが驚いている。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "dialogue", "タクヤ", "320円でした"),
        (2, "dialogue", "ミサキ", "320円！"),
    ),
    "takuya_zoom_mentor"
))

# P42: ひなたに報告
rows.append((
    42,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがひなたを抱き上げている。\n2コマ目(中段): ひなたが笑っている。\n3コマ目(下段): ミサキが嬉しそうに話しかけている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ひなたを抱き上げた。"),
        (2, "dialogue", "ミサキ", "ひなた、ママね、やったよ。ちょーっとだけ稼いだんだよ"),
        (3, "narration", None, "ひなたはミサキの笑顔を見て笑った。"),
    ),
    "misaki_casual"
))

# P43: 通帳の意味の変化
rows.append((
    43,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキが夜に通帳を見ている。\n2コマ目(下段大): ミサキが静かに微笑んでいる。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "以前は「減っていく通帳」だった——"),
        (2, "narration", None, "今は「増やしていく通帳」だ。変わったのはミサキ自身。"),
    ),
    "misaki_casual"
))

# P44: ケンタに見せる
rows.append((
    44,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがケンタに通帳を見せている。\n2コマ目(中段): ケンタが驚いた表情で通帳を見ている。\n3コマ目(下段): ケンタが笑って応援している。",
        outfit_block("kenta_work_casual")),
    panels_json(
        (1, "dialogue", "ミサキ", "ケンタ、見て。初めて振り込まれたの"),
        (2, "dialogue", "ケンタ", "1,280円……すごいじゃん。本物だ。"),
        (3, "dialogue", "ケンタ", "ずっと頑張ってたもんな——よかった"),
    ),
    "kenta_work_casual"
))

# P44b: ケンタとの回想——応援してたよ
rows.append((
    45,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ケンタが笑いながら言っている。\n2コマ目(下段大): ミサキが目を潤ませている。",
        outfit_block("kenta_work_casual")),
    panels_json(
        (1, "dialogue", "ケンタ", "ずっと応援してたんだよ——言えなかったけど"),
        (2, "narration", None, "その言葉が、ミサキの胸に深く刺さった。"),
    ),
    "kenta_work_casual"
))

# P45: 夜の静けさ
rows.append((
    46,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキとケンタが並んで夜の窓の外を見ている。\n2コマ目(下段大): 穏やかな夜の空気。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "夜が、静かに更けていく。"),
        (2, "narration", None, "1,280円は終わりじゃない——ここからが始まりだ。"),
    ),
    "misaki_casual"
))

# P46: コラム⑨
rows.append((
    47,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【コラム原文】\nコラム⑨：「雇われる」以外の選択肢\n——キャリアコンサルタントの視点から\n\n1,280円。\n\nこの金額に、ミサキは泣きました。\n\nキャリアコンサルタントとして多くの方の転機に立ち会ってきましたが、「初めて自分で稼いだ瞬間」ほど感動的な場面はありません。そしてその金額は、たいてい驚くほど小さい。\n\n■フリーランス・個人事業主は約462万人\n\nフリーランス・個人事業主の数は約462万人。派遣労働者の3倍以上です。「雇われない働き方」はもう少数派ではない。フリーランス保護法が施行されたのは2024年11月。制度のほうが現実に追いついていなかっただけです。\n\n■自分で選択肢を作る時代\n\n「会社が私の席を用意してくれなかったのは、不幸なことだと思っていた」——ミサキが後にそう言いました。「でも今は思う。あの日退職届を出したから、私は自分の席を見つけられた」。\n\n自分で選択肢を作る時代。大事なのは、自分の可能性を自分で決めつけないこと——。",
    "[]",
    ""
))

# ===== 第10話: 私のキャリアは、私が決める =====

# P47: 第10話扉
rows.append((
    48,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキが窓の外を見ている。穏やかな表情。夕暮れの暖かい光。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "第10話「私のキャリアは、私が決める」")),
    "misaki_casual"
))

# P48: ひなた2歳・日常
rows.append((
    49,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ひなたが「ジュース！」と言っている。\n2コマ目(中段): ミサキがひなたにジュースを渡している。\n3コマ目(下段): 二人が笑っている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "初収益から数ヶ月。ひなたは2歳になった。"),
        (2, "dialogue", "ひなた", "ジュース！"),
        (3, "narration", None, "言葉が増えた。毎日が少し賑やかになった。"),
    ),
    "misaki_casual"
))

# P49: フォロワー成長・収益安定
rows.append((
    50,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): スマホにフォロワー800人超の表示。\n2コマ目(中段): 月収2〜3万円のグラフ。\n3コマ目(下段): ミサキが穏やかな顔でパソコンに向かっている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "フォロワー800人超。月の収益は安定して2〜3万円。"),
        (2, "narration", None, "金額はまだ大きくない——でもゼロから積み上げた。"),
        (3, "monologue", None, "これは全部、自分の手で作ったものだ。"),
    ),
    "misaki_work_home"
))

# P50: 退職日を思い出す
rows.append((
    51,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがClaudeと来月の投稿計画を立てているパソコン画面。\n2コマ目(中段): ミサキの手が止まった。\n3コマ目(下段): 回想が始まる演出——退職日の記憶。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "ある晩、Claudeと来月の投稿計画を立てていると——"),
        (2, "monologue", None, "ふと、手が止まった。"),
        (3, "narration", None, "退職届を出した日を思い出す。"),
    ),
    "misaki_work_home"
))

# P51: 回想——退職日
rows.append((
    52,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): 回想（過去）。ミサキが退職届を提出している。紺スーツ姿。\n2コマ目(中段): 段ボールを抱えてビルを出る日。\n3コマ目(下段): 一人でバスに乗って帰る後ろ姿。",
        outfit_block("misaki_formal")),
    panels_json(
        (1, "narration", None, "退職届を出した日を思い出す。"),
        (2, "narration", None, "段ボールを抱えてビルを出た日——"),
        (3, "narration", None, "あの日から、どれくらい歩いただろう。"),
    ),
    "misaki_formal"
))

# P52: 名刺がなくなった
rows.append((
    53,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): あの日のミサキが空っぽの表情で座っている（回想）。\n2コマ目(下段大): 名刺が手の中にない場面。",
        outfit_block("misaki_formal")),
    panels_json(
        (1, "narration", None, "名刺がなくなったとき、怖かった。"),
        (2, "narration", None, "何者でもない自分が怖くて仕方なかった。"),
    ),
    "misaki_formal"
))

# P53: 現在に戻る
rows.append((
    54,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "窓ガラスにミサキの顔が映っている。名刺も肩書きもない。でも揺るぎない表情。",
        outfit_block("misaki_work_home")),
    panels_json((1, "monologue", None, "名刺はない。でも自分が何をしているか——分かっている。")),
    "misaki_work_home"
))

# P54: ゆかりさんと公園
rows.append((
    55,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキとゆかりさんが公園のベンチで話している。\n2コマ目(中段): ゆかりさんが驚いた表情。\n3コマ目(下段): ミサキが答えている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "dialogue", "ゆかりさん", "ミサキちゃん、最近何やってるの？"),
        (2, "dialogue", "ミサキ", "Instagramで育児のこと発信してて。AIも使ってるの"),
        (3, "dialogue", "ゆかりさん", "えー！すごい！フォロワー何人？"),
    ),
    "misaki_casual"
))

# P55: 800人のやりとり
rows.append((
    56,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが答えている。\n2コマ目(中段): ゆかりさんが目を丸くしている。\n3コマ目(下段): ゆかりさんが続けて言っている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "dialogue", "ミサキ", "800人くらい"),
        (2, "dialogue", "ゆかりさん", "800人！？私47人だよ！？"),
        (3, "dialogue", "ゆかりさん", "事務やってたから資料まとめるの上手そうだもんね"),
    ),
    "misaki_casual"
))

# P56: 「事務しかできない」→「役に立ってる」
rows.append((
    57,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキが自然な笑顔で答えている。\n2コマ目(下段大): ミサキが軽やかな足取りで歩いている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "dialogue", "ミサキ", "うん、事務の経験、めちゃくちゃ役に立ってるよ"),
        (2, "narration", None, "半年前なら傷ついた言葉——今は自然に言えた。"),
    ),
    "misaki_casual"
))

# P57: 公園からの帰り道
rows.append((
    58,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがひなたの手を引いて公園から帰っている。\n2コマ目(中段): ひなたが落ち葉を拾っている。\n3コマ目(下段): ミサキが穏やかに空を見上げている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ひなたの手はいつの間にかしっかりした。"),
        (2, "narration", None, "ゆっくり、でも確実に、二人で歩いてきた。"),
        (3, "monologue", None, "この道のりが——私のキャリアだったんだ。"),
    ),
    "misaki_casual"
))

# P58: ひなたとミサキの会話
rows.append((
    59,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ひなたがミサキに「おかあさん、なにしてるの？」と聞いている。\n2コマ目(中段): ミサキが笑顔で答えている。\n3コマ目(下段): ひなたが満足そうに頷いている。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "dialogue", "ひなた", "おかあさん、なにしてるの？"),
        (2, "dialogue", "ミサキ", "お仕事——ひなたのためのお仕事だよ"),
        (3, "narration", None, "ひなたは「ふーん」と頷いて、また遊びに戻った。"),
    ),
    "misaki_casual"
))

# P59: ミサキが画面を閉じる
rows.append((
    60,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキがパソコンの画面をそっと閉じている。\n2コマ目(下段大): 夜の静かな部屋。柔らかな光。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "今夜の分の仕事が終わった。"),
        (2, "narration", None, "また明日——その言葉が、今は怖くない。"),
    ),
    "misaki_work_home"
))

# P60: タクヤとの最後の面談（元P57）
rows.append((
    61,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): タクヤとの定期面談の場面。\n2コマ目(中段): タクヤが問いかけている。\n3コマ目(下段): ミサキが少し考えている。",
        outfit_block("takuya_zoom_mentor")),
    panels_json(
        (1, "narration", None, "タクヤとの定期面談。"),
        (2, "dialogue", "タクヤ", "最初に言った言葉、覚えてますか？"),
        (3, "narration", None, "ミサキは少し考えた——"),
    ),
    "takuya_zoom_mentor"
))

# P61: 「事務しかできない」→今は
rows.append((
    62,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが答えている。\n2コマ目(中段): タクヤが静かに聞いている。\n3コマ目(下段): ミサキが首を横に振っている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "dialogue", "ミサキ", "「事務しかできない」って言いました"),
        (2, "dialogue", "タクヤ", "今でもそう思いますか？"),
        (3, "dialogue", "ミサキ", "……思いません。自分の見方が変わったんです"),
    ),
    "misaki_work_home"
))

# P63: タクヤの言葉
rows.append((
    63,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "タクヤが穏やかに、でも力強く答えている。感動的な一場面。",
        outfit_block("takuya_zoom_mentor")),
    panels_json((1, "dialogue", "タクヤ", "自分の見方が変わった——それが全てですよ、佐藤さん。")),
    "takuya_zoom_mentor"
))

# P64: 夜のルーティン
rows.append((
    64,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ひなたを寝かしつけているミサキ。\n2コマ目(中段): ミサキがパソコンを開いている。\n3コマ目(下段): Claudeのインターフェース画面。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "夜。ひなたを寝かしつけた後、パソコンを開く。"),
        (2, "narration", None, "いつものルーティンが当たり前になっていた。"),
        (3, "narration", None, "Claudeとの作業が、日常の一部になっていた。"),
    ),
    "misaki_work_home"
))

# P65: 過去と今の対比
rows.append((
    65,
    "テンプレ4",
    manga_prompt("テンプレ4", "2コマ（左・右）",
        "1コマ目(左): 半年前の緊張したミサキ（セピア色・過去）。\n2コマ目(右): 今の自然なミサキ。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "半年前は「AIを使う」ことがイベントだった——"),
        (2, "narration", None, "今は日常だ。当たり前に使っている。"),
    ),
    "misaki_work_home"
))

# P66: 窓ガラスの自分
rows.append((
    66,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): 窓ガラスにミサキの顔が映る。\n2コマ目(中段): ミサキが自分の顔を見つめている。\n3コマ目(下段): 静かに微笑んでいる。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "窓ガラスに自分の顔が映る。"),
        (2, "narration", None, "名刺はない。肩書きもない。"),
        (3, "narration", None, "でも、それで十分だった。"),
    ),
    "misaki_work_home"
))

# P63: ひなたに布団
rows.append((
    67,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキがひなたの部屋を覗く。\n2コマ目(中段): 布団からはみ出したひなたの小さな足。\n3コマ目(下段): ミサキが優しく布団をかけ直している。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ひなたの部屋を覗いた。"),
        (2, "narration", None, "布団からはみ出した小さな体——"),
        (3, "narration", None, "そっと布団をかけ直す。"),
    ),
    "misaki_casual"
))

# P64: モノローグ前半
rows.append((
    68,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキがひなたを見下ろしている後ろ姿。暖かい光。静かな夜。",
        outfit_block("misaki_casual")),
    panels_json((1, "monologue", None, "会社が私の席を用意してくれなかった——")),
    "misaki_casual"
))

# P65: モノローグ後半
rows.append((
    69,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキの横顔。目に光が宿っている。静かな決意。",
        outfit_block("misaki_casual")),
    panels_json((1, "monologue", None, "あの日退職届を出したから、自分の席を見つけられた")),
    "misaki_casual"
))

# P66: 「自分の可能性を自分で決めつけない」
rows.append((
    70,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキが前を向いている。穏やかで力強い表情。",
        outfit_block("misaki_casual")),
    panels_json((1, "monologue", None, "自分の可能性を、自分で決めつけないこと")),
    "misaki_casual"
))

# P67: 新しい企画
rows.append((
    71,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): パソコンの画面が明るくなっている。\n2コマ目(中段): Claudeのインターフェース。\n3コマ目(下段): ミサキがパソコンに向かって座っている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "パソコンの画面が明るくなる。"),
        (2, "narration", None, "Claudeが静かに待っている——"),
        (3, "narration", None, "新しい企画のアイデアがある。"),
    ),
    "misaki_work_home"
))

# P68: 電子書籍の構想
rows.append((
    72,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキが構想を練っている。\n2コマ目(中段): タイトル案が画面に映っている。\n3コマ目(下段): ミサキの目が輝いている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "育児中のママ向けのAIを使った働き方ガイド——"),
        (2, "narration", None, "自分の体験をまとめた電子書籍にしたい。"),
        (3, "narration", None, "誰かの「やってみよう」になれたら——"),
    ),
    "misaki_work_home"
))

# P69: 「やってみよう」
rows.append((
    73,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "ミサキが決意した表情で力強く前を向いている。光が差し込んでいる。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "dialogue", "ミサキ", "やってみよう。"),
        (2, "narration", None, "あの言葉が、ミサキの人生を変えた。"),
    ),
    "misaki_work_home"
))

# P70: ミサキのこれから
rows.append((
    74,
    "テンプレ3",
    manga_prompt("テンプレ3", "2コマ（上段小・下段大）",
        "1コマ目(上段小): ミサキが夜のパソコン画面に向かっている。\n2コマ目(下段大): 画面に新しいプロジェクトのタイトルが輝いている。",
        outfit_block("misaki_work_home")),
    panels_json(
        (1, "narration", None, "次の挑戦が、もう始まっていた。"),
        (2, "monologue", None, "私のキャリアは、私が決める——"),
    ),
    "misaki_work_home"
))

# P71: エンディング
rows.append((
    75,
    "テンプレ5",
    manga_prompt("テンプレ5", "3コマ（上段・中段・下段）",
        "1コマ目(上段): ミサキの物語の幕が静かに閉じる演出。\n2コマ目(中段): ひなたとミサキが一緒にいる場面。\n3コマ目(下段): 新しい始まりの光。",
        outfit_block("misaki_casual")),
    panels_json(
        (1, "narration", None, "ミサキの物語は、ここで一区切り。"),
        (2, "narration", None, "でも彼女のキャリアは、ここから始まる——"),
        (3, "narration", None, "あなたのキャリアも、あなたが決めていい。"),
    ),
    "misaki_casual"
))

# P71: 最終ページ
rows.append((
    76,
    "テンプレ1",
    manga_prompt("テンプレ1", "1コマ",
        "最終ページ。ミサキが前を向いている。夕暮れの光の中。",
        outfit_block("misaki_casual")),
    panels_json((1, "narration", None, "第10話「私のキャリアは、私が決める」おわり")),
    "misaki_casual"
))

# P72: コラム⑩ テキスト(1)
rows.append((
    77,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【コラム原文】\nコラム⑩：おわりに——キャリアコンサルタントとして伝えたいこと\n\n10話にわたるミサキの物語を読んでいただき、ありがとうございます。\n\n最後のコラムでは、キャリアコンサルタントとして——この物語を通じて本当に伝えたかったことをお話しします。\n\n■ミサキは特別な人ではありません\n\nミサキは「AIが得意な人」でも「発信が上手な人」でも「強いメンタルを持つ人」でもありませんでした。事務職で5年。出産で退職。「事務しかできない」と思っていた、どこにでもいる32歳でした。\n\n■「自分にはできる」という仮説\n\n彼女が変わったのは、一つの仮説を持ったからです。「もしかしたら、自分にもできるかもしれない」——この仮説を持ち、実験し、小さな成功体験を積み重ねた。それだけです。",
    "[]",
    ""
))

# P73: コラム⑩ テキスト(2)
rows.append((
    78,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【コラム原文】\n■会社が変わるのを待たなくていい\n\n同じことが会社にも言えます。会社の中にいても外にいても、キャリアは自分で作れる。副業でも、スキルアップでも、社内での新しい挑戦でも。\n\n「会社が用意してくれるキャリア」を待つのではなく、自分から動くこと。そのために必要なのは——「自分にはできる」と思えること。\n\nミサキがそれを証明しました。あなたにも、できます。\n\n■最後に\n\n「大事なのは、自分の可能性を、自分で決めつけないこと」——ミサキが最後に辿り着いた言葉です。\n\nこの本を読み終えたあなたへ。今日から、あなたの物語を始めてください。",
    "[]",
    ""
))

# P74: 著者紹介
rows.append((
    79,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【著者紹介】\n\n著者：Yuichi\n\nフリーランスとして活動するコンテンツクリエイター・プロデューサー。\n\n出産・育児・キャリアの分岐点に立つ女性たちを応援するコンテンツを制作。AIツールを活用した働き方・発信戦略の実践と普及に取り組む。\n\n本シリーズでは、ミサキを通じて「始めることの小ささ」と「続けることの力」を描いた。\n\n■お問い合わせ\ninfo@ynfactory.online",
    "[]",
    ""
))

# P75: 奥付
rows.append((
    80,
    "テキストページ",
    "◆【テキストページ】このページは画像生成不要。EPUB製本時にテキストとして直接レンダリングする。\n◆【奥付】\n\n出産でキャリアを失った元事務職ママが、AIで初めて稼ぐまで　第4巻\n\n2026年4月　初版発行\n\n著者：Yuichi\n発行：YN Factory\n連絡先：info@ynfactory.online\n\n本書の無断複製・転載を禁じます。\nCopyright © 2026 Yuichi / YN Factory. All rights reserved.",
    "[]",
    ""
))

# ==================== CSV書き出し ====================
output_path = "G:/マイドライブ/YNFactory-cc/.company/outputs/ebooks-manga/manga-career-restart/vol4/panels/comicle_output.csv"

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerow(["ページ番号", "使用するコマ割りテンプレ", "漫画作成のプロンプト", "コマ別テキストJSON", "outfit_id"])
    for row in rows:
        writer.writerow(row)

print(f"Pages: {len(rows)}")

# 統計
panel_count_total = 0
over50 = 0
total_chars = 0
outfit_counts = {}
template_counts = {}

for row in rows:
    page_num, tmpl, prompt, panels_raw, outfit_id = row
    if outfit_id:
        outfit_counts[outfit_id] = outfit_counts.get(outfit_id, 0) + 1
    template_counts[tmpl] = template_counts.get(tmpl, 0) + 1
    try:
        panels = json.loads(panels_raw)
        for p in panels:
            text = p.get("text", "")
            total_chars += len(text)
            panel_count_total += 1
            if len(text) > 50:
                over50 += 1
    except Exception:
        pass

print(f"Total panels: {panel_count_total}")
print(f"Total chars: {total_chars}")
over50_pct = over50 / panel_count_total * 100 if panel_count_total else 0
print(f"Over 50 chars: {over50} / {panel_count_total} = {over50_pct:.1f}%")
print("outfit_counts:", json.dumps(outfit_counts, ensure_ascii=False))
print("template_counts:", json.dumps(template_counts, ensure_ascii=False))
