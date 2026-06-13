# LAUNCH_CHECKLIST.md — 高単価AIコンサル Sales OS 起動計画

- **作成日**: 2026-06-09
- **バージョン**: 1.1（実コード検証済み）
- **工程**: 工程2（起動計画）の成果物
- **参照元**: `.company/requirements/sales-system-2026-06/REQUIREMENTS.md`
- **前提**: 工程1の成果物 `.company/sales/STRATEGY.md` が完成済みであること

> **このファイルの位置づけ**:
> 「このファイルだけ見れば、オーナーが画面操作レベルで実行できる」完全ガイド。
> 5週間休眠中のSales OSを本番稼働させるための全手順を網羅している。
> 上から順に実行すれば、合計 **2〜3時間** でウェビナー・Calendly・本番DM送信が揃う。
>
> **v1.1 修正点**: コード実装（db.py/gmail_sender.py/config.py/personalizer.py）を実際に読んで
> コマンド・SQL・URLの反映経路をすべて実コードで裏取りした。

---

## 最初の1時間でやること（最優先アクション）

5週間の休眠を終わらせるために、**この順番で1時間以内に完了させる**。

| 優先順 | アクション | 所要時間 | 担当 | 完了判定 |
|---|---|---|---|---|
| 1 | From問題の方針確定（案Cで即決推奨） | 5分 | オーナー判断 | 方針を決めた |
| 2 | Peatixイベント作成・公開 | 20分 | オーナー手動 | 公開URLが発行された |
| 3 | CalendlyイベントタイプとZoom連携 | 15分 | オーナー手動 | 予約URLが発行された |
| 4 | DMテンプレートにウェビナーURLを直書き + VPS反映 | 10分 | オーナー手動 | URLが確認できた |
| 5 | 自分宛テスト送信 1通（本番送信GO確認） | 20分 | オーナー+Claude支援 | info@yn-factory.comに届いた |

**重要ルール**: 「完璧な準備」を待たない。案Cで今日中に送信する。
From問題が気になっても、送信ゼロの期間が続く方が損失大。

---

## Part 1. From表示問題の解決方針

### 現状

| 項目 | 現状 |
|---|---|
| From（送信者アドレス） | `yuichi4107@gmail.com` |
| Reply-To | `info@yn-factory.com`（.envの`GMAIL_REPLY_TO`で設定済み） |
| 署名内の連絡先 | `info@yn-factory.com` |
| 特電法フッター | `gmail_sender.py`で自動付与（全件確認済み） |

---

### 3案の評価と推奨

| 案 | 方法 | Fromの見え方 | 難易度 | 推奨度 |
|---|---|---|---|---|
| **案C: そのまま運用** | 変更なし。今すぐ動く | `yuichi4107@gmail.com` | ★（即可） | **今すぐ実施** |
| 案A: Gmailエイリアス設定 | Gmail「Send mail as」でinfo@登録 | `info@yn-factory.com` | ★★★（前回535エラー。原因は下記） | 案C稼働後に並行試行 |
| 案B: Workspace OAuth | y-nakada@yn-factory.com 認証・token差し替え | `info@yn-factory.com` | ★★★★（前回ブラウザエラー未特定） | 案A失敗後に試行 |

---

### 推奨: 今すぐ案Cで開始し、並行して案A→Bを試す

Reply-ToとDM本文の連絡先は `info@yn-factory.com` で統一されているため、
受信者が返信すれば正しく `info@yn-factory.com` に届く。
From表示が `gmail.com` であることの実害は小さい。

---

### 案C: そのまま運用（今すぐ実施）

変更は不要。現状の `.env` 設定のまま `run_send_approved.py` を実行するだけで送信できる。

確認のみ行う:

```bash
# VPSにSSH接続してFromアドレスを確認
ssh yn-vps "grep -E 'GMAIL_SENDER_ADDRESS|GMAIL_REPLY_TO|SALES_OPS_DRY_RUN' /opt/sales-ops/.env"
```

期待される出力:
```
GMAIL_SENDER_ADDRESS=yuichi4107@gmail.com
GMAIL_REPLY_TO=info@yn-factory.com
SALES_OPS_DRY_RUN=true    ← Part 2 でfalseに変える
```

---

### 案A: Gmailエイリアス設定（案Cと並行して試行）

**所要時間**: 約30分（成功すれば）

**前回535エラーの真の原因と対処**:

535エラーは「SMTPパスワードが間違っている」エラー。Gmailでは通常パスワードでのSMTP認証は無効化されており、**アプリパスワード**が必要。
アプリパスワードは **2段階認証が有効なアカウントでのみ発行可能**。

> 注意: Google Workspace Admin での「IMAP有効化」はSMTP送信の535エラーとは無関係。

**STEP 1: Workspaceアカウントで2段階認証を有効化**（約5分）

1. `y-nakada@yn-factory.com` でGoogleアカウントにログイン
2. `https://myaccount.google.com/signinoptions/two-step-verification` を開く
3. 「使ってみる」をクリックして2段階認証を有効化する

**STEP 2: アプリパスワードを発行**（約3分）

1. `https://myaccount.google.com/apppasswords` を開く（2段階認証が有効でないと表示されない）
2. 「アプリを選択」→「その他（カスタム名）」→「Sales OS Gmail alias」と入力
3. 「生成」をクリック → 16桁のパスワードが表示される
4. このパスワードをメモ（一度しか表示されない）

**STEP 3: Gmail「Send mail as」エイリアス設定**（約10分）

1. `yuichi4107@gmail.com` の Gmail を開く（`https://mail.google.com`）
2. 右上の歯車アイコン → 「すべての設定を表示」
3. 「アカウントとインポート」タブ → 「他のメールアドレスでメールを送信」
4. 「メールアドレスを追加」をクリック
5. 以下を入力:
   - 名前: `YNファクトリー 代表 中田雄一`
   - メールアドレス: `info@yn-factory.com`
6. 「次のステップ」をクリック
7. SMTPサーバー設定:
   - SMTPサーバー: `smtp.gmail.com`
   - ポート: `587`（推奨。TLS/STARTTLS）。587が通らない場合は代替として`465`（SSL）も可
   - ユーザー名: `y-nakada@yn-factory.com`
   - パスワード: STEP 2で発行した16桁のアプリパスワード
8. 「アカウントを追加」をクリック

**STEP 4: 確認メールを認証**

Gmail が `info@yn-factory.com`（= `y-nakada@yn-factory.com` Workspace）に確認メールを送信する。
`y-nakada@yn-factory.com` の受信トレイを確認してリンクをクリックして認証完了。

**STEP 5: Gmailの「Send mail as」で info@ を既定の差出人に設定**（任意）

「アカウントとインポート」→「デフォルトとして使用」で `info@yn-factory.com` を選択。

> 案Aが成功しても、`run_send_approved.py` は `.env` の `GMAIL_SENDER_ADDRESS` でFromを決める。
> Gmail側でエイリアスを設定しても、VPSのコードは変わらない。
> **案A成功後に必要な追加作業**: VPS `.env` の `GMAIL_SENDER_ADDRESS` を `info@yn-factory.com` に変更すること。
> ただし Gmail OAuth token は `yuichi4107@gmail.com` で認証済みのため、
> `info@yn-factory.com` でのOAuth認証には案Bが必要になる点に注意。

---

### 案B: Workspace OAuth 再挑戦（案A失敗後に試行）

**所要時間**: 約45分

VPSのコード（`run_send_approved.py`）は `gmail_oauth_token_json` のtokenファイルを使ってGmailにアクセスする。
このtokenを `y-nakada@yn-factory.com` で再認証することでFromを変更できる。

**前回のブラウザエラー原因の候補**:
- OAuth クライアントのリダイレクトURIに `http://localhost` が含まれていない
- `y-nakada@yn-factory.com` がOAuth同意画面のテストユーザーリストに未登録
- スコープが不足（`gmail.send` のみで足りているはず）

**STEP 1: Google Cloud Console でOAuthクライアントを確認**

1. `https://console.cloud.google.com` を開く（yn-toolsプロジェクト）
2. 「APIとサービス」→「認証情報」→ 既存のOAuthクライアントを開く
3. 「承認済みのリダイレクトURI」に `http://localhost` があることを確認
   - なければ追加して「保存」
4. 「OAuth同意画面」→「テストユーザー」→ `y-nakada@yn-factory.com` が登録されているか確認
   - 未登録なら「ユーザーを追加」

**STEP 2: ローカルPCで認証実行**

```bash
# ローカルPC（Macターミナル）で実行
cd "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/sales-ops"
python scripts/gmail_oauth_setup.py
```

- ブラウザが開いたら `y-nakada@yn-factory.com` でログイン
- 「このアプリはGoogleによって確認されていません」警告が出たら「詳細」→「安全ではないページに移動」
- 「許可」をクリック
- ターミナルに `Token saved` が表示されれば成功

**STEP 3: tokenをVPSに転送**

```bash
scp "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc/sales-ops/secrets/gmail_token.json" yn-vps:/opt/sales-ops/secrets/
```

**STEP 4: VPS .env の GMAIL_SENDER_ADDRESS を更新**

```bash
ssh yn-vps "sed -i 's/GMAIL_SENDER_ADDRESS=yuichi4107@gmail.com/GMAIL_SENDER_ADDRESS=y-nakada@yn-factory.com/' /opt/sales-ops/.env"
# 確認
ssh yn-vps "grep GMAIL_SENDER_ADDRESS /opt/sales-ops/.env"
```

---

## Part 2. ウェビナーURL / CalendlyURLをDMに反映する方法

### 重要な事実: `.env` に書くだけではDMにURLが入らない

**コード確認結果（personalizer.py 15-46行 / config.py 全体）**:
- `WEBINAR_URL` / `CONSULT_BOOKING_URL` は `config.py` に読み込みコードが存在しない
- `personalizer.py` の `PROMPT_TEMPLATE` にウェビナーURL・CalendlyURLの差し込みはない
- `.env` に書いても自動でDMに入る仕組みは**現状未実装**

**DMテンプレートの実態**:
- `.company/sales/templates/ai-advisor-dm/dm_v1_human_resource.md` に `{{webinar_url}}` プレースホルダーが存在する
- しかし `personalizer.py` の `PROMPT_TEMPLATE` はこのファイルを読まずに**Claudeに直接プロンプトを送る**設計
- PersonalizerはClaudeが生成したJSON（subject/body）をそのまま `approval_queue` に投入する

**結論: URLはPersonalizerのプロンプトに直書きするのが唯一の確実な方法**

---

### 対処法: personalizer.pyのPROMPT_TEMPLATEにURLを直書きする

VPS上の `PROMPT_TEMPLATE`（`/opt/sales-ops/src/tracks/c_outbound/personalizer.py` の16行目付近）に
ウェビナーURLとCalendly URLを直接埋め込む。

**STEP 1: 現在のPROMPT_TEMPLATEを確認**

```bash
ssh yn-vps "grep -n 'webinar\|calendly\|booking\|ウェビナー\|無料' /opt/sales-ops/src/tracks/c_outbound/personalizer.py | head -20"
```

**STEP 2: プロンプトにURLを追加**

VPS上でファイルを編集する:

```bash
ssh yn-vps "nano /opt/sales-ops/src/tracks/c_outbound/personalizer.py"
```

`PROMPT_TEMPLATE` 内の制約4番（現在は「14日間の無料トライアル」の記述）を以下のように書き換える:

```python
# 変更前（personalizer.pyの34行目付近）
4. 最後に14日間の無料トライアル案内と30分オンラインデモ提案

# 変更後（Peatix URLとCalendly URLを決定した後に記入）
4. 最後に以下のウェビナー案内を必ず含める:
   無料ウェビナー「人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選」
   申込URL: https://peatix.com/event/（PeatixイベントID）
   個別相談予約URL: https://calendly.com/（CalendlyURL）/30min-consult
```

`Ctrl+X → Y → Enter` で保存。

**STEP 3: ローカルのpersonalizer.pyにも同じ変更を反映**（Git管理のため）

```bash
# ローカルのsales-ops/src/tracks/c_outbound/personalizer.py を同様に編集
# 変更後: git add + git commit
cd "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
git add sales-ops/src/tracks/c_outbound/personalizer.py
git commit -m "add webinar/calendly URLs to personalizer PROMPT_TEMPLATE"
```

---

### VPSへの反映方法（STEP 2 の編集後に必須）

DEPLOY.md に定められたデプロイ方式は **rsync**（git pull は使わない）。

**方法A: ローカル編集 → rsync でVPS反映（推奨）**

```bash
# Mac ターミナルで実行（ローカル編集後）
cd "/Users/yuichi/Library/CloudStorage/GoogleDrive-yuichi4107@gmail.com/マイドライブ/YNFactory-cc"
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='tests' \
  --exclude='.pytest_cache' --exclude='data' \
  sales-ops/ yn-vps:/opt/sales-ops/
```

成功すると VPS の `/opt/sales-ops/src/tracks/c_outbound/personalizer.py` が上書きされる。

確認:

```bash
ssh yn-vps "grep -A3 '無料のオンライン\|peatix\|calendly' /opt/sales-ops/src/tracks/c_outbound/personalizer.py | head -10"
```

追記したPeatix URL / Calendly URL が表示されればVPS反映完了。

**方法B: VPS上で直接 nano 編集（ローカル編集なしで即時対応したい場合）**

```bash
ssh yn-vps "nano /opt/sales-ops/src/tracks/c_outbound/personalizer.py"
# Ctrl+X → Y → Enter で保存
```

> **注意**: 方法BはVPS上のファイルだけ変わり、ローカルと乖離する。
> 後で方法Aの rsync を実行するとVPSの変更が上書き消去される。
> 方法Bで編集した場合は、ローカルの同ファイルにも必ず同じ変更を加えて git commit しておくこと。

---

**注意**: 既に `approval_queue` に入っている `pending` のDMには反映されない。
次回の cron（02:30 run_personalizer.py）が実行するときに新しいプロンプトが使われる。
既存pending分はURLなしのまま送るか、一旦 rejected にして再生成するかをオーナーが判断すること。

---

### 既存pendingのURL更新が急ぎの場合

既存のpendingデータを確認し、URLを手動で更新する:

```bash
# pending件数と内容の確認
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python -c \"
import sys, json
sys.path.insert(0, 'src')
from core.db import Database
from core.approval_queue import ApprovalQueue
import os
from dotenv import load_dotenv
load_dotenv()
db = Database(os.environ['SALES_OPS_DB_PATH'])
q = ApprovalQueue(db)
items = q.list_pending(track='c')
print(f'pending件数: {len(items)}')
for item in items[:3]:
    p = json.loads(item['payload_json'])
    print(f'  id={item[\"id\"]} subject={p.get(\"subject\",\"\")}')
\""
```

URLが入っていないpendingが多い場合は `/sales-briefing` スキルで目視確認してから承認するか、
stale pending を reject してpersonalizer再実行を待つのが安全。

---

## Part 3. 工程8b: 本番送信 GO 手順（最重要）

**前提（この手順を始める前に完了していること）**:
- [ ] Part 1 の方針確定（案Cで即決推奨）
- [ ] Part 2 のpersonalizer.py 更新（URLを直書き）
- [ ] Part 4 の Peatix公開URL取得済み
- [ ] Part 5 の Calendly公開URL取得済み
- [ ] `approval_queue` に `/sales-briefing` スキルで**5件以上確認・承認済み**であること
  （`status='approved'` の件が送信対象。承認せずに送信スクリプトを実行しても何も起きない）

---

### STEP 1: 既存テストデータの確認（約3分）

dryrun時のテストデータ（YNテスト株式会社 / queue_id=270）が残っている場合は
`/sales-briefing` スキルを実行すると一覧に表示される。
実際の送信対象に含めたくなければ `/sales-briefing` で「却下」を選択すればOK。
（`reject()` メソッドで `status='rejected'` になり送信対象から外れる）

---

### STEP 2: DRY_RUN を false に切り替える（約5分）

```bash
ssh yn-vps "nano /opt/sales-ops/.env"
```

以下の行を変更する:

```bash
# 変更前
SALES_OPS_DRY_RUN=true
SALES_OPS_DAILY_SEND_LIMIT=5

# 変更後（テスト送信用。1通だけ送る）
SALES_OPS_DRY_RUN=false
SALES_OPS_DAILY_SEND_LIMIT=1
```

`Ctrl+X → Y → Enter` で保存。

確認:

```bash
ssh yn-vps "grep -E 'DRY_RUN|DAILY_SEND_LIMIT' /opt/sales-ops/.env"
```

`SALES_OPS_DRY_RUN=false` と `SALES_OPS_DAILY_SEND_LIMIT=1` が表示されればOK。

---

### STEP 3: 自分宛テスト送信 1通（約5分）

**事前確認**: `approval_queue` に `status='approved'` のアイテムが存在することを確認する。

```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python -c \"
import sys, json
sys.path.insert(0, 'src')
from core.db import Database
from core.approval_queue import ApprovalQueue
import os
from dotenv import load_dotenv
load_dotenv()
db = Database(os.environ['SALES_OPS_DB_PATH'])
q = ApprovalQueue(db)
items = q.list_approved(track='c')
print(f'approved件数: {len(items)}')
\""
```

`approved件数: 0` の場合は、まず `/sales-briefing` スキルで pending を承認してから戻ること。

**送信実行**（DAILY_SEND_LIMIT=1 のため最初の1件だけ送られる）:

```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python scripts/run_send_approved.py"
```

成功時の出力:

```
[OK] sent 1 emails (dry_run=False)
```

---

### STEP 4: 受信確認（約5分）

`info@yn-factory.com`（= `y-nakada@yn-factory.com` Workspace）の受信トレイを確認。
または `yuichi4107@gmail.com` の送信済みトレイでも確認できる。

確認項目:

| 確認項目 | 合格条件 | つまずき時の対処 |
|---|---|---|
| [ ] メールが届いている | 受信トレイまたは迷惑メールに届く | 5分待ってもない → ログ確認（後述） |
| [ ] Fromアドレスの表示 | 案Cなら `YNファクトリー 代表 中田雄一 <yuichi4107@gmail.com>` | 案Cなら正常 |
| [ ] Reply-To | 返信先が `info@yn-factory.com` になっている | `.env` の GMAIL_REPLY_TO を確認 |
| [ ] 本文 | ウェビナーURL（Peatix）が実際のURLになっている | Part 2 の personalizer.py 更新を確認 |
| [ ] 特電法フッター | 送信者名・連絡先・配信停止URLが末尾に自動付与されている | `gmail_sender.py` の `build_raw_email` が自動付与するため通常は問題なし |

**ログで送信結果を確認**:

```bash
ssh yn-vps "tail -30 /var/log/sales-ops.log"
```

成功ログの例:

```
[INFO] Sending email to: xxx@xxx.jp
[OK] sent 1 emails (dry_run=False)
```

**送信記録をDBで確認**:

```bash
ssh yn-vps "cd /opt/sales-ops && ./venv/bin/python -c \"
import sys
sys.path.insert(0, 'src')
from core.db import Database
import os
from dotenv import load_dotenv
load_dotenv()
db = Database(os.environ['SALES_OPS_DB_PATH'])
with db.connect() as conn:
    rows = conn.execute('SELECT id, status, sent_at FROM approval_queue ORDER BY id DESC LIMIT 5').fetchall()
    for r in rows:
        print(dict(r))
\""
```

`status: sent` と `sent_at: 日時` が表示されれば送信記録が残っている。

> **注意**: `conversations` テーブルへの送信記録は現状コードでは書き込まれない（gmail_sender.py確認済み）。
> 送信の唯一の記録場所は `approval_queue.status='sent'` のみ。
> LAUNCH.md の「条件4: conversationsテーブルに残る」は現状コードでは達成されない。
> 将来的に送信履歴の追跡が必要な場合は `gmail_sender.py` の `_send_one()` メソッドに
> conversations INSERT処理の追加実装が必要。

---

### STEP 5: 段階的な送信数の引き上げ（確認OK後）

| フェーズ | DAILY_SEND_LIMIT | 引き上げタイミング | 判断基準 |
|---|---|---|---|
| テスト | 1 | 今すぐ（STEP 3） | 自分宛1通が正常に届いた |
| フェーズ1 | 5 | テスト確認OK直後 | 特電法・URL・Reply-Toに問題なし |
| フェーズ2 | 30 | 5通送信後3日間、スパム判定なし | Bounce率 < 5%、返信率 > 0 |
| フェーズ3 | 50 | フェーズ2から1週間後 | Bounce率 < 5% を維持 |
| フェーズ4 | 100 | フェーズ3から1週間後 | 週次レビューで問題なし |

**DAILY_SEND_LIMIT の変更方法**:

```bash
ssh yn-vps "nano /opt/sales-ops/.env"
# SALES_OPS_DAILY_SEND_LIMIT=5 ← 数字を変更
# Ctrl+X → Y → Enter で保存
```

確認:

```bash
ssh yn-vps "grep DAILY_SEND_LIMIT /opt/sales-ops/.env"
```

---

### ローンチ後の最初の48時間モニタリング

何を見れば「正常稼働」と判断できるかの基準:

| 確認項目 | 確認場所 | 正常の定義 | 異常の定義 |
|---|---|---|---|
| 送信ログ | `ssh yn-vps "tail -50 /var/log/sales-ops.log"` | `sent N emails` が出ている | `Exception` / `Error` が連続 |
| DBの送信記録 | `approval_queue.status='sent'`（上記確認コマンド） | 承認件数と送信件数が一致 | `status='failed'` が存在 |
| Gmail受信 | `info@yn-factory.com` 受信トレイ | 正常着信 | 届かない・迷惑メールに入る |
| Bounce通知 | `yuichi4107@gmail.com` 受信トレイ | Bounceメールがない | Bounceが5%超 |
| 返信 | `info@yn-factory.com` 受信トレイ | 100通に1〜3通の返信 | 0通/週が2週間継続 |
| Cronの動作 | `ssh yn-vps "grep -E 'drafted|OK' /var/log/sales-ops.log \| tail -5"` | 毎日02:00/02:30にログ出力 | 2日以上ログが出ない |

**正常稼働の定義（総合判定）**:
以下をすべて満たせば「正常稼働」:
- [ ] 送信ログにエラーなし（48時間）
- [ ] DBにsent記録が蓄積されている
- [ ] Bounce率 < 10%
- [ ] 自分宛テストメールが正常に届いた実績あり
- [ ] cron が02:00/02:30に動作している

---

## Part 4. 工程4b: ウェビナー実セットアップ（Peatix）

**所要時間**: 約20分
**参照元**: `.company/outputs/sales-content/webinar-platform/signup-form.md`

### 開催日の逆算スケジュール

KGI: 2026-07-15 までに1回開催。今日 2026-06-09 から逆算:

| マイルストーン | 日程 | 残り日数 |
|---|---|---|
| Peatixイベント公開 | **2026-06-09（今日中）** | 今日 |
| DM/SNSで告知開始 | 2026-06-09〜 | 今日から |
| 参加者リマインド開始 | 2026-06-30 | 21日後 |
| ウェビナー申込締切 | 2026-07-12 | 33日後 |
| 第1回ウェビナー開催 | **2026-07-15（水）19:00** | 36日後 |

> 告知期間が6週間あればベストだが、3〜4週間でも5名以上の集客は可能。
> 絶対に「今日中にPeatix公開」することが最優先。

---

### STEP 1: Peatixアカウントの確認・作成（約3分）

1. `https://peatix.com` を開く
2. 「ログイン」をクリック
3. Google アカウント（`y-nakada@yn-factory.com`）でログイン
4. アカウントが未作成の場合: 「新規登録」→ 名前:「YNファクトリー」、メール:`info@yn-factory.com` で登録

---

### STEP 2: イベント作成（約10分）

Peatix管理画面 `https://peatix.com/organizer/event` → 「イベントを作成」をクリック。

**基本情報**（以下をコピー＆ペースト）:

| 項目 | 設定値 |
|---|---|
| イベントタイトル | `【無料ウェビナー】人手不足に悩む地方中小企業のための、今すぐ使えるAI活用5選` |
| サブタイトル | `キャリアコンサルタント国家資格保持者が「AI＝人を活かす」視点で解説する90分` |
| 開催日時 | 2026年7月15日（水）19:00〜20:30 |
| 開催場所 | `オンライン（Zoom）※ 申込後にZoom URLをメールでお送りします` |
| カテゴリ | ビジネス > セミナー・勉強会 |
| タグ | `AI活用, 中小企業, 人手不足, 地方, DX` |

**チケット設定**:

| 種別 | 参加費 | 定員 |
|---|---|---|
| 一般参加（無料） | 0円 | 30名 |

**イベント本文**: `.company/outputs/sales-content/webinar-platform/signup-form.md` の
「イベント本文（コピー用）」セクションをそのままコピー＆ペースト。

---

### STEP 3: アンケート（事前ヒアリング）を追加（約3分）

「チケット購入時アンケート」で以下を追加:

| 質問文 | 種別 | 必須 |
|---|---|---|
| 会社名 | テキスト（一行） | 必須 |
| 業種 | 選択肢（製造業/建設業/小売業/飲食業/物流業/医療福祉/サービス業/その他） | 必須 |
| 従業員数 | 選択肢（10〜30名/31〜50名/51〜100名/101名以上） | 必須 |
| 都道府県 | テキスト（一行） | 必須 |
| 事前に聞きたいこと・現在の課題 | テキスト（複数行） | 任意 |

---

### STEP 4: 申込完了メールを設定（約3分）

「参加者へのメール」→「申込完了メール」の本文を
`.company/outputs/sales-content/webinar-platform/auto-emails/registration-confirmation.md`
からコピーして貼り付ける。

> ZoomミーティングURLは開催3日前までに作成し、前日リマインダーメールに含める。

---

### STEP 5: 公開設定・公開実行（約1分）

| 設定項目 | 推奨値 |
|---|---|
| 公開範囲 | 公開（全体に公開） |
| 検索許可 | オン |
| 申込締切 | 開催3日前（2026-07-12） |

「公開」ボタンをクリック → イベントURLが発行される。

**発行されたURLをメモ**:
```
Peatix URL = https://peatix.com/event/（発行されたイベントID）
```

このURLを Part 2 の `personalizer.py` 更新時に使用する。

---

### 完了判定チェックリスト（工程4b）

- [ ] Peatix公開URLが発行された
- [ ] イベントページが `https://peatix.com/event/（ID）` で表示される
- [ ] 自分でテスト申込して申込完了メールが届いた
- [ ] アンケート（業種・従業員数等）が申込フォームに表示される
- [ ] 開催日: 2026-07-15（水）19:00 が正しく設定されている

**つまずき時の代替**:
- Peatixへのログインができない → `info@yn-factory.com` で新規登録して対応
- 申込完了メールのZoom URLが未確定 → 「申込確認後にZoom URLをメールでお送りします」と本文に記載して公開を優先

---

## Part 5. 工程5b: Calendly実セットアップ

**所要時間**: 約15分
**参照元**: `.company/outputs/sales-content/calendly-setup/README.md`

---

### STEP 1: Calendlyにログイン（約2分）

1. `https://calendly.com` を開く
2. 「Log in」→ Google アカウントでログイン
   - 推奨: `y-nakada@yn-factory.com` または `yuichi4107@gmail.com`
3. アカウント未作成なら「Sign up」→ Google でサインアップ

---

### STEP 2: プロフィール設定（約3分）

右上アイコン → 「Account settings」→「Profile」タブ:

| 項目 | 設定値 |
|---|---|
| Name | YN Factory |
| Welcome message | `AIを活用して経営を加速させたい中小企業の経営者様へ。国家資格キャリアコンサルタントとして、人を活かすAI活用を一緒に考えます。` |

「Save changes」をクリック。

---

### STEP 3: イベントタイプ（予約枠）を作成（約5分）

1. ダッシュボード上部「+ New event type」をクリック
2. 「One-on-one」を選択 → 「Create」
3. 以下を設定:

| 項目 | 設定値 |
|---|---|
| Event name | `無料個別AI活用相談（30分）` |
| Duration | 30分 |
| Description | `キャリアコンサルタント国家資格保持のAI活用アドバイザーが、貴社の状況に合わせたAI活用のはじめの一歩を無料でご提案します。売り込みや勧誘は一切ありません。` |
| Availability | 平日 10:00-18:00 |
| URL slug | `30min-consult` |

---

### STEP 4: Zoom連携（約3分）

1. Event Type 編集画面 → 「Location」セクション
2. 「Zoom」を選択
3. 「Connect Zoom」をクリック → Zoomアカウント（`yuichi4107@gmail.com` に紐付いたZoom Pro）にOAuthログイン
4. 「承認」をクリック → 連携完了

確認: 予約が入ると Zoom ミーティングURLが自動生成されるようになる。

---

### STEP 5: 事前ヒアリング質問を追加（約2分）

Event Type 編集 → 「Invitee Questions」タブ → 「+ Add a question」で以下を追加:

| 質問文 | 種別 | 必須 |
|---|---|---|
| 会社名を教えてください | テキスト | 必須 |
| 業種を教えてください | テキスト | 必須 |
| 従業員数を教えてください | テキスト | 必須 |
| 都道府県（本社所在地） | テキスト | 必須 |
| 現在お困りのことや相談したいことがあればお聞かせください | テキスト（複数行） | 任意 |

---

### STEP 6: 公開URLを確認・コピー（約1分）

1. ダッシュボード → 作成したイベントタイプの「Share」ボタン
2. URLをコピー（例: `https://calendly.com/yn-factory/30min-consult`）

**発行されたURLをメモ**:
```
Calendly URL = https://calendly.com/（ユーザーID）/30min-consult
```

このURLを Part 2 の `personalizer.py` 更新時に使用する。

---

### STEP 7: テスト予約（約5分）

発行されたURLに別のブラウザ（またはシークレットモード）からアクセスして自分でテスト予約を実施:

- [ ] 予約ページが正常に表示される
- [ ] 日時選択ができる
- [ ] 事前ヒアリング質問が表示される
- [ ] 予約完了後に申込者メール（確認メール）が届く
- [ ] オーナーのGmailに新規予約通知が届く
- [ ] Zoom URLが確認メールに含まれている

---

### 完了判定チェックリスト（工程5b）

- [ ] CalendlyのイベントタイプURLが発行された（`https://calendly.com/xxx/30min-consult`）
- [ ] テスト予約でZoom URLが自動生成された
- [ ] 確認メールが届いた（Zoom URL含む）
- [ ] オーナーへの通知メールが届いた

**つまずき時の代替**:
- Zoom連携がうまくいかない → 「Zoom URL: 別途ご連絡します」と設定して予約システムだけ先に稼働させる
- Cal.comへの切り替え → Calendlyが使えない場合は `https://cal.com` で同様の手順で設定可能

---

## Part 6. LAUNCH.md との整合性チェック（工程8完了条件）

`.company/sales/LAUNCH.md` の「工程8 完了条件チェック」との対応:

| LAUNCH.md の完了条件 | このガイドの対応箇所 | 備考 |
|---|---|---|
| [x] dryrunで5社分の下書きがapproval_queueに生成 | 既完了（2026-05-04確認済み） | — |
| [ ] オーナーが5件の下書きを確認し文面品質・ターゲット適合性をレビュー | `/sales-briefing` スキルで承認前にレビュー | Part 3 STEP 3 の前提条件 |
| [ ] オーナーが承認した件数のDMが実際に Gmail 経由で送信（最低3件） | Part 3 STEP 3〜5 | DAILY_LIMIT=1で1通→その後5に引き上げ |
| [ ] 送信記録が `approval_queue.status = 'sent'` に残る | Part 3 STEP 4 の確認コマンド | conversationsテーブルは現状未記録（下記注意参照） |
| [ ] 送信ログに特電法表記が含まれている | `gmail_sender.py`の`build_raw_email`が自動付与 | 実受信メールで目視確認 |
| [ ] 本番 cron（02:00/02:30）が正常に動作している | Part 7 の48時間チェックリスト | cronは設定済み（2026-04-20確認） |

> **conversationsテーブルについて**: `gmail_sender.py` を実際に確認した結果、
> 送信時に `conversations` テーブルへのINSERTは**実装されていない**。
> 送信記録は `approval_queue.status='sent'` のみが現状の唯一の記録。
> LAUNCH.md 条件4の「conversationsテーブルに残る」は現コードでは達成不可。
> 将来的に追跡が必要なら `gmail_sender.py` の `_send_one()` メソッドへの追加実装が必要。

このガイドの全手順を完了すれば、LAUNCH.md の実現可能な全チェックボックスをチェックできる状態になる。

---

## 所要時間サマリー

| パート | 内容 | 所要時間 |
|---|---|---|
| Part 1 | From問題の方針確定（案Cで即決） | 5分 |
| Part 2 | personalizer.pyへのURL直書き | 10分 |
| Part 3 | 本番送信 GO（テスト→段階引き上げ） | 30分 |
| Part 4 | Peatix イベント作成・公開 | 20分 |
| Part 5 | Calendly セットアップ・公開URL取得 | 15分 |
| **合計（初日）** | | **約1時間20分** |

---

*作成: 2026-06-09 executor（工程2成果物）*
*v1.1 更新: 2026-06-09 実コード検証済み（db.py/gmail_sender.py/config.py/personalizer.py/run_send_approved.py）*
*参照: `.company/requirements/sales-system-2026-06/REQUIREMENTS.md` 工程2仕様*
*前提: `.company/sales/STRATEGY.md` 工程1成果物（完成済み）*
