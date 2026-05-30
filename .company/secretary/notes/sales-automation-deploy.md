---
topic: 営業自動化ツール Vercelデプロイ手順
created: 2026-03-19
---

# 営業自動化ツール Vercelデプロイ手順

## ステータス: 未完了（別PCで実施予定）

## 手順

### 1. Vercelでプロジェクト作成
- https://vercel.com/dashboard → 「Add New...」→「Project」
- **yn-tools** リポジトリを選択
- **Root Directory**: `apps/sales-automation`
- **Framework Preset**: Next.js

### 2. 環境変数を2つ追加

- `DATABASE_URL` = `postgresql://neondb_owner:npg_GIOMaht85jpC@ep-withered-wave-a1xlu3ks-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- `DIRECT_URL` = `postgresql://neondb_owner:npg_GIOMaht85jpC@ep-withered-wave-a1xlu3ks.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`

※ 違いは `-pooler` の有無だけ

### 3. Deploy → 完了後 `/setup` で管理者アカウント作成

## DB情報
- Neon PostgreSQL（無料枠）
- テーブル作成済み（prisma db push 実行済み）
- Region: Asia Pacific (Singapore)
