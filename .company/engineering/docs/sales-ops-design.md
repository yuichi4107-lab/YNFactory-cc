# Sales OS（営業自律実行システム）設計書

- **作成日**: 2026-04-19
- **作成者**: 秘書室 + CEO（/company スキル経由）
- **ステータス**: 設計承認済み、実装前（writing-plans へ引き継ぎ）
- **オーナー承認**: 2026-04-19（ブレインストーム完了時点）

---

## 1. 背景と目的

### 1.1 背景
- オーナーの事業の中で営業活動が最も弱い領域として認識されている
- `.company/sales/` は2026-03-10に初期設定されたまま約40日間更新されていない
  - ココナラ: 3サービス出品済みだが閲覧数・反応チェック未実施
  - クラウドワークス: 1件応募のまま追加応募なし
  - ランサーズ: プロフィールのみで未着手
- PDCAが回っていないため、受注・収益が安定しない
- オーナーは複数プロジェクト（AI投資、ばんえい、電子書籍等）と並行しており、営業に割ける時間は平日2-3時間が上限

### 1.2 目的
「オーナーが毎日考えなくても営業オペレーションが自律的に回る仕組み」を構築する。

- **自律性**: 外部送信を除く全てをAI/自動化で実行
- **オーナーの関与**: 朝の承認（10-20分/日）のみ
- **3軸並行**: フリーランス案件獲得（A）、YNツール集客（B）、法人AIコンサル（C, **メイン**）

### 1.3 KGI（最上位目標）
- **2026-06-30時点で MRR 20万円**（軸Cメイン）
  - 内訳想定: yn-tools法人プラン 10社×2万 = 20万 / または AI顧問 2-3社

---

## 2. 決定事項サマリー

| 論点 | 決定 |
|---|---|
| 営業の軸 | 3軸並行、軸Cを拡大のメインエンジンとする |
| 自律化レベル | 全プロセスAI実行、外部送信のみP2（朝バッチ承認制） |
| 軸Cターゲット | T1（中小企業経営者）+ T2（士業・制作会社） |
| 実行エンジン | E3（VPS cron + Claude Code朝セッション ハイブリッド） |
| 軸Cオファー | O3（yn-tools法人プラン 月2万〜）フロント → O1（AI顧問 月5-10万）アップセル |
| アーキテクチャ | 案Y（Track別マイクロパイプライン） |

---

## 3. アーキテクチャ全体図

```
┌─────────────────────────────────────────────────────────────┐
│  VPS（ConoHa 163.44.101.31）                                 │
│  /opt/sales-ops/                                             │
│                                                              │
│  core/                                                       │
│    ├ kpi_aggregator.py    KPI集計                           │
│    ├ approval_queue.py    朝承認キュー管理                  │
│    ├ senders/             送信ドライバー                     │
│    │   ├ gmail_sender.py  Gmail API                         │
│    │   ├ cw_sender.py     CW応募送信（Playwright）          │
│    │   └ x_sender.py      X投稿                             │
│    └ db.py                共通SQLite（sales_ops.db）         │
│                                                              │
│  tracks/                                                     │
│    a_freelance/                                              │
│    │   ├ scanner.py                                          │
│    │   ├ scorer.py                                           │
│    │   └ drafter.py                                          │
│    b_content/                                                │
│    │   ├ planner.py                                          │
│    │   ├ drafter.py                                          │
│    │   └ kpi_tracker.py                                      │
│    c_outbound/                                               │
│        ├ list_builder.py（google_maps/biz_db fetcher）       │
│        ├ personalizer.py                                     │
│        ├ reply_watcher.py                                    │
│        └ deal_manager.py                                     │
│                                                              │
│  cron:                                                       │
│    00 2 * * *   tracks/a_freelance/scanner.py               │
│    30 2 * * *   tracks/a_freelance/scorer.py                │
│    00 3 * * *   tracks/c_outbound/list_builder.py           │
│    30 3 * * *   tracks/c_outbound/personalizer.py           │
│    */15 * * * * tracks/c_outbound/reply_watcher.py          │
│    00 23 * * *  core/kpi_aggregator.py                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Google Drive同期 (.company/配下のstate/)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  オーナーPC（Claude Code）                                   │
│                                                              │
│  Windows Task Scheduler: 平日07:30 起動                      │
│    ↓                                                         │
│  /sales-briefing スキル実行                                  │
│    ├ 前夜のスキャン・下書き結果をレビュー                   │
│    ├ 承認リスト提示（P2）                                   │
│    ├ オーナー承認 → VPS API に送信指示                      │
│    ├ DASHBOARD_SALES.md 更新                                │
│    └ 秘書がTelegramでサマリー通知                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 主要コンポーネント責務

### 4.1 core/（共通基盤）

| ファイル | 責務 | 入出力 |
|---|---|---|
| `core/db.py` | SQLite（sales_ops.db）スキーマ定義・接続管理 | — |
| `core/kpi_aggregator.py` | 日次でKPIを集計してMarkdownに出力 | DB → `DASHBOARD_SALES.md` |
| `core/approval_queue.py` | 朝承認キューの管理（pending/approved/rejected） | DB操作 |
| `core/senders/gmail_sender.py` | Gmail API経由でDM送信（1通/分、日次上限100通） | approved queue → Gmail |
| `core/senders/cw_sender.py` | クラウドワークス応募送信（Playwright） | approved queue → CW |
| `core/senders/x_sender.py` | X投稿（既存yn-toolsのX投稿ロジック流用） | approved queue → X |

### 4.2 tracks/a_freelance/

| ファイル | 責務 |
|---|---|
| `scanner.py` | CW・ランサーズ・ココナラの新着案件をスクレイピング取得、キーワードフィルタ、`jobs` テーブル追加 |
| `scorer.py` | Claude APIで案件を「応募価値」にスコアリング（単価・難易度・自分スキルマッチ） |
| `drafter.py` | トップ5件の応募文を下書き生成 → `approval_queue` にpending投入 |

### 4.3 tracks/b_content/

| ファイル | 責務 |
|---|---|
| `planner.py` | 週次でnote/X投稿の週間計画（テーマ7本）を生成 |
| `drafter.py` | 日次でその日の投稿下書き生成 → `approval_queue` にpending投入 |
| `kpi_tracker.py` | note閲覧数・X impressions・yn-tools LP流入・サブスクCV を追跡 |

### 4.4 tracks/c_outbound/（メイン）

| ファイル | 責務 |
|---|---|
| `list_builder.py` | 毎日50-100社の新規リスト取得（google_maps_fetcher.py でT2士業、biz_db_fetcher.py でT1中小企業） |
| `personalizer.py` | 各社HP/IR/公式SNSからパーソナライズ要素を抽出し、Claude APIでDM文面生成 |
| `reply_watcher.py` | Gmail INBOX を15分毎に監視、返信検知→Telegram通知→`conversations` テーブル記録 |
| `deal_manager.py` | lead → qualified → proposal → won/lost のステートマシン管理、ステータス遷移時に通知 |

### 4.5 /sales-briefing スキル（Claude Code側）

- 朝セッションで起動し、承認UIを提示
- 3軸の承認キューを統合表示（軸Cを先頭、A・Bを次に）
- オーナーが一括承認 or 個別承認 → VPS API（SSH経由 or HTTP）に送信指示
- 結果サマリーを `.company/DASHBOARD_SALES.md` に書き込み
- Telegramで秘書から「今日の承認分 N件送信完了」の事後通知

---

## 5. データモデル（sales_ops.db）

```sql
-- 共通
CREATE TABLE approval_queue (
    id INTEGER PRIMARY KEY,
    track TEXT CHECK(track IN ('a', 'b', 'c')),
    item_type TEXT,  -- 'cw_application', 'note_post', 'dm', 'x_post'
    payload_json TEXT,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected', 'sent', 'failed')),
    created_at TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP
);

-- 軸A
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    source TEXT CHECK(source IN ('cw', 'lancers', 'coconala')),
    job_url TEXT UNIQUE,
    title TEXT,
    budget_min INTEGER,
    budget_max INTEGER,
    description TEXT,
    score REAL,
    scored_at TIMESTAMP,
    created_at TIMESTAMP
);

-- 軸C
CREATE TABLE companies (
    id INTEGER PRIMARY KEY,
    source TEXT CHECK(source IN ('google_maps', 'biz_db', 'manual')),
    segment TEXT CHECK(segment IN ('t1_sme', 't2_pro_service')),
    company_name TEXT,
    website_url TEXT,
    contact_email TEXT,
    industry TEXT,
    size_employees INTEGER,
    hp_summary TEXT,
    personalization_hints TEXT,
    status TEXT DEFAULT 'new',
    created_at TIMESTAMP
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    direction TEXT CHECK(direction IN ('outbound', 'inbound')),
    subject TEXT,
    body TEXT,
    sent_at TIMESTAMP,
    received_at TIMESTAMP
);

CREATE TABLE deals (
    id INTEGER PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    stage TEXT CHECK(stage IN ('lead', 'qualified', 'proposal', 'won', 'lost')),
    offer TEXT,  -- 'o3_yntools', 'o1_consultant', etc.
    amount_yen INTEGER,
    stage_changed_at TIMESTAMP,
    created_at TIMESTAMP
);

-- KPI
CREATE TABLE daily_kpi (
    date DATE,
    track TEXT,
    metric TEXT,
    value REAL,
    PRIMARY KEY (date, track, metric)
);
```

---

## 6. 1日のタイムライン（軸C例）

| 時刻 | アクター | 処理 |
|---|---|---|
| 03:00 | VPS cron | `list_builder.py` → T2 40社 + T1 10社 = 50社 `companies` 追加 |
| 03:30 | VPS cron | `personalizer.py` → 50社の下書き `approval_queue` に pending投入 |
| 07:30 | PC Task Scheduler | Claude Code起動 → `/sales-briefing` 実行 |
| 07:30-07:50 | オーナー | 承認UIで下書きレビュー（通常10-20件承認） |
| 07:50 | VPS API | `core/senders/gmail_sender.py` → 承認分を1分間隔で順次送信 |
| 08:00-23:00 | VPS cron 15分毎 | `reply_watcher.py` → 返信があれば Telegram通知 |
| 返信時 | オーナー | Telegram通知を見て対応判断、Claude Codeで返信文生成→承認→送信 |
| 23:00 | VPS cron | `kpi_aggregator.py` → `DASHBOARD_SALES.md` 更新 |

---

## 7. KPIダッシュボード（`.company/DASHBOARD_SALES.md`）

```markdown
# Sales OS Dashboard — 2026-04-XX

## Track C（法人AIコンサル）- メイン
当月累計:
  リスト取得: 1,500社 (T1: 300 / T2: 1,200)
  DM送信: 300社
  開封: 180 (60.0%)
  返信: 12 (4.0%)
  商談化: 4 (1.3%)
  受注: 1社（O3 月2万）
MRR: 2.0万円  (目標 2026-06-30: 20万円)

## Track A（フリーランス）
当月累計:
  応募: 40件  結果待ち: 8  受注: 2  売上: 5万円

## Track B（YNツール集客）
当月累計:
  note投稿: 8本  X投稿: 30本
  yn-tools LP流入: 450  サブスク新規: 3件  MRR寄与: 0.6万円
```

---

## 8. フェーズ分け（段階実装）

### Phase 1（2週間）: 軸CのMVP
- `core/db.py`（スキーマ初期化）
- `tracks/c_outbound/list_builder.py`（Google Mapsのみ T2対応）
- `tracks/c_outbound/personalizer.py`
- `core/approval_queue.py`
- `core/senders/gmail_sender.py`
- `/sales-briefing` スキル（最小承認UI）
- **目標**: 朝承認→手動10社送信できる状態

### Phase 2（1週間）: 軸A・Bを最小実装で並走
- `tracks/a_freelance/{scanner, scorer, drafter}.py`（CWのみ先行）
- `tracks/b_content/{planner, drafter}.py`（note + X）
- `/sales-briefing` に3軸統合表示
- **目標**: 毎朝の承認リストに3軸全部が並ぶ

### Phase 3（1週間）: 自動化強化・受注パイプライン
- `tracks/c_outbound/reply_watcher.py`（Gmail監視 + Telegram通知）
- `tracks/c_outbound/deal_manager.py`（商談ステートマシン）
- `list_builder.py` に T1（biz_db）対応追加
- `core/senders/cw_sender.py`（Playwright応募自動化）
- `core/kpi_aggregator.py` + `DASHBOARD_SALES.md`
- **目標**: 返信→商談→受注の全パイプラインが動く

### Phase 4（継続）: 最適化
- DM A/Bテスト（件名・文面バリエーション）
- 反応率の高い業種・時間帯を特定
- リスト品質改善
- `tracks/a_freelance` にランサーズ・ココナラ追加

---

## 9. 安全装置・リスク対策

### 9.1 外部送信リスク
- **スパム判定回避**: 1通/分、日次上限100通、連続失敗3回で停止
- **誤送信防止**: 送信前に `{{変数名}}` の差込未処理を検知したらブロック
- **法令順守**: 特電法の表示義務（送信停止手続き記載、送信者名・連絡先）を全DMに自動挿入
- **重複送信防止**: `companies.status` で送信済みフラグ管理、同一ドメインへの再送を30日間ブロック

### 9.2 データ破損リスク
- **SQLiteはローカル配置**: `.company/`（Google Drive配下）には**置かない**（JP-DAYTRADEの教訓）
  - VPS: `/opt/sales-ops/data/sales_ops.db`
  - PC側が読む場合は別DBまたはVPS APIで取得
- 日次バックアップ: cron で `/var/backup/sales_ops_YYYYMMDD.db`

### 9.3 承認取りこぼしリスク
- 朝セッションで承認されなかった pending 項目は48時間後に自動 reject（鮮度切れ）
- 未承認のまま3日溜まったら Telegramでオーナーに警告

### 9.4 返信対応取りこぼしリスク
- reply_watcher が返信検知から24h以内にオーナーがTelegramに反応しない場合、秘書が再通知
- 重要度スコア（相手企業規模×文面積極性）で通知優先度決定

### 9.5 外部API依存リスク
- Google Maps API: 無料枠超過監視、超過時はT2のみに限定
- Claude API: レート制限リトライ、月次上限監視
- Gmail API: OAuth token期限監視、期限前アラート

---

## 10. テスト戦略

- **単体テスト**: 各モジュール pytest（既存 jp-daytrade パターン踏襲、カバレッジ70%目標）
- **統合テスト**: dry-runモード（`SALES_OPS_DRY_RUN=true` で送信せずDBに記録のみ）
- **本番最小検証**: Phase 1完了時、オーナー承認下で5社だけ本番送信し反応確認
- **回帰テスト**: 各Phase完了時、前Phaseの全テストが通ることを確認

---

## 11. 既存資産との連携

| 既存資産 | 連携方法 |
|---|---|
| yn-tools（31ツール、tools.ynfactory.online） | オファーO3の対象。DM文面にLP URLを自動挿入 |
| sales-automation/（Render稼働中） | 廃止を検討（管理者アカウント未作成で実質未稼働） |
| AYC / comicle-pipeline | 軸Bのコンテンツ生成で流用可能（将来） |
| keiba / ai-trade-system | 連携なし（独立） |
| Gmail（既存アカウント） | 軸C outbound送信で使用 |
| Telegram bot（既存） | 返信通知・完了報告で使用 |
| Windows Task Scheduler | 朝の Claude Code 自動起動 |
| ConoHa VPS cron | 深夜バッチ実行基盤 |

---

## 12. 完了条件

### 12.1 Phase別完了条件

| Phase | 完了条件 |
|---|---|
| Phase 1 | 朝承認 → 10社にDM送信できる。送信記録がDBに残る。特電法表記が自動挿入されている |
| Phase 2 | 3軸全部が毎朝の承認リストに並ぶ。承認→送信が各軸で動く |
| Phase 3 | 返信検知→Telegram通知→商談ステート遷移までつながる。KPIダッシュボード自動生成 |
| Phase 4（継続） | 月次で DM反応率・受注率の改善が記録される |

### 12.2 KGI（最上位目標）
- **2026-06-30時点で MRR 20万円**
  - 軸C: O3（yn-tools法人プラン）10社 × 2万 = 20万、または O1（AI顧問）2-3社
  - 進捗不足時は Phase 4 で戦略見直し（リスト刷新 / オファー変更 / 単価上げ）

---

## 13. 想定工数

| Phase | 工数見積 | 備考 |
|---|---|---|
| Phase 1 | 25-35h | 基盤構築含む、VPS初期セットアップ別途3-5h |
| Phase 2 | 15-20h | Phase 1の基盤流用で効率化 |
| Phase 3 | 15-20h | 商談管理・KPI集計 |
| Phase 4 | 継続的 | 月5-10h程度 |
| **合計（Phase 1-3）** | **55-75h + VPSセットアップ** | 平日2-3h/日想定で約4-6週間 |

---

## 14. 次のアクション

1. この設計書をオーナーレビュー → 承認
2. `writing-plans` スキルで Phase 1 の実装プランを作成
3. `pm/tickets/` に Phase 1 工程ごとのチケット生成
4. `executor` エージェントで工程1から実装開始
5. `quality-checker` で工程ごとに品質検証（85点以上で次工程へ）

---

## 付録A: オファー文面の骨子（軸C 初期版）

### O3（yn-tools法人プラン）DM初期骨子
```
件名: {{company_name}} 様 — AI業務自動化ツール31種類のご案内

{{recipient_name}} 様

はじめまして、YN Factory の {{owner_name}} と申します。
{{personalization_hint_1}} を拝見し、貴社の業務効率化に
お役立てできる可能性があると感じご連絡いたしました。

弊社では、中小企業・専門サービス業向けに
AI業務自動化ツール31種類を月額2,000円/ユーザーで
提供しております（tools.ynfactory.online）。

主な活用例:
・請求書・契約書ドラフト自動生成
・社内FAQチャットボット
・営業メール一括パーソナライズ
{{personalization_hint_2}}

14日間の無料トライアルをご案内できますので、
もしご興味がございましたら30分のオンライン説明会で
デモをお見せいたします。

--
{{owner_name}}
YN Factory
{{owner_email}} / {{website}}
※配信停止をご希望の場合は本メールにご返信ください
```

---

以上。
