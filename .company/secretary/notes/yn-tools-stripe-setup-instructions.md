---
title: YN Tools Stripe本番キー設定 作業指示書
created: 2026-03-27
---

# YN Tools Stripe本番キー設定 作業指示書

## 概要
ConoHa VPS上のYN Toolsアプリケーションの.envファイルを編集し、Stripeのテストキーを本番キーに切り替える。

## サーバー情報
- IP: 163.44.101.31
- OS: Ubuntu 22.04
- 作業ファイル: `/opt/yn-tools/.env`

## 現在の.env内容（変更が必要な行のみ）

```
STRIPE_SECRET_KEY=<TEST_SECRET_KEY>   # ← Stripeダッシュボード(テスト)から取得
STRIPE_PUBLISHABLE_KEY=pk_test_51T3D1oKAVaivWwqwbjnhFgihjsXApgKWebYZ8uGEk7qcw45zWqqRBGEoxypRtyaAToOdZgGO3xUBLgRaJXt0GqwR00JlPHzne8
STRIPE_PRICE_ALL_TOOLS=price_1TEgqWKAVaivWwqwjAtBdduH
```

## 変更後（本番キー）

```
<STRIPE_LIVE_SECRET_KEY>   # ← Stripeダッシュボード(本番)から取得。要ローテーション(2026-05-30漏洩)
STRIPE_PUBLISHABLE_KEY=pk_live_51T3D1oKAVaivWwqwTBVvHaio7MsMf9SKgQltAGtOlVChq4ZLS36QiJyCgDOVBL7t1YXDndnHuNPw82mJsEdHrU8b00HoDPVvN1
STRIPE_PRICE_ALL_TOOLS=price_1TEmtlKAVaivWwqwPE68VEGw
```

## 作業手順

### ステップ1: .envファイルの編集
`/opt/yn-tools/.env` の以下3行を変更する。他の行は変更しないこと。

変更対象:
1. `STRIPE_SECRET_KEY` の値を `sk_test_...` → `sk_live_...` に変更
2. `STRIPE_PUBLISHABLE_KEY` の値を `pk_test_...` → `pk_live_...` に変更
3. `STRIPE_PRICE_ALL_TOOLS` の値を `price_1TEgqWKAVaivWwqwjAtBdduH` → `price_1TEmtlKAVaivWwqwPE68VEGw` に変更

### ステップ2: 変更確認
```bash
grep STRIPE /opt/yn-tools/.env
```

期待される出力:
```
<STRIPE_LIVE_SECRET_KEY>
STRIPE_PUBLISHABLE_KEY=pk_live_51T3D1oKAVaivWwqwTBVvHaio7MsMf9SKgQltAGtOlVChq4ZLS36QiJyCgDOVBL7t1YXDndnHuNPw82mJsEdHrU8b00HoDPVvN1
STRIPE_WEBHOOK_SECRET=<STRIPE_WEBHOOK_SECRET>
STRIPE_PRICE_ID=price_xxx
STRIPE_PRICE_ALL_TOOLS=price_1TEmtlKAVaivWwqwPE68VEGw
```

### ステップ3: 個別ツールのPrice IDをDBに登録
アプリコンテナ内でPythonスクリプトを実行し、tool_definitionsテーブルのstripe_price_idを更新する。

```bash
cd /opt/yn-tools
docker compose exec yn-tools python -c "
import sqlite3
conn = sqlite3.connect('yn_tools.db')
cur = conn.cursor()

# 現在のツール定義を確認
cur.execute('SELECT slug, stripe_price_id FROM tool_definitions')
print('=== 現在の設定 ===')
for row in cur.fetchall():
    print(row)

# 本番Price IDを設定
updates = {
    'sales': 'price_1TEmrmKAVaivWwqwOO0NPLql',
    'mailer': 'price_1TEms7KAVaivWwqwabRK9pJb',
    'gems': 'price_1TEmtNKAVaivWwqwmeG7NnWK',
}
for slug, price_id in updates.items():
    cur.execute('UPDATE tool_definitions SET stripe_price_id = ? WHERE slug = ?', (price_id, slug))
    print(f'Updated {slug} -> {price_id}')

conn.commit()

# 更新後を確認
cur.execute('SELECT slug, stripe_price_id FROM tool_definitions')
print('=== 更新後 ===')
for row in cur.fetchall():
    print(row)

conn.close()
"
```

注意: DBがSQLiteではなくPostgreSQLの場合は以下を使用:
```bash
docker compose exec yn-tools-db psql -U postgres -d yn_tools -c "SELECT slug, stripe_price_id FROM tool_definitions;"
```
を先に実行してDBの種類を確認すること。

PostgreSQLの場合:
```bash
docker compose exec yn-tools-db psql -U postgres -d yn_tools -c "
UPDATE tool_definitions SET stripe_price_id = 'price_1TEmrmKAVaivWwqwOO0NPLql' WHERE slug = 'sales';
UPDATE tool_definitions SET stripe_price_id = 'price_1TEms7KAVaivWwqwabRK9pJb' WHERE slug = 'mailer';
UPDATE tool_definitions SET stripe_price_id = 'price_1TEmtNKAVaivWwqwmeG7NnWK' WHERE slug = 'gems';
SELECT slug, stripe_price_id FROM tool_definitions;
"
```

### ステップ4: コンテナ再起動
```bash
cd /opt/yn-tools
docker compose down
docker compose up -d
```

### ステップ5: 動作確認
```bash
# コンテナが正常起動しているか
docker ps

# アプリのレスポンス確認
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
```
200が返ればOK。

### ステップ6: Stripe Webhook設定（本番用）
Stripeダッシュボード（本番モード）→ Developers → Webhooks で:
1. 「+ エンドポイントを追加」
2. URL: `https://tools.ynfactory.online/billing/webhook`
3. リッスンするイベント:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.deleted`
4. 作成後に表示される `whsec_` キーをコピー
5. `/opt/yn-tools/.env` の `STRIPE_WEBHOOK_SECRET` を新しい `whsec_` に更新
6. 再度 `docker compose down && docker compose up -d`

## 変更しない行（参考: .envの全内容）
```
APP_ENV=production
SECRET_KEY=<APP_SECRET_KEY>
DB_PASSWORD=<DB_PASSWORD>
GOOGLE_CLIENT_ID=191044568608-187db6pvbimfuld8kkqalj5u22n74id8.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<GOOGLE_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=https://tools.ynfactory.online/auth/callback
（↑ここより上は変更しない）
STRIPE_SECRET_KEY=（変更する）
STRIPE_PUBLISHABLE_KEY=（変更する）
STRIPE_WEBHOOK_SECRET=<STRIPE_WEBHOOK_SECRET>（ステップ6で変更）
STRIPE_PRICE_ID=price_xxx（変更不要）
GOOGLE_PLACES_API_KEY=（変更不要）
ENCRYPTION_KEY=<ENCRYPTION_KEY>（変更不要）
SCRAPING_DELAY_SEC=2.0（変更不要）
TRIAL_DAYS=30（変更不要）
STRIPE_PRICE_ALL_TOOLS=（変更する）
```

> **2026-05-30 セキュリティ注記**: 本ファイルは過去に実シークレット値を含んでいたため伏字化した。
> 実値は VPS `/opt/yn-tools/.env` を正とする。漏洩した `SECRET_KEY` / `DB_PASSWORD` /
> `GOOGLE_CLIENT_SECRET` / `STRIPE_WEBHOOK_SECRET` / `ENCRYPTION_KEY` / Stripe live secret は
> ローテーション対象（別途手順書参照）。

## 完了条件
- [ ] .envの3つのStripeキーが本番値に変更されていること
- [ ] DBのtool_definitionsに本番Price IDが設定されていること
- [ ] コンテナが正常に再起動していること
- [ ] https://tools.ynfactory.online/ が200を返すこと
- [ ] Stripe Webhookエンドポイントが作成されていること
