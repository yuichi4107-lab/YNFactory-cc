# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(".company/outputs/ai-stock-investment")
SOURCE = ROOT / "文字本"
OUT = ROOT / "マンガ版"

TITLE = "マンガでわかる！AI株に投資すべきか？"
SOURCE_TITLE = "AI株に投資すべきか？"
SUBTITLE = "熱狂に乗る前に知っておきたい企業分析・分散・リスク管理の実践入門"
AUTHOR = "Yuichi"
TARGET_PAGES = 56


STYLE = (
    "日本のビジネスマンガ調。清潔感のある線、表情は読みやすく、"
    "カフェ・自宅・オフィス・証券アプリ画面を背景にした実務的な演出。"
    "投資判断を煽らず、分散・リスク管理・数字を見る態度が伝わる落ち着いた色調。"
    "実写風、写真風、3D風は禁止。"
)

TEMPLATE_DESCRIPTIONS = {
    "テンプレ1": "1コマ: ページ全体を使った大ゴマ",
    "テンプレ2": "2コマ: 上下に均等2分割。読み順は上段、下段",
    "テンプレ3": "2コマ: 上段小、下段大。読み順は上段、下段",
    "テンプレ4": "2コマ: 上段大、下段小。読み順は上段、下段",
    "テンプレ5": "3コマ: 上・中・下の3段構成。読み順は上段、中段、下段",
    "テンプレ6": "3コマ: 上段1コマ + 下段左右2コマ。読み順は上段、下段右、下段左",
    "テンプレ7": "3コマ: 上段左右2コマ + 下段1コマ。読み順は上段右、上段左、下段",
}


CHARACTER_DEFS = {
    "ミナミ": (
        "ミナミ: 32歳女性、会社員。肩にかかる黒髪のボブ、知的で少し不安げな大きな目、"
        "細身。白ブラウスにネイビーのカーディガン、ベージュのパンツ。"
        "NISAで投資を始めており、AI株の熱狂に揺れる読者代表。"
    ),
    "高橋": (
        "高橋: 45歳男性、独立系ファイナンシャルプランナー。短い黒髪に少し白髪、"
        "落ち着いた目、標準体型。チャコールグレーのジャケット、白シャツ、ノーネクタイ。"
        "数字とリスク管理を重視する案内役。"
    ),
    "リョウ": (
        "リョウ: 28歳男性、データアナリスト。明るい茶色の短髪、丸メガネ、細身。"
        "黒いTシャツにライトグレーのパーカー。AI業界の構造とデータを可視化する友人。"
    ),
    "outfit_presets": {
        "minami_cafe": {
            "character": "ミナミ",
            "description": "白ブラウス、ネイビーのカーディガン、ベージュのパンツ、黒いフラットシューズ",
            "scenes": ["カフェ", "相談", "学習"],
        },
        "takahashi_advisor": {
            "character": "高橋",
            "description": "チャコールグレーのジャケット、白シャツ、黒い革靴、薄いノートPC",
            "scenes": ["相談", "オフィス", "解説"],
        },
        "ryo_data": {
            "character": "リョウ",
            "description": "黒いTシャツ、ライトグレーのパーカー、デニム、丸メガネ、タブレット端末",
            "scenes": ["データ分析", "カフェ", "オンライン会議"],
        },
        "team_cafe": {
            "character": "all",
            "description": "ミナミは白ブラウスとネイビーカーディガン、高橋はチャコールジャケット、リョウはグレーパーカー",
            "scenes": ["カフェでの相談", "学習会", "章末まとめ"],
        },
    },
}


BEATS = [
    ("プロローグ", "SNSの急騰投稿を見たミナミが、AI株を今すぐ買わないと置いていかれると焦る。", [("ミナミ", "AI株、今からでも買うべきですか？"), ("高橋", "まず、焦りを判断軸に変えましょう。")]),
    ("プロローグ", "高橋は、AI株を買うか買わないかではなく、資産全体の中でどう扱うかを考える本だと告げる。", [("高橋", "結論は二択ではありません。どのリスクを、どの量で取るかです。"), ("ミナミ", "買う前に決めることがあるんですね。")]),
    ("プロローグ", "リョウがタブレットでAI関連企業の地図を広げ、AI株という言葉の中身が広すぎると示す。", [("リョウ", "AI株という一語の中に、半導体もクラウドもアプリも入っています。"), ("ミナミ", "同じAIでも、全然違う会社なんですね。")]),
    ("プロローグ", "高橋は、最初に生活防衛資金と長期資産の土台を守ることを強調する。", [("高橋", "熱狂より先に、生活資金と長期資産を守ります。"), ("ミナミ", "投資の前に、守る順番ですね。")]),
    ("プロローグ", "ミナミはAIの未来を信じたい気持ちと、損をしたくない気持ちの間で揺れる。", [("ミナミ", "未来は信じたい。でも、高値づかみは怖いです。"), ("高橋", "その怖さは正常です。だからルール化します。")]),
    ("プロローグ", "3人は、AI株投資を企業分析、価格、分散、売る条件に分けて考える旅を始める。", [("リョウ", "地図を四つに分けましょう。企業、価格、分散、見直しです。"), ("ミナミ", "ようやく霧が晴れてきました。")]),
    ("第1章", "AI株ブームは、生成AIの利用拡大だけでなく、GPU、データセンター、電力、ソフトウェアの投資連鎖で起きている。", [("リョウ", "ブームの正体は、AIアプリだけではなく設備投資の連鎖です。"), ("高橋", "売上になる場所とコストになる場所を分けます。")]),
    ("第1章", "ミナミは、話題の企業がすべて同じように儲かるわけではないと知る。", [("ミナミ", "AIの中心にいる会社なら全部強いと思っていました。"), ("高橋", "強い立場でも、株価が先に期待を織り込むことがあります。")]),
    ("第1章", "高橋は、投資家の期待と企業の実績の差が株価を大きく動かすと説明する。", [("高橋", "株価は未来への期待で動きます。実績との差が大きいほど揺れます。"), ("ミナミ", "良い会社でも下がる理由があるんですね。")]),
    ("第1章", "リョウがデータセンター建設、半導体需要、クラウド利用料の流れを図で示す。", [("リョウ", "設備投資は波のように広がります。上流と下流で利益の出方が違います。"), ("ミナミ", "ニュースの見方が変わります。")]),
    ("第1章", "高橋は、ブーム初期ほど物語が強く、後半ほど数字で確認されると語る。", [("高橋", "物語だけで買う時期と、数字で選別される時期は違います。"), ("ミナミ", "今がどちらなのかを見ないといけない。")]),
    ("第1章", "章末で、AI株は成長テーマであるほど、期待過剰にもなりやすいとまとめる。", [("高橋", "成長テーマほど、価格には熱が入りやすい。"), ("ミナミ", "だから、未来だけでなく価格も見るんですね。")]),
    ("第1章", "ミナミは、AI株を一括りにせず、収益源と期待値で分解するノートを作る。", [("ミナミ", "AI株というラベルを外して、どこで稼ぐかを書きます。"), ("リョウ", "そのメモが、最初のフィルターになります。")]),
    ("第2章", "第2章では、半導体、クラウド、ソフトウェア、電力・インフラ、ETFを分けて見る。", [("高橋", "まずはAI関連銘柄を層に分けます。"), ("ミナミ", "一つのテーマを棚に分ける感じですね。")]),
    ("第2章", "半導体はAI需要の中心だが、景気循環や供給過剰の影響を受けると説明する。", [("リョウ", "半導体は強い一方で、サイクルがあります。"), ("高橋", "永遠に直線で伸びる前提は危険です。")]),
    ("第2章", "クラウド企業はAI利用の受け皿だが、設備投資が利益率を押し下げる可能性もある。", [("高橋", "クラウドは受益者ですが、投資負担も背負います。"), ("ミナミ", "売上が増えても利益が増えるとは限らないんですね。")]),
    ("第2章", "ソフトウェア企業はAIで機能を増やせるが、課金力と解約率が重要になる。", [("リョウ", "AI機能を入れても、ユーザーが追加料金を払うかは別問題です。"), ("ミナミ", "便利さが利益に変わるかを見る。")]),
    ("第2章", "電力・データセンター・冷却技術のような周辺インフラにも資金が向かる。", [("高橋", "掘る人だけでなく、つるはしを売る会社もあります。"), ("ミナミ", "でも、それぞれの利益率は違いますよね。")]),
    ("第2章", "ETFは個別企業リスクを下げるが、中身と手数料を確認する必要がある。", [("高橋", "ETFは分散になりますが、中身を見ない分散は危険です。"), ("ミナミ", "名前ではなく保有銘柄を見るんですね。")]),
    ("第2章", "ミナミは、AI関連を一枚の地図にして、自分がどの層に投資するのかを決める。", [("ミナミ", "私は個別銘柄より、まずETFと少額の個別で考えます。"), ("高橋", "良い入口です。集中しすぎないことが大切です。")]),
    ("第2章", "章末で、AI関連銘柄は事業の位置、利益の出方、価格の三つで見分けるとまとめる。", [("リョウ", "位置、利益、価格。この三つを同時に見ます。"), ("ミナミ", "テーマ買いから、企業選びに変わりました。")]),
    ("第3章", "第3章では、企業分析の入口として売上成長率、粗利率、営業利益率、キャッシュフローを見る。", [("高橋", "まず五つの数字を見ます。売上、粗利、営業利益、現金、投資額です。"), ("ミナミ", "ニュースより決算ですね。")]),
    ("第3章", "高橋は、売上が伸びても利益率が下がる企業は、競争や投資負担を確認すると説明する。", [("高橋", "伸びているのに利益率が落ちるなら、理由を探します。"), ("ミナミ", "成長の質を見るんですね。")]),
    ("第3章", "リョウがPER、PSR、フリーキャッシュフロー利回りを並べ、価格の高さを測る。", [("リョウ", "指標は答えではなく、温度計です。"), ("高橋", "高い理由を説明できるかが大事です。")]),
    ("第3章", "ミナミは、良い会社ほど高く買ってしまう危険があると気づく。", [("ミナミ", "好きな会社ほど、高くても買いたくなります。"), ("高橋", "その気持ちに、買う条件をぶつけます。")]),
    ("第3章", "強気・標準・弱気の三つのシナリオで、成長率と利益率の前提を変えて考える。", [("高橋", "未来は一つに決めず、三つのシナリオで持ちます。"), ("ミナミ", "外れたときの心の準備にもなります。")]),
    ("第3章", "粉飾や過度な宣伝、根拠の薄いSNS投稿を避けるチェックポイントを作る。", [("リョウ", "派手な投稿より、一次情報と決算資料を見ましょう。"), ("ミナミ", "おすすめ投稿だけで決めないようにします。")]),
    ("第3章", "章末で、企業分析は未来を当てる作業ではなく、買ってよい価格帯を狭める作業だとまとめる。", [("高橋", "分析は予言ではありません。高すぎる買い物を避ける道具です。"), ("ミナミ", "買わない判断も、立派な判断ですね。")]),
    ("第3章", "ミナミは、候補企業ごとに数字、強み、リスク、買う条件を一枚にまとめる。", [("ミナミ", "銘柄メモに、買う理由と買わない理由を両方書きます。"), ("高橋", "それで熱狂から一歩離れられます。")]),
    ("第4章", "第4章では、AI株を資産全体にどう入れるかを考える。", [("高橋", "良いテーマでも、入れすぎれば生活を揺らします。"), ("ミナミ", "割合を決めてから買うんですね。")]),
    ("第4章", "生活防衛資金、インデックス投資、AI株の順で土台を確認する。", [("高橋", "順番は、守るお金、育てるお金、攻めるお金です。"), ("ミナミ", "AI株は攻めるお金の一部ですね。")]),
    ("第4章", "コア・サテライトの考え方で、インデックスを中心にAI株を周辺に置く。", [("リョウ", "中心は広く分散、周辺でテーマを試す形です。"), ("ミナミ", "これなら失敗しても全部は崩れません。")]),
    ("第4章", "一括投資と積立投資の違いを、心理面と価格変動の面から比べる。", [("高橋", "一括は期待を取りやすいが、心が揺れやすい。積立は時間でならします。"), ("ミナミ", "私は積立と少額追加が合いそうです。")]),
    ("第4章", "個別銘柄に集中する場合は、最大比率と損失許容額を先に決める。", [("高橋", "何株買うかより、いくら失っても生活が壊れないかです。"), ("ミナミ", "損失額で考えると現実的になります。")]),
    ("第4章", "為替、金利、景気後退、規制など、AI以外の要因でも株価が動くと確認する。", [("リョウ", "AIが順調でも、金利や為替で株価は揺れます。"), ("ミナミ", "テーマ以外の風も受けるんですね。")]),
    ("第4章", "章末で、買う前に割合、買い方、売る条件を紙に書くことを決める。", [("ミナミ", "買う前に、割合と売る条件をメモします。"), ("高橋", "その一枚が、未来の自分を助けます。")]),
    ("第4章", "ミナミは、AI株を資産全体の一部にとどめ、定期的に見直すルールを作る。", [("ミナミ", "私は資産全体の5%から始めます。"), ("高橋", "小さく始めるのは、弱さではなく設計です。")]),
    ("第5章", "第5章では、買った後に何を見るかを整理する。", [("高橋", "買ったら終わりではありません。見続ける数字を決めます。"), ("ミナミ", "毎日株価を見るだけではダメなんですね。")]),
    ("第5章", "四半期決算で、売上成長、利益率、ガイダンス、設備投資、キャッシュを確認する。", [("リョウ", "決算では、伸びた数字と悪化した数字をセットで見ます。"), ("ミナミ", "良い点だけ拾わないようにします。")]),
    ("第5章", "投資ストーリーが崩れた場合、株価が戻るまで祈るのではなく仮説を見直す。", [("高橋", "ストーリーが崩れたら、祈るより先に仮説を直します。"), ("ミナミ", "持ち続ける理由を更新するんですね。")]),
    ("第5章", "値上がりしたときこそ、利益確定やリバランスのルールを確認する。", [("ミナミ", "上がったらもっと欲しくなりそうです。"), ("高橋", "だから上がった時のルールも先に作ります。")]),
    ("第5章", "SNSで強い意見を見るほど、最初に書いた投資メモに戻る。", [("リョウ", "市場が騒がしい日は、自分のメモを読み返しましょう。"), ("ミナミ", "他人の熱より、自分のルールですね。")]),
    ("第5章", "詐欺的なAI投資話や、元本保証をうたう勧誘には近づかない。", [("高橋", "元本保証の高リターン話は、投資ではなく危険信号です。"), ("ミナミ", "AIという言葉で油断しないようにします。")]),
    ("第5章", "章末で、投資後のチェックリストを作り、見る日をカレンダーに入れる。", [("ミナミ", "決算日と見直し日を予定に入れます。"), ("高橋", "続けられる仕組みにするのが大切です。")]),
    ("第5章", "ミナミは、株価ではなく自分の判断プロセスを育てることに価値を感じ始める。", [("ミナミ", "勝ち負けだけでなく、判断を育てる投資にしたいです。"), ("高橋", "その姿勢が長く残ります。")]),
    ("第5章", "3人は、AI株投資の判断を一枚のルール表にまとめる。買う理由、買わない理由、見直す日が並ぶ。", [("リョウ", "最後は、情報ではなく行動ルールに落とします。"), ("ミナミ", "これなら次のニュースにも振り回されません。")]),
    ("エピローグ", "ミナミは、AIの未来を否定せず、熱狂から距離を取る方法を身につけた。", [("ミナミ", "AIの未来は楽しみです。でも、全財産を賭ける話ではありません。"), ("高橋", "その距離感が、熱狂を味方にします。")]),
    ("エピローグ", "3人は、AI株に投資すべきかの答えを、買うか買わないかではなく自分の条件で決めるとまとめる。", [("リョウ", "答えは市場の声ではなく、自分の条件から出します。"), ("ミナミ", "私は、少額・分散・見直しで始めます。")]),
    ("エピローグ", "最後に、高橋は投資判断は自己責任であり、情報に振り回されず学び続けることを伝える。", [("高橋", "本書は一般的な情報です。最後の判断は、自分の状況に合わせてください。"), ("ミナミ", "焦らず、でも学びながら進みます。")]),
    ("エピローグ", "ミナミは投資ノートを閉じ、次の決算日をカレンダーに入れて静かに前を向く。", [("ミナミ", "未来に参加するなら、まず自分のルールから。"), ("高橋", "それがAI株との健全な付き合い方です。")]),
    ("エピローグ", "ラストは、AIの光る街を背景に、3人が地に足のついた表情で歩き出す。", [("リョウ", "技術は進みます。投資家も、判断の技術を磨けます。"), ("ミナミ", "熱狂ではなく、納得で進みます。")]),
]


def panel_count(template: str) -> int:
    if template == "テンプレ1":
        return 1
    if template in {"テンプレ2", "テンプレ3", "テンプレ4"}:
        return 2
    return 3


def make_template_sequence() -> list[str]:
    remaining = Counter(
        {
            "テンプレ1": 8,
            "テンプレ2": 6,
            "テンプレ3": 6,
            "テンプレ4": 6,
            "テンプレ5": 9,
            "テンプレ6": 8,
            "テンプレ7": 8,
        }
    )
    pattern = ["テンプレ5", "テンプレ2", "テンプレ6", "テンプレ3", "テンプレ7", "テンプレ4", "テンプレ1", "テンプレ5", "テンプレ6", "テンプレ7"]
    seq: list[str] = []
    while sum(remaining.values()):
        progressed = False
        for template in pattern:
            if remaining[template] > 0:
                seq.append(template)
                remaining[template] -= 1
                progressed = True
        if not progressed:
            break
    assert len(seq) == 51
    return seq


def make_text_json(template: str, lines: list[tuple[str, str]], narration: str) -> list[dict[str, object]]:
    n = panel_count(template)
    items: list[dict[str, object]] = []
    if n == 1:
        items.append({"panel_id": 1, "type": "narration", "speaker": None, "text": narration})
        for speaker, text in lines[:2]:
            items.append({"panel_id": 1, "type": "dialogue", "speaker": speaker, "text": text})
        return items
    if n == 2:
        items.append({"panel_id": 1, "type": "narration", "speaker": None, "text": narration})
        items.append({"panel_id": 1, "type": "dialogue", "speaker": lines[0][0], "text": lines[0][1]})
        items.append({"panel_id": 2, "type": "dialogue", "speaker": lines[1][0], "text": lines[1][1]})
        return items
    items.append({"panel_id": 1, "type": "narration", "speaker": None, "text": narration})
    items.append({"panel_id": 2, "type": "dialogue", "speaker": lines[0][0], "text": lines[0][1]})
    items.append({"panel_id": 3, "type": "dialogue", "speaker": lines[1][0], "text": lines[1][1]})
    return items


def story_prompt(template: str, beat: tuple[str, str, list[tuple[str, str]]], page_num: int) -> tuple[str, str]:
    section, narration, lines = beat
    json_items = make_text_json(template, lines, narration)
    panel_lines: list[str] = []
    for item in json_items:
        pid = item["panel_id"]
        if item["type"] == "narration":
            panel_lines.append(f"{pid}コマ目: {section}の場面。ミナミ、高橋、リョウの表情と背景で状況を見せる。ナレーション: ［四角枠］{item['text']}")
        else:
            speaker = item["speaker"]
            panel_lines.append(f"{pid}コマ目: {speaker}が自然な表情で話す。セリフ: {speaker}の吹き出しに「{item['text']}」")

    prompt = "\n".join(
        [
            "◆【注意】【】で囲まれた単語は感情や状況の指示であり、画像内に文字として描画しないでください",
            "◆【絶対最優先】必ずフルカラーにしてください",
            "◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。",
            "◆【出力サイズ】2:3",
            "◆【補足情報】上下左右に50ピクセルの余白を設けてください",
            "◆【補足情報】キャラクター外見: ミナミは32歳女性の黒髪ボブ会社員。高橋は45歳男性の落ち着いたFP。リョウは28歳男性の丸メガネのデータアナリスト。",
            "◆【補足情報】服装: ミナミは白ブラウスとネイビーカーディガン、高橋はチャコールジャケット、リョウはグレーパーカー。",
            f"◆【コマ構成】{template}: {TEMPLATE_DESCRIPTIONS[template]}",
            f"◆【作画】{STYLE}",
            f"◆【ストーリー】ページ{page_num:03d}・{section}",
            *panel_lines,
            "背景: 投資ノート、タブレットのグラフ、証券アプリ風の抽象UI、カフェや小さな相談室を使い分ける。実在企業ロゴや個別銘柄名は描かない。",
        ]
    )
    return prompt, json.dumps(json_items, ensure_ascii=False)


def write_outputs() -> None:
    for path in [
        OUT / "KDP出版用",
        OUT / "manuscript" / "characters",
        OUT / "panels" / "pages",
        OUT / "quality_reports",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    manuscript_files = sorted((SOURCE / "manuscript").glob("*.md"))
    source_chars = sum(len(p.read_text(encoding="utf-8")) for p in manuscript_files)
    source_chapters = [p.stem for p in manuscript_files]

    progress = {
        "book_name": "ai-stock-investment",
        "source_path": str(SOURCE),
        "output_path": str(OUT),
        "source_title": SOURCE_TITLE,
        "manga_title": TITLE,
        "target_pages": TARGET_PAGES,
        "genre": "ビジネス・投資学習マンガ",
        "batch_size": 8,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_analysis": {
            "manuscript_files": [p.name for p in manuscript_files],
            "source_chars": source_chars,
            "chapters": source_chapters,
        },
        "steps": {
            "1_source": {"status": "done"},
            "2_scenario": {"status": "done"},
            "3_characters": {"status": "done", "images_status": "pending"},
            "4_panels": {"status": "done"},
            "5_images": {"status": "pending", "completed": 0, "total": 52, "failed": []},
            "6_cover": {"status": "pending"},
            "7_epub": {"status": "pending"},
            "8_metadata": {"status": "pending"},
        },
    }

    scenario_lines = [
        f"「{TITLE}」",
        f"原作: {SOURCE_TITLE}",
        "",
        "登場人物",
        "ミナミ: AI株に興味を持つ会社員。SNSの熱狂に揺れる読者代表。",
        "高橋: 独立系FP。熱狂を判断軸へ変える案内役。",
        "リョウ: データアナリスト。AI業界の構造を図解する友人。",
        "",
    ]
    current = None
    for section, narration, lines in BEATS:
        if section != current:
            scenario_lines.append(f"## {section}")
            current = section
        scenario_lines.append(narration)
        for speaker, text in lines:
            scenario_lines.append(f"{speaker}「{text}」")
        scenario_lines.append("")

    (OUT / "manuscript" / "シナリオ.txt").write_text("\n".join(scenario_lines), encoding="utf-8")
    (OUT / "manuscript" / "character_defs.json").write_text(
        json.dumps(CHARACTER_DEFS, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "manuscript" / "characters" / "character_reference_prompts.md").write_text(
        "\n\n".join(
            [
                "# キャラクターリファレンス生成プロンプト",
                "◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。",
                "ミナミ: 32歳女性、黒髪ボブ、白ブラウス、ネイビーカーディガン、ベージュのパンツ。全身立ち絵、正面、白背景。",
                "高橋: 45歳男性、短い黒髪に少し白髪、チャコールグレーのジャケット、白シャツ。全身立ち絵、正面、白背景。",
                "リョウ: 28歳男性、明るい茶色の短髪、丸メガネ、ライトグレーのパーカー。全身立ち絵、正面、白背景。",
            ]
        ),
        encoding="utf-8",
    )

    rows: list[list[str]] = []
    rows.append(
        [
            "1",
            "テキストページ",
            "◆【テキストページ】目次\nマンガでわかる！AI株に投資すべきか？\nプロローグ / 第1章 AI株ブームの正体 / 第2章 AI関連銘柄を分解する / 第3章 企業分析とバリュエーション / 第4章 ポートフォリオにどう入れるか / 第5章 投資後に見続けるもの / エピローグ",
            "[]",
            "",
        ]
    )
    intro_json = json.dumps(
        [
            {"panel_id": 1, "type": "narration", "speaker": None, "text": "登場人物紹介"},
            {"panel_id": 1, "type": "narration", "speaker": None, "text": "ミナミ、AI株に迷う会社員"},
            {"panel_id": 1, "type": "narration", "speaker": None, "text": "高橋、数字で考えるFP"},
            {"panel_id": 1, "type": "narration", "speaker": None, "text": "リョウ、AI業界を図解するデータアナリスト"},
        ],
        ensure_ascii=False,
    )
    intro_prompt = "\n".join(
        [
            "◆【絶対最優先】必ずフルカラーにしてください",
            "◆【絶対最優先】必ず日本のアニメ・マンガ調のイラストで描いてください。実写風・フォトリアル風は禁止です。",
            "◆【出力サイズ】2:3",
            "◆【コマ構成】テンプレ1: 1コマ: ページ全体を使った大ゴマ",
            f"◆【作画】{STYLE}",
            "◆【ストーリー】登場人物紹介ページ。ミナミ、高橋、リョウを縦に並べた全身イラスト。名前と一行紹介の吹き出しを読みやすく配置。",
        ]
    )
    rows.append(["2", "テンプレ1", intro_prompt, intro_json, "team_cafe"])

    templates = make_template_sequence()
    for idx, (template, beat) in enumerate(zip(templates, BEATS), start=3):
        prompt, text_json = story_prompt(template, beat, idx)
        rows.append([str(idx), template, prompt, text_json, "team_cafe"])

    rows.append(
        [
            "54",
            "テキストページ",
            "◆【テキストページ】投資前チェックリスト\n1. 生活防衛資金を残しているか\n2. 資産全体の何%までにするか\n3. 個別株かETFかを選んだ理由はあるか\n4. 買う価格と買わない価格を決めたか\n5. 決算で見る数字を決めたか\n6. 売る条件を書いたか",
            "[]",
            "",
        ]
    )
    rows.append(
        [
            "55",
            "テキストページ",
            "◆【テキストページ】著者紹介\nYuichi\nYN出版。AI活用、仕事の自動化、個人の学びをテーマに、実務で使える電子書籍を制作。本書は一般的な情報提供であり、個別銘柄の購入・売却を推奨しない。",
            "[]",
            "",
        ]
    )
    rows.append(
        [
            "56",
            "テキストページ",
            f"◆【テキストページ】奥付\n書名: {TITLE}\n著者: {AUTHOR}\n発行所: YN出版\n発行日: 2026年6月4日\nCopyright (c) 2026 Yuichi. All rights reserved.",
            "[]",
            "",
        ]
    )

    csv_path = OUT / "panels" / "comicle_output.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ページ番号", "使用するコマ割りテンプレ", "漫画作成のプロンプト", "コマ別テキストJSON", "outfit_id"])
        writer.writerows(rows)

    template_counts = Counter(row[1] for row in rows if row[1] != "テキストページ")
    report = [
        "# ebook-to-manga Step 1-4 Report",
        "",
        f"- source: `{SOURCE}`",
        f"- output: `{OUT}`",
        f"- source chars: {source_chars}",
        f"- target pages: {TARGET_PAGES}",
        f"- CSV rows: {len(rows)}",
        f"- image pages: {sum(template_counts.values())}",
        "",
        "## Template Distribution",
    ]
    total_image = sum(template_counts.values())
    for template in [f"テンプレ{i}" for i in range(1, 8)]:
        count = template_counts[template]
        report.append(f"- {template}: {count} ({count / total_image:.1%})")
    report.extend(
        [
            "",
            "## Skill Compliance",
            "- Step 1 source analysis: done",
            "- Step 2 scenario: done",
            "- Step 3 character definitions: done; character reference images pending in Step 5/6 generation flow",
            "- Step 4 CSV: done with required 5-column header",
            "- Step 5 images: pending; generate in 8-page batches using ChatGPT/Codex image generation",
        ]
    )
    (OUT / "quality_reports" / "STEP1_4_REPORT.md").write_text("\n".join(report), encoding="utf-8")

    cover_prompt = f'''request_type: generate_hyper_detailed_magazine_cover_with_fixed_aspect_ratio
title: "{TITLE}"
subtitle: "{SUBTITLE}"
author: "{AUTHOR}"

description: >
  添付された原稿ドキュメントを分析して抽出したテキスト要素を使用して、
  圧倒的な情報量と高いデザイン密度を備えたプロ仕様のマンガ書籍カバーを生成する。

design_taste: >
  マンガ・コミック風の書籍カバーデザイン。
  日本のビジネスマンガ調。投資の熱狂と冷静な判断軸の対比を、明るく信頼感のある構図で表現。
  キャラクターを全面に配置し、株価チャートやAI回路を抽象背景として使う。

character: >
  ミナミ: 32歳女性、黒髪ボブ、白ブラウス、ネイビーカーディガン。AI株に迷いながら学ぶ主人公。
  高橋: 45歳男性、チャコールジャケットのFP。落ち着いた案内役。
  リョウ: 28歳男性、丸メガネとグレーパーカーのデータアナリスト。AI業界を図解する友人。

processing_steps:
  - step 1: 原稿分析とテキスト要素抽出
  - step 2: デザインムードと構図の決定
  - step 3: キャラクター配置と背景の生成（2:3アスペクト比）
  - step 4: テキストと装飾要素のレイアウト
  - step 5: キャラクター・背景とテキスト・装飾の統合
'''
    (OUT / "KDP出版用" / "表紙プロンプト.md").write_text(cover_prompt, encoding="utf-8")

    project = f"""# {TITLE}

## ebook-to-manga Step 1-4

- 元書籍: {SOURCE_TITLE}
- サブタイトル: {SUBTITLE}
- 著者: {AUTHOR}
- 入力フォルダ: `{SOURCE}`
- 出力フォルダ: `{OUT}`
- 作画ジャンル: ビジネス・投資学習マンガ
- 目標ページ数: {TARGET_PAGES}
- 画像生成バッチ: 8ページ単位

## 進捗

- Step 1 ソース分析: done
- Step 2 マンガ用シナリオ: done
- Step 3 キャラクターデザイン定義: done
- Step 4 コマ割りCSV: done
- Step 5 画像生成: pending
- Step 6 表紙作成: pending
- Step 7 EPUB製本: pending
- Step 8 メタデータ: pending
"""
    (OUT / "project.md").write_text(project, encoding="utf-8")
    (OUT / "progress.json").write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"rows": len(rows), "image_pages": total_image, "template_counts": dict(template_counts)}, ensure_ascii=False))


if __name__ == "__main__":
    write_outputs()
