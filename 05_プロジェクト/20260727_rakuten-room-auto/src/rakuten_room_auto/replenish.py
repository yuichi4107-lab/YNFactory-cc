from __future__ import annotations

import hashlib
import re

# タイトルからクーポン・セール文言などのノイズを除去するためのパターン
BRACKET_PATTERN = re.compile(r"【[^】]*】|\[[^\]]*\]|［[^］]*］|＼[^／]*／|〈[^〉]*〉|《[^》]*》|（[^）]*）|\([^)]*\)")
NOISE_TOKEN_PATTERN = re.compile(
    r"クーポン|OFF|ｵﾌ|オフ|ポイント|マラソン|スーパーSALE|セール|限定|割引|レビュー特典|特典|送料無料|即納|%|％|\d+円",
    re.IGNORECASE,
)
# 優良誤認（景表法）につながりうる誇大表現。出どころを検証できないため紹介文には使わない
EXAGGERATED_TOKEN_PATTERN = re.compile(
    r"No\.?\s?1|Ｎｏ\.?１|ナンバーワン|\d+位|１位|一位|日本一|世界一|世界初|業界初|業界最高|殿堂|受賞|"
    r"グランプリ|最高|最強|最安|圧倒的|奇跡|驚異|完璧|完全|永久|絶対|万能|究極|至高|革命",
    re.IGNORECASE,
)

FALLBACK_NAME = "楽天ランキング掲載の人気アイテム"

DESCRIPTION_TEMPLATES = [
    "楽天のデイリーランキングで見つけた人気商品です。{name}。レビューも参考にチェックしてみてください。",
    "{name}。楽天ランキング上位の注目アイテムです。詳細は商品ページでご確認ください。",
    "いま楽天ランキングで人気の「{name}」。気になる方はレビューもあわせてどうぞ。",
]

MAX_NAME_CHARS = 40


def contains_exaggerated_claim(text: str) -> bool:
    """優良誤認につながりうる誇大表現を含むかどうか。"""
    return bool(EXAGGERATED_TOKEN_PATTERN.search(text))


def clean_item_title(title: str) -> str:
    """ランキングの商品タイトルから宣伝ノイズ・誇大表現を落とし、紹介文に使える短い商品名にする。"""
    text = BRACKET_PATTERN.sub(" ", title)
    tokens = [
        token
        for token in text.split()
        if token and not NOISE_TOKEN_PATTERN.search(token) and not contains_exaggerated_claim(token)
    ]
    name = ""
    for token in tokens:
        candidate = f"{name} {token}".strip()
        if len(candidate) > MAX_NAME_CHARS:
            break
        name = candidate
    if not name:
        # トークン分割で全滅した場合は、文字列全体からノイズ・誇大表現を除去して再構成する
        stripped = EXAGGERATED_TOKEN_PATTERN.sub("", NOISE_TOKEN_PATTERN.sub("", text))
        name = " ".join(stripped.split())[:MAX_NAME_CHARS].strip()
    return name or FALLBACK_NAME


ITEM_URL_PATTERN = re.compile(r"https?://item\.rakuten\.co\.jp/([^/]+)/([^/?#]+)/?")
NON_WORD_PATTERN = re.compile(r"[^0-9a-zぁ-んァ-ヶ一-龥ー]")
TRAILING_DIGITS_PATTERN = re.compile(r"\d+$")

# 商品名ベースの類似度がこの値以上なら「同じ商品」とみなしてスキップする
# （実データ検証: 同一商品ペア0.31〜0.82、別商品ペア0.26以下）
SIMILARITY_THRESHOLD = 0.28

# バリエーション紹介文のパターン。定型文の量産はROOMでいいねが付きにくいため、
# 商品ごとにハッシュでパターンを固定して文面を散らす(同じ商品には常に同じ文)。
# 順位の数字は投稿時点でズレている可能性があるため「上位」表現に留める(優良誤認の予防)
VARIED_OPENERS = [
    "{name}、いま楽天ランキング上位に入っている人気商品です。",
    "楽天ランキングで売れている{name}をチェックしました。",
    "最近気になっている{name}。ランキングでも上位と好調みたいです。",
    "{name}が楽天ランキング上位に入っていたのでご紹介。",
]
VARIED_SURGE_OPENERS = [
    "{name}、ランキング急上昇中で注目度が上がっています。",
    "いま伸びてる{name}。ランキングの順位が一気に上がってきました。",
]
VARIED_REVIEW_SENTENCES = [
    "レビュー{count}件で評価★{avg}と安定の人気ぶり。",
    "★{avg}({count}件)と口コミ評価も高めです。",
    "{count}件のレビューが付いていて、評価は★{avg}。",
]
VARIED_CLOSERS = [
    "気になった方はレビューもチェックしてみてください。",
    "お買い物リストの候補にどうぞ。",
    "使い勝手が良さそうなので候補に入れました。",
    "セールのタイミングで狙うのも良さそうです。",
]

PLACEHOLDER_PATTERN = re.compile(r"\{[^}]*\}")

# 「。」「★」のような極小断片は先に置換されると長い断片のマッチを壊すため除外する
MIN_FRAGMENT_CHARS = 4


def _literal_fragments(templates: list[str]) -> list[str]:
    return [
        frag
        for template in templates
        for frag in PLACEHOLDER_PATTERN.split(template)
        if len(frag) >= MIN_FRAGMENT_CHARS
    ]


# 自動生成テンプレートの定型部分。紹介文同士の類似度計算では取り除く
# （定型文の共有だけで別商品が「同一」と誤判定されるのを防ぐ）
# FALLBACK_NAMEも含める: 誇大表現除去で両方フォールバックした別商品同士が
# 完全一致（類似度1.0）と誤判定されるのを防ぐ。除去後に空になれば類似度は0.0になる
# 長い断片から先に置換する(短い断片が長い断片のマッチを壊さないように)
TEMPLATE_FRAGMENTS = sorted(
    [fragment for template in DESCRIPTION_TEMPLATES for fragment in template.split("{name}") if fragment]
    + _literal_fragments(VARIED_OPENERS + VARIED_SURGE_OPENERS + VARIED_REVIEW_SENTENCES + VARIED_CLOSERS)
    + [FALLBACK_NAME],
    key=len,
    reverse=True,
)


def strip_template_boilerplate(text: str) -> str:
    for fragment in TEMPLATE_FRAGMENTS:
        text = text.replace(fragment, " ")
    return text


def normalize_for_similarity(text: str) -> str:
    text = strip_template_boilerplate(text)
    text = BRACKET_PATTERN.sub(" ", text)
    return NON_WORD_PATTERN.sub("", text.lower())


def product_similarity(text_a: str, text_b: str) -> float:
    """文字バイグラムのオーバーラップ係数（0.0〜1.0）。商品名・紹介文の同一商品判定に使う。"""
    a = normalize_for_similarity(text_a)
    b = normalize_for_similarity(text_b)
    bigrams_a = {a[i : i + 2] for i in range(len(a) - 1)}
    bigrams_b = {b[i : i + 2] for i in range(len(b) - 1)}
    if not bigrams_a or not bigrams_b:
        return 0.0
    return len(bigrams_a & bigrams_b) / min(len(bigrams_a), len(bigrams_b))


def is_same_shop_variant(url_a: str, url_b: str) -> bool:
    """同じショップで商品コードが型番違い（例: glove001とglove002）なら同一商品扱いにする。"""
    match_a = ITEM_URL_PATTERN.match(url_a)
    match_b = ITEM_URL_PATTERN.match(url_b)
    if not match_a or not match_b:
        return False
    shop_a, slug_a = match_a.group(1).lower(), match_a.group(2).lower()
    shop_b, slug_b = match_b.group(1).lower(), match_b.group(2).lower()
    if shop_a != shop_b:
        return False
    if slug_a == slug_b:
        return True
    base_a = TRAILING_DIGITS_PATTERN.sub("", slug_a)
    base_b = TRAILING_DIGITS_PATTERN.sub("", slug_b)
    return bool(base_a) and base_a == base_b


def is_duplicate_product(
    url: str,
    text: str,
    existing: list[tuple[str, str]],
    threshold: float = SIMILARITY_THRESHOLD,
) -> bool:
    """既存の(URL, 商品名/紹介文)一覧と照合し、同一とみられる商品ならTrue。"""
    for existing_url, existing_text in existing:
        if is_same_shop_variant(url, existing_url):
            return True
        if text and existing_text and product_similarity(text, existing_text) >= threshold:
            return True
    return False


def build_description(title: str, index: int, max_chars: int = 180) -> str:
    """商品タイトルからテンプレートベースの紹介文を作る。indexで文面をローテーションする。"""
    name = clean_item_title(title)
    if contains_exaggerated_claim(name):
        name = FALLBACK_NAME
    template = DESCRIPTION_TEMPLATES[index % len(DESCRIPTION_TEMPLATES)]
    return template.format(name=name)[:max_chars]


def _pick(patterns: list[str], key: str, salt: str) -> str:
    digest = hashlib.md5(f"{salt}:{key}".encode()).digest()
    return patterns[digest[0] % len(patterns)]


def build_varied_description(
    title: str,
    *,
    review_count: int = 0,
    review_average: float = 0.0,
    surge: bool = False,
    key: str = "",
    max_chars: int = 180,
) -> str:
    """商品ごとに文面パターンを変えた紹介文を作る(公式APIベースの補充用)。

    keyのハッシュでパターンを固定するので、同じ商品には常に同じ文が生成される。
    レビュー件数・評価は取得時点のAPI値をそのまま使う(事実ベース)。
    """
    name = clean_item_title(title)
    if contains_exaggerated_claim(name):
        name = FALLBACK_NAME
    key = key or name

    openers = VARIED_SURGE_OPENERS if surge else VARIED_OPENERS
    parts = [_pick(openers, key, "opener").format(name=name)]
    if review_count >= 100 and review_average:
        parts.append(
            _pick(VARIED_REVIEW_SENTENCES, key, "review").format(
                count=f"{review_count:,}", avg=review_average
            )
        )
    parts.append(_pick(VARIED_CLOSERS, key, "closer"))
    return "".join(parts)[:max_chars]
