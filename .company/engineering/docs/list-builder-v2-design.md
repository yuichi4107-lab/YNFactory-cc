# list_builder v2 設計書

- **作成日**: 2026-05-04
- **設計者**: executor (Claude Sonnet 4.6)
- **対象ファイル**: `/opt/sales-ops/src/tracks/c_outbound/list_builder.py`
- **依存**: 工程1（DBスキーマ拡張）完了済み前提

---

## 1. 既存コード分析（v1）

### ファイル構成

`/opt/sales-ops/src/tracks/c_outbound/list_builder.py`

### 現行の設計

**対象セグメント**: `t2_pro_service`（士業・制作会社）
**検索クエリ**: 10種（税理士・社労士・行政書士・司法書士・弁護士・会計事務所・ウェブ制作・デザイン事務所・広告代理店・コンサルティング会社）
**APIクライアント**: Google Places API (New) / Text Search エンドポイント
**挿入ロジック**:
```python
INSERT INTO companies (source, segment, company_name, website_url, location, industry)
VALUES ('google_maps', 't2_pro_service', ?, ?, ?, ?)
```
**重複防止**: `website_url` の UNIQUE 制約による `INSERT` エラーキャッチ
**フィルタなし**: 現状では地域・規模フィルタが存在しない

### 現行の問題点

1. 首都圏企業が混入する（検索ロケーション次第）
2. 従業員数の推定ロジックがない
3. `is_metro` フラグが自動セットされない
4. `prefecture` カラムへの格納が不完全（address からのparse不要）
5. AI/IT系企業の除外ロジックがない
6. セグメント `t1_sme` への対応がない（地方中小企業一般）

---

## 2. v2 設計方針

### ターゲット変更

| 項目 | v1 | v2 |
|---|---|---|
| セグメント | `t2_pro_service`（士業のみ） | `t1_sme`（地方中小企業一般）に追加 |
| 対象地域 | 指定なし（全国） | 非首都圏（東京都・大阪府・愛知県・福岡県を除外） |
| 従業員規模 | フィルタなし | 30〜100名（推定値でフィルタ） |
| 除外業種 | なし | AI/IT系・フランチャイズ大手 |

### ソース優先順位

1. **a5 Google Maps API** — 即実装可能。公式API。先行稼働推奨
2. **a4 商工会議所名簿** — 条件付きOK。実装は Phase 2 で対応
3. **a3 採用媒体** — 全サービスで NG 判定。実装しない

---

## 3. v2 実装設計

### 3.1 地方フィルタ（非首都圏フィルタ）

**除外都道府県**: 東京都・大阪府・愛知県・福岡県

```python
METRO_PREFECTURES = {
    "東京都", "大阪府", "愛知県", "福岡県",
    # 準首都圏（フィルタ対象外だが将来拡張用にコメント）
    # "神奈川県", "埼玉県", "千葉県", "京都府", "兵庫県",
}

def is_metro(prefecture: str | None) -> bool:
    """都道府県名が首都圏に該当するか判定する。"""
    if not prefecture:
        return False
    return prefecture in METRO_PREFECTURES
```

**Places API での地域指定戦略**:
- 検索時に `locationBias` で非首都圏の都市座標を指定することで効率化
- 推奨都市座標リスト（30都市程度を順番にローテーション）:

```python
TARGET_CITIES = [
    # 東北
    ("仙台市", (38.2682, 140.8694)),
    ("盛岡市", (39.7036, 141.1527)),
    ("山形市", (38.2404, 140.3633)),
    # 北陸
    ("金沢市", (36.5613, 136.6562)),
    ("富山市", (36.6953, 137.2113)),
    ("福井市", (36.0652, 136.2214)),
    # 甲信越
    ("長野市", (36.6485, 138.1949)),
    ("新潟市", (37.9026, 139.0232)),
    ("甲府市", (35.6635, 138.5686)),
    # 関東（非首都圏）
    ("水戸市", (36.3418, 140.4468)),
    ("宇都宮市", (36.5546, 139.8829)),
    ("前橋市", (36.3895, 139.0631)),
    # 東海（愛知除く）
    ("静岡市", (34.9756, 138.3828)),
    ("浜松市", (34.7108, 137.7261)),
    ("岐阜市", (35.4232, 136.7608)),
    # 近畿（大阪除く）
    ("神戸市", (34.6913, 135.1830)),
    ("奈良市", (34.6851, 135.8048)),
    ("和歌山市", (34.2306, 135.1708)),
    # 中国
    ("広島市", (34.3853, 132.4553)),
    ("岡山市", (34.6617, 133.9346)),
    ("山口市", (34.1858, 131.4706)),
    # 四国
    ("松山市", (33.8395, 132.7657)),
    ("高松市", (34.3401, 134.0434)),
    ("高知市", (33.5597, 133.5311)),
    # 九州（福岡除く）
    ("熊本市", (32.8031, 130.7079)),
    ("鹿児島市", (31.5966, 130.5571)),
    ("長崎市", (32.7448, 129.8736)),
    ("大分市", (33.2382, 131.6126)),
    ("宮崎市", (31.9077, 131.4202)),
    ("那覇市", (26.2124, 127.6809)),
]
```

### 3.2 業種絞り込み（AI/IT系除外）

```python
# AI活用アドバイザーのターゲット向け検索クエリ
T1_SME_SEARCH_QUERIES = [
    # 製造業
    "製造業 中小企業",
    "工場 地域企業",
    # サービス業
    "介護施設 有料老人ホーム",
    "建設会社 工務店",
    "物流会社 運送業",
    "小売店 地域スーパー",
    "飲食チェーン 地域",
    # 専門サービス
    "税理士事務所",
    "社労士事務所",
    "行政書士事務所",
    "コンサルティング会社",
]

# 除外: AI/IT系・フランチャイズ大手のキーワード
EXCLUDE_KEYWORDS = {
    "ai", "人工知能", "機械学習", "システム開発", "ソフトウェア",
    "it企業", "saas", "クラウド", "フランチャイズ", "fc",
    "マクドナルド", "セブンイレブン", "ローソン", "ファミリーマート",
}

def is_excluded_industry(industry: str, company_name: str) -> bool:
    """AI/IT系またはフランチャイズ大手を除外する。"""
    combined = (industry + " " + company_name).lower()
    return any(kw in combined for kw in EXCLUDE_KEYWORDS)
```

### 3.3 規模推定ロジック（Claude API連携）

**目的**: Google Maps APIが従業員数を提供しないため、HPコンテンツからAIで推定する

**推定フロー**:
```
会社URL → HP取得（requests） → Claude API → 規模推定（30-100名 / それ以外）
```

**Claude API プロンプト設計**:

```python
EMPLOYEE_ESTIMATE_PROMPT = """
あなたは企業規模推定の専門家です。
以下の企業ホームページの文章から、この会社の従業員数を推定してください。

企業名: {company_name}
HP内容（先頭2000文字）:
{hp_text}

以下のJSON形式で回答してください：
{{
  "estimated_employees": <数値または null>,
  "confidence": "high" | "medium" | "low",
  "reason": "<推定根拠の説明>",
  "in_target_range": <true（30-100名）| false | null（判定不能）>
}}

推定根拠となる情報例：
- 「従業員数: XX名」「スタッフ数: XX人」などの直接記載
- 拠点数・部署数からの推測
- 「創業XX年、老舗」など規模を示唆する表現
- 求人情報での部署構成

判定不能な場合は estimated_employees を null にしてください。
"""
```

**実装クラス設計**:

```python
class EmployeeSizeEstimator:
    """HPテキストからClaude APIで従業員数を推定する。"""
    
    def __init__(self, anthropic_client, model: str = "claude-haiku-4-5"):
        self.client = anthropic_client
        self.model = model
    
    def estimate(self, company_name: str, website_url: str) -> dict:
        """
        Returns:
            {
                "estimated_employees": int | None,
                "confidence": str,
                "in_target_range": bool | None,
            }
        """
        hp_text = self._fetch_hp_text(website_url)
        if not hp_text:
            return {"estimated_employees": None, "confidence": "low", "in_target_range": None}
        
        # Claude Haiku で低コスト推定（50〜100トークン程度）
        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": EMPLOYEE_ESTIMATE_PROMPT.format(
                    company_name=company_name,
                    hp_text=hp_text[:2000]
                )
            }]
        )
        return self._parse_response(response.content[0].text)
    
    def _fetch_hp_text(self, url: str, timeout: int = 10) -> str | None:
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            # HTMLタグを除去してテキスト抽出
            from html.parser import HTMLParser
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.texts = []
                def handle_data(self, data):
                    self.texts.append(data)
            parser = TextExtractor()
            parser.feed(r.text)
            return " ".join(parser.texts)[:3000]
        except Exception:
            return None
    
    def _parse_response(self, text: str) -> dict:
        import json, re
        try:
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return {"estimated_employees": None, "confidence": "low", "in_target_range": None}
```

### 3.4 `is_metro` 自動セット・`prefecture` 格納

```python
def extract_prefecture(formatted_address: str) -> str | None:
    """Google Maps のformattedAddressから都道府県を抽出する。"""
    import re
    # 日本の都道府県パターン
    pattern = r'(北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|' \
              r'埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|' \
              r'岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|' \
              r'鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|' \
              r'佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)'
    m = re.search(pattern, formatted_address)
    return m.group(1) if m else None
```

### 3.5 v2 ListBuilder クラス設計（全体）

```python
class ListBuilderV2:
    """
    v2: 非首都圏フィルタ・規模フィルタ・AI推定を組み込んだリストビルダー。
    """
    
    # 従業員数フィルタ
    MIN_EMPLOYEES = 30
    MAX_EMPLOYEES = 100
    
    def __init__(
        self,
        db: Database,
        places_client: PlacesClient,
        size_estimator: EmployeeSizeEstimator | None = None,
        dry_run: bool = False,
    ):
        self.db = db
        self.places = places_client
        self.size_estimator = size_estimator
        self.dry_run = dry_run
    
    def fetch_t1_sme(
        self,
        *,
        query: str,
        city: str,
        location: tuple[float, float],
        max_results: int = 20,
        radius_m: int = 5000,
    ) -> int:
        """非首都圏の中小企業を検索してDBに格納する。"""
        results = self.places.search_text(
            query=query, location=location, radius_m=radius_m
        )
        
        inserted = 0
        for place in results[:max_results]:
            website = place.get("website")
            if not website:
                continue
            
            address = place.get("formatted_address", "")
            prefecture = extract_prefecture(address)
            
            # 1. 非首都圏フィルタ
            if is_metro(prefecture):
                logger.debug("skip metro: %s (%s)", place.get("name"), prefecture)
                continue
            
            # 2. AI/IT系除外
            industry = self._infer_industry(place.get("types", []))
            if is_excluded_industry(industry, place.get("name", "")):
                logger.debug("skip excluded industry: %s", place.get("name"))
                continue
            
            # 3. 規模推定（estimator がある場合のみ）
            size_estimated = None
            in_target_range = None
            if self.size_estimator:
                result = self.size_estimator.estimate(place.get("name", ""), website)
                size_estimated = result.get("estimated_employees")
                in_target_range = result.get("in_target_range")
                # 推定できた場合のみフィルタを適用
                if in_target_range is False:
                    logger.debug(
                        "skip size out of range: %s (est=%s)",
                        place.get("name"), size_estimated
                    )
                    continue
            
            # 4. DB格納
            if not self.dry_run:
                if self._insert(
                    name=place.get("name", ""),
                    website=website,
                    address=address,
                    industry=industry,
                    prefecture=prefecture,
                    is_metro_flag=is_metro(prefecture),
                    size_estimated=size_estimated,
                ):
                    inserted += 1
            else:
                logger.info("[DRY_RUN] would insert: %s (%s)", place.get("name"), prefecture)
                inserted += 1
        
        logger.info(
            "fetch_t1_sme: city=%s query=%s inserted=%d/%d",
            city, query, inserted, len(results)
        )
        return inserted
    
    def _insert(
        self,
        *,
        name: str,
        website: str,
        address: str,
        industry: str,
        prefecture: str | None,
        is_metro_flag: bool,
        size_estimated: int | None,
    ) -> bool:
        try:
            with self.db.connect() as conn:
                conn.execute(
                    """INSERT INTO companies
                       (source, segment, company_name, website_url, location,
                        industry, prefecture, is_metro, size_employees_estimated)
                       VALUES ('google_maps', 't1_sme', ?, ?, ?, ?, ?, ?, ?)""",
                    (name, website, address, industry,
                     prefecture, int(is_metro_flag), size_estimated),
                )
            return True
        except Exception as e:
            if "UNIQUE" in str(e):
                return False
            raise
    
    @staticmethod
    def _infer_industry(types: list[str]) -> str:
        types_set = set(types)
        if "lawyer" in types_set:
            return "lawyer"
        if "accounting" in types_set:
            return "accounting"
        if "doctor" in types_set:
            return "medical"
        if "restaurant" in types_set or "food" in types_set:
            return "food_service"
        if "store" in types_set or "shop" in types_set:
            return "retail"
        return ",".join(sorted(types_set))[:200]
```

---

## 4. run_list_builder.py への組み込み方針

`/opt/sales-ops/run_list_builder.py`（工程7で改修）で以下のように使用:

```python
# 環境変数
DRY_RUN = os.environ.get("SALES_OPS_DRY_RUN", "false").lower() == "true"
CITIES_PER_RUN = 3  # 1回の実行で3都市分を処理
TARGET_PER_CITY = 20  # 1都市あたり最大20社

# ローテーション: 都市リストをシャッフルして毎回異なる都市をカバー
import random
selected_cities = random.sample(TARGET_CITIES, CITIES_PER_RUN)

for city_name, location in selected_cities:
    for query in T1_SME_SEARCH_QUERIES[:3]:  # 1都市あたり3クエリ
        builder_v2.fetch_t1_sme(
            query=query,
            city=city_name,
            location=location,
            max_results=TARGET_PER_CITY,
        )
```

**1回実行あたりの想定取得数**: 3都市 × 3クエリ × 最大20件 = 最大180件（フィルタ後20〜50件程度が想定）

---

## 5. テスト設計

### dryrun テスト手順

```bash
# VPS上での実行
cd /opt/sales-ops
SALES_OPS_DRY_RUN=true python3 run_list_builder.py
```

**期待結果**:
- DBに実際の INSERT が行われないこと
- ログに `[DRY_RUN] would insert: <企業名> (<都道府県>)` が出力されること
- 首都圏企業が `skip metro` でフィルタされること
- 20社以上の候補が出力されること

### ユニットテスト追加項目

```python
# test_list_builder_v2.py

def test_metro_filter_excludes_tokyo():
    """東京都の企業がフィルタされること"""
    
def test_metro_filter_allows_sendai():
    """仙台市（宮城県）の企業が通過すること"""
    
def test_industry_exclusion():
    """AI/IT系キーワードが除外されること"""
    
def test_employee_range_filter():
    """推定従業員数が範囲外の場合にスキップされること"""
    
def test_duplicate_prevention():
    """同一URLの企業が重複挿入されないこと"""
    
def test_dry_run_no_insert():
    """dryrunモードでDBに書き込まれないこと"""
```

---

## 6. 変更ファイル一覧（工程7で適用）

| ファイル | 変更内容 |
|---|---|
| `/opt/sales-ops/src/tracks/c_outbound/list_builder.py` | `ListBuilderV2` クラスを追加。既存 `ListBuilder` は残存（後方互換） |
| `/opt/sales-ops/run_list_builder.py` | `ListBuilderV2` を使用するよう切り替え |
| `/opt/sales-ops/tests/test_list_builder_v2.py` | 新規テストファイル |

---

## 7. 未解決事項・判断依頼

1. **サイズ推定の必須化**: Claude API コストが発生する（1社あたり約0.01〜0.05円）。50社/日なら月150〜1,500円程度。コストを承認するか確認が必要
2. **初回実装スコープ**: size_estimator を外して `is_metro` フィルタのみ先行実装するか、フル実装するか
3. **商工会議所(a4)のスクレイピング実装**: 法的に条件付きOKだが、実装工数がかかる。a5（Google Maps）が安定したら Phase 2 で着手推奨
