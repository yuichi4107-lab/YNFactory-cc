# 要件定義書: yntools 管理者アカウント機能実装

作成日: 2026-04-29
対象プロジェクト: `yn-tools/` (FastAPI / ConoHa VPS / Docker / SQLite / Stripe)

---

## ゴール

`info@ynfactory.online` を永久無料のフル管理者として登録し、全ツールを課金バイパスで利用可能にしつつ、ユーザー一覧・課金履歴・ユーザー管理操作ができる管理者ダッシュボードを本番環境に反映する。

---

## スコープ

### やること

- `User.has_active_plan` / `User.has_full_access` プロパティに `is_admin` バイパスを追加
- `require_tool_access` 依存が admin を透過することの確認（`has_full_access` 経由で自動解決）
- `/admin` 配下の管理者ダッシュボード実装（ユーザー一覧・課金履歴サマリー・ユーザー詳細編集・強制ログアウト）
- `base.html` のアカウントメニューへ `is_admin` 限定の管理者ダッシュボードリンク追加
- `yn-tools/scripts/promote_admin.py` の作成（指定メールを `is_admin=True` にする冪等 CLI）
- `main.py` への admin router 登録
- 本番 VPS での `docker compose up -d --build` によるデプロイと DB 反映
- `info@ynfactory.online` の `is_admin` フラグを本番 DB で True に更新

### やらないこと

- Stripe 側の設定変更（webhook・商品設定等は一切触らない）
- 既存の課金フロー・プランロジック（`per_tool` / `all_tools` / トライアル等）の変更
- 独自パスワード認証の追加（Google OAuth のみ継続）
- 管理者の複数アカウント追加（今回は `info@ynfactory.online` 1名のみ）
- メール通知・Slack 通知等の外部連携
- ロールベースアクセス制御（RBAC）の多段階化（is_admin の二値フラグのみ）
- 管理者ダッシュボードの CSVエクスポート・高度な分析機能（最低限の一覧・編集のみ）
- テスト自動化の追加（`tests/` ディレクトリは空であり、追加は対象外）
- .env への変数追加（環境変数変更がないため `--force-recreate` は不要）

---

## 工程一覧

| 工程 | 中間成果物 | 入力 |
|---|---|---|
| 工程1: `is_admin` 課金バイパス実装 | `users/models.py` の修正済みプロパティ | 現行コード |
| 工程2: 管理者ダッシュボード実装 | `app/admin/router.py` + `app/templates/admin/` テンプレート群 | 工程1の成果物 + 現行コード |
| 工程3: `promote_admin.py` スクリプト作成 | `yn-tools/scripts/promote_admin.py` | 現行 DB スキーマ |
| 工程4: 本番 VPS デプロイ・動作確認 | 本番環境の反映確認チェックリスト（全項目 Yes） | 工程1〜3の成果物 |

---

## 工程1: `is_admin` 課金バイパス実装

### 変更対象ファイル

- `yn-tools/app/users/models.py`

### 実装内容

```python
# has_active_plan プロパティ先頭に追加
if self.is_admin:
    return True

# has_full_access プロパティ先頭に追加
if self.is_admin:
    return True
```

`require_tool_access` は `has_full_access` を参照するため、追加変更不要（自動的にバイパスされる）。
`require_active_plan` は `has_active_plan` を参照するため、同様に自動バイパス済み。

### 完了条件

- [ ] `has_active_plan` プロパティの先頭に `if self.is_admin: return True` が追加されていること
- [ ] `has_full_access` プロパティの先頭に `if self.is_admin: return True` が追加されていること
- [ ] `is_admin=False` のユーザーに対して既存のプロパティ挙動が変わっていないこと
- [ ] `is_admin=True` かつ `plan="free"` の場合に `has_active_plan` が `True` を返すことをコード上で確認できること
- [ ] `is_admin=True` かつ `plan="free"` の場合に `has_full_access` が `True` を返すことをコード上で確認できること
- [ ] `is_admin=True` かつ `plan="per_tool"` 非購読ツールにアクセスした場合に `require_tool_access` が 402 を返さないこと（`has_full_access=True` 経由で透過されること）

### 品質チェック項目（工程1）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | `has_active_plan` に `is_admin` バイパスが正しく追加されているか（先頭に配置・戻り値 True） | 機能要件 | 25 |
| 2 | `has_full_access` に `is_admin` バイパスが正しく追加されているか（先頭に配置・戻り値 True） | 機能要件 | 25 |
| 3 | `is_admin=False` ユーザーのプロパティ挙動が変化していないか（既存ロジック破壊なし） | 既存挙動保護 | 25 |
| 4 | `require_tool_access` が `has_full_access` 経由で自動バイパスされることをコード追跡で確認できるか | 機能要件 | 15 |
| 5 | 変更行数が最小限か（2プロパティへの2行追加のみ、余分な変更なし） | 可読性・影響範囲 | 10 |
| 合計 | | | 100 |

---

## 工程2: 管理者ダッシュボード実装

### 新規作成ファイル

```
yn-tools/app/admin/router.py
yn-tools/app/templates/admin/base_admin.html    # 管理者用ベーステンプレート
yn-tools/app/templates/admin/users.html         # ユーザー一覧
yn-tools/app/templates/admin/user_detail.html   # ユーザー詳細・編集
yn-tools/app/templates/admin/billing.html       # 課金履歴サマリー
```

### 変更対象ファイル

```
yn-tools/app/main.py                            # admin router を include_router に追加
yn-tools/app/templates/base.html                # アカウントメニューに管理者リンクを追加
```

### ルート設計

| パス | メソッド | 機能 | 依存 |
|---|---|---|---|
| `GET /admin` | GET | ダッシュボードトップ（ユーザー一覧へリダイレクト） | `require_admin` |
| `GET /admin/users` | GET | ユーザー一覧（全カラム表示、ページネーションなし・件数上限1000） | `require_admin` |
| `GET /admin/users/{user_id}` | GET | ユーザー詳細・編集フォーム | `require_admin` |
| `POST /admin/users/{user_id}` | POST | ユーザー属性更新（`is_admin` / `is_active` / `plan` 手動変更） | `require_admin` |
| `POST /admin/users/{user_id}/logout` | POST | 強制ログアウト（セッションは Cookie ベースのため `session.clear()` 等は不可。代替: `is_active=False` に設定してログイン不可にする） | `require_admin` |
| `GET /admin/billing` | GET | 課金履歴サマリー（月次集計・合計件数・合計金額） | `require_admin` |

**強制ログアウトの実装注意点**: Starlette の `SessionMiddleware` はサーバー側セッションストアを持たない（Cookie 署名方式）。そのため、セッション Cookie を直接無効化できない。代替実装として `is_active=False` を設定し、`get_current_user` が `is_active` フィールドをチェックするよう修正するか、または「次回リクエスト時に 401 を返す」方式（`require_login` でチェック追加）を採用する。

### ユーザー一覧表示カラム

メールアドレス / 表示名 / プラン / 登録日 / 最終更新日（`updated_at` で代替）/ `is_admin` / `is_active`

### 課金履歴サマリー

`PaymentHistory` テーブルから以下を集計して表示:
- 月別売上合計（JPY）
- サブスク購入件数（`tool_slug IS NULL`）
- 個別ツール購入件数（`tool_slug IS NOT NULL`）
- `status = 'succeeded'` のみ集計

### `base.html` への追加

アカウントドロップダウン（`<div class="absolute right-0 top-full...">`）内の「アカウント設定」リンクの直上に以下を挿入:

```html
{% if user and user.is_admin %}
<a href="/admin/users" class="flex items-center gap-2 px-4 py-2 text-sm text-indigo-600 hover:bg-indigo-50">
    <svg ...>（管理者アイコン）</svg>
    管理者ダッシュボード
</a>
<div class="border-t my-1"></div>
{% endif %}
```

### 完了条件

- [ ] `/admin/users` にアクセスすると全ユーザー一覧が表示されること（`is_admin=True` のユーザーでのみアクセス可）
- [ ] `/admin/users/{user_id}` から `is_admin` / `is_active` / `plan` を手動変更できること（POST が DB に反映されること）
- [ ] `/admin/users/{user_id}/logout` の POST により、対象ユーザーが次回リクエスト時にアクセス拒否されること（`is_active=False` 設定方式）
- [ ] `/admin/billing` に月次売上サマリーが表示されること（`status='succeeded'` のみ集計）
- [ ] `is_admin=False` のユーザーが `/admin` 配下にアクセスした場合に 403 が返ること（`require_admin` 依存が機能していること）
- [ ] `base.html` のアカウントメニューに「管理者ダッシュボード」リンクが `is_admin=True` のユーザーにのみ表示されること
- [ ] `main.py` に admin router が正しく `include_router` で登録されていること
- [ ] 管理者ダッシュボードのテンプレートが既存 `base.html` を継承し、デザインが統一されていること

### 品質チェック項目（工程2）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 全ルートに `require_admin` 依存が設定されており、非管理者アクセスが 403 になるか | セキュリティ | 20 |
| 2 | ユーザー詳細更新（POST）が DB に正しく反映されるか（`is_admin` / `is_active` / `plan` の書き込み） | 機能要件 | 20 |
| 3 | 強制ログアウト（`is_active=False`）が `require_login` or `get_current_user` で正しくブロックされるか | 機能要件 | 15 |
| 4 | 課金履歴サマリーが `status='succeeded'` のみを集計しているか | 機能要件 | 15 |
| 5 | `base.html` の管理者リンクが `user.is_admin` 条件でのみ表示されているか（非管理者に露出しないか） | セキュリティ | 15 |
| 6 | `main.py` に admin router が漏れなく登録されているか（`/admin` ルートが 404 にならないか） | 機能要件 | 10 |
| 7 | テンプレートが既存デザイン（Tailwind CSS / base.html 継承）に統一されているか | 可読性・UI | 5 |
| 合計 | | | 100 |

---

## 工程3: `promote_admin.py` スクリプト作成

### 作成ファイル

`yn-tools/scripts/promote_admin.py`

### 仕様

```
python scripts/promote_admin.py <email>
```

- 指定メールの User レコードを検索し、`is_admin = True` に更新する（冪等：既に True でも OK）
- 対象ユーザーが見つからない場合はエラーを出力して終了（exit code 1）
- 成功時は `[OK] info@ynfactory.online を is_admin=True に設定しました` を出力
- SQLAlchemy の同期エンジン（`create_engine`）を使い、本番 DB パス（`/app/data/yn_tools.db` 等）は環境変数 `DATABASE_URL` から取得する

### VPS 上での実行手順（運用ドキュメント）

```bash
# 1. コンテナ内で実行
docker compose exec web python scripts/promote_admin.py info@ynfactory.online

# 2. 直接 SQLite で確認（任意）
docker compose exec web sqlite3 /app/data/yn_tools.db \
  "SELECT id, email, is_admin FROM users WHERE email='info@ynfactory.online';"
```

### 想定外パターン: `info@ynfactory.online` が未登録の場合

`promote_admin.py` はエラーを出力して終了する。この場合:
1. オーナーが `https://tools.ynfactory.online` にアクセスし、Google OAuth で `info@ynfactory.online` アカウントを使って初回ログインする
2. DB にユーザーレコードが作成されたことを確認（`SELECT` で確認可能）
3. 再度 `promote_admin.py` を実行して `is_admin=True` に設定する

### 完了条件

- [ ] `python scripts/promote_admin.py info@ynfactory.online` が成功メッセージを出力すること
- [ ] 実行後、DB の該当レコードで `is_admin = 1`（True）であること
- [ ] 存在しないメールを指定した場合にエラーメッセージ + exit code 1 で終了すること
- [ ] 冪等性が担保されていること（同じコマンドを 2 回実行してもエラーにならないこと）
- [ ] `DATABASE_URL` 環境変数が未設定の場合にわかりやすいエラーメッセージが出ること

### 品質チェック項目（工程3）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | コマンドが冪等であること（2回実行してもエラーなし・DB が正常な状態になること） | 機能要件 | 30 |
| 2 | 対象ユーザー不存在時に exit code 1 + エラーメッセージが出力されること | エラーハンドリング | 25 |
| 3 | `DATABASE_URL` 環境変数から DB パスを取得し、ハードコードしていないこと | 可搬性 | 20 |
| 4 | 成功時に更新内容（メール・is_admin の前後値）を出力すること | 可読性 | 15 |
| 5 | スクリプトが Docker コンテナ外部（ローカル）でも実行できる構造になっているか（環境変数だけで制御できるか） | 可搬性 | 10 |
| 合計 | | | 100 |

---

## 工程4: 本番 VPS デプロイ・動作確認

### 前提条件

工程1〜3の成果物がすべて合格（85点以上）であること。

### デプロイ手順

```bash
# VPS へ SSH ログイン後（または CI経由）

# 1. コード反映
cd /opt/yn-tools/  # VPS 上の本番ディレクトリ（HANDOFF.md に記載の実際パスを確認すること）
git pull origin master

# 2. イメージ再ビルド（COPY 焼き込みのため必須）
docker compose up -d --build

# （.env 変更がある場合は --force-recreate を追加するが、今回は .env 変更なし）

# 3. admin 化スクリプト実行
docker compose exec web python scripts/promote_admin.py info@ynfactory.online

# 4. DB 反映確認
docker compose exec web sqlite3 /app/data/yn_tools.db \
  "SELECT id, email, is_admin, plan FROM users WHERE email='info@ynfactory.online';"
```

### 動作確認チェックリスト

#### A. 管理者権限チェック（`info@ynfactory.online` でログイン後）

- [ ] ダッシュボードの `plan = "free"` 状態でも「アップグレード」バナーが表示されないこと（`has_active_plan = True` のため）
- [ ] 任意のツール（例: `/tools/sales/`）に課金なしでアクセスできること（402 が出ないこと）
- [ ] アカウントメニューに「管理者ダッシュボード」リンクが表示されること
- [ ] `/admin/users` にアクセスしてユーザー一覧が表示されること
- [ ] `/admin/billing` にアクセスして課金サマリーが表示されること

#### B. 一般ユーザー権限チェック（別の Google アカウントでログイン）

- [ ] `plan = "free"` の一般ユーザーがツールにアクセスすると 402 が返ること（既存挙動が破壊されていないこと）
- [ ] アカウントメニューに「管理者ダッシュボード」リンクが表示されないこと
- [ ] `/admin/users` にアクセスすると 403 が返ること

#### C. 課金フロー確認（Stripe Webhook 整合性）

- [ ] トライアル登録フローが正常に動作すること（既存挙動の破壊なし）
- [ ] `per_tool` プランのユーザーが個別ツール購読できること（既存挙動の破壊なし）

### 完了条件

- [ ] 上記 A・B・C のすべてのチェック項目が Yes であること
- [ ] `docker compose up -d --build` がエラーなく完了していること
- [ ] `docker compose logs web` に起動エラーがないこと
- [ ] `/health` エンドポイントが `{"status": "ok", "db": "connected"}` を返すこと

### 品質チェック項目（工程4）

| # | チェック項目 | カテゴリ | 配点 |
|---|---|---|---|
| 1 | 管理者アカウント（`info@ynfactory.online`）で全ツールに 402 なしでアクセスできるか | 機能要件 | 25 |
| 2 | 管理者ダッシュボード（`/admin/users`, `/admin/billing`）が正常表示されるか | 機能要件 | 20 |
| 3 | 一般ユーザーの課金フロー（トライアル・`per_tool`・`all_tools`）が破壊されていないか | 既存挙動保護 | 25 |
| 4 | 非管理者が `/admin` にアクセスして 403 が返るか | セキュリティ | 15 |
| 5 | `/health` が `ok` を返し、コンテナログにエラーがないか | デプロイ品質 | 15 |
| 合計 | | | 100 |

---

## リスクとブロッカー

### R1: 本番 DB バックアップ（必須・デプロイ前）

工程4実行前に本番 SQLite DB のバックアップを取得すること。

```bash
docker compose exec web cp /app/data/yn_tools.db /app/data/yn_tools.db.bak_$(date +%Y%m%d)
```

万一 `promote_admin.py` が誤ったレコードを更新した場合に即時リストアできる状態にしておく。

### R2: Stripe Webhook との整合性

今回の変更は Stripe 側のデータに一切触れない（Webhook 受信ロジック・subscription ID・customer ID は変更なし）。`is_admin` バイパスはアプリケーションレイヤーのみであり、Stripe 請求は発生しない。ただし、管理者によるユーザーの `plan` 手動変更は Stripe と非同期になる点に注意（Stripe のサブスクリプションをキャンセルせず DB の `plan` だけ変更すると、Webhook による上書きが発生する可能性がある）。管理者の `plan` 編集はデバッグ・緊急対応用途に限定し、通常は Stripe 経由で変更すること。

### R3: 強制ログアウトの制限

Starlette の `SessionMiddleware` はサーバーサイドセッションストアを持たない（Cookie 署名方式）。そのため、発行済みセッション Cookie を即時無効化する手段がない。工程2では `is_active=False` を設定し、次回リクエスト時に `get_current_user` でチェックして `None` を返す方式を採用する。これにより、既存セッションの有効期間中は一時的にアクセスが継続される可能性があるが、セッション期限（`SessionMiddleware` の `max_age` 設定値）が過ぎれば自動的に無効化される。

### R4: `info@ynfactory.online` が未登録の場合

`promote_admin.py` がエラーで終了する。対処法は工程3「想定外パターン」のセクションを参照。デプロイ前にオーナーが一度 Google OAuth でログインしておくことを推奨する。

### R5: VPS 本番ディレクトリパスの確認

本要件定義書では `/opt/yn-tools/` と仮定しているが、実際のパスは HANDOFF.md に記載の VPS 情報を確認すること。`DATABASE_URL` に設定されている SQLite パスも同様に確認すること。

---

## ループ上限

各工程ごとに **最大5回** まで実行→品質チェックを繰り返す。5回超過した場合はユーザーへ相談する。

---

## 備考

- `User.is_in_trial`, `User.has_paid_plan_during_trial`, `User.trial_remaining_days` の各プロパティは今回変更しない（トライアル管理に直接関係しないため）
- `PlanGuardMiddleware`（`billing/plan_guard.py`）は `/tools/*` の未認証ユーザーをリダイレクトするだけであり、plan チェックは `require_active_plan` 依存に委譲している。admin バイパスは `has_active_plan` に追加されるため、Middleware は変更不要
- 管理者ダッシュボードの `/admin` パスは `FREE_PATHS` に追加不要（`require_admin` 依存が認証・認可を担保する）
- `billing/plan_guard.py` の `FREE_PATHS` には `/admin` が含まれないが、`PlanGuardMiddleware` は `/tools/*` のみをチェックするため問題なし
