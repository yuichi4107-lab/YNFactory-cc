# note記事自動投稿プロジェクト 引き継ぎ書（Codex向け）

最終更新: 2026-05-14
作成: Claude Code セッション

---

## 1. このプロジェクトの目的

5アカウント運用の note 記事を、週次バッチで「5アカウント × 7日 = 35記事」分まとめて
下書き生成し、オーナーが毎朝公開ボタンを押すだけにする仕組みを作る。

- 記事生成（本文＋画像）→ note下書き保存 までを自動化
- 公開ボタンはオーナーが手動（誤投稿防止）
- スキル本体: `.agents/skills/note-article-publisher/SKILL.md`

---

## 2. 5アカウント構成（全アカウント作成・ログイン済み）

| account_id | note URL | クリエイター名 | ログインID | テーマ |
|---|---|---|---|---|
| you-ai-dx | https://note.com/you_ai_dx | yuichi | yuichi4107@gmail.com | AI活用 |
| money | https://note.com/money_40s_note | 40代からのお金と資産形成 | yuichi4107+note-money@gmail.com | お金・資産運用 |
| career | https://note.com/career_redesign_40s | 40代からのキャリア再設計 | yuichi4107+note-career@gmail.com | 40代キャリア |
| spiritual | https://note.com/tonoeru_hibi | 整える日々 | yuichi121@ymail.ne.jp | 日常の整え方 |
| love | https://note.com/tsuduku_kankei | 続く関係の手前で | fcmdt743@yahoo.co.jp | パートナーシップ |

**パスワード**: このファイルには記載しない。オーナーが1Password等で管理。
Codexが投稿作業する場合はオーナーから都度受け取るか、ログイン済みブラウザプロファイルを使う。

### 要確認事項（未確定）
- **career**: note ID を `brainy_mink6911` → `career_redesign_40s` にオーナーが手動変更する予定だった。
  実際に変更されたか未確認。accounts.json は変更後の前提で記載済み。最初に実URLを確認すること。
- **spiritual**: メール認証（yuichi121@ymail.ne.jp 宛）がオーナー手動で未完了の可能性。
  投稿前に認証完了しているか確認。
- **AI/お金/career のパスワードが `fair2000@` で共通**。セキュリティ上、別パスワード化をオーナーに推奨済み。

---

## 3. 完了済みの作業

### 3-1. スキル拡張（`.agents/skills/note-article-publisher/`）
- `SKILL.md` — 5アカウント運用・週次バッチモードのセクション追加済み
- `references/personas/{ai,money,career,spiritual,love}.md` — 5アカウントのペルソナ定義
- `references/weekly-batch.md` — 週次バッチ手順書
- `references/task-scheduler-setup.md` — Windows Task Scheduler 自動起動手順
- `scripts/run_weekly_batch.ps1` — Task Schedulerから呼ぶ起動スクリプト
- `templates/accounts.json.example`, `templates/topics.*.md.example` — 初期テンプレート

### 3-2. 運用ファイル（`.company/outputs/note-articles/`）
- `accounts.json` — 5アカウント構成（v3）。side-business / personal-brand は archived
- `accounts.archive-2026-05-13.json` — 旧構成のバックアップ
- `topics/{ai,money,career,spiritual,love}.md` — トピックキュー（各10件）
- `history.json` — 投稿履歴。末尾に love 試運転記事1件を追記済み

### 3-3. Chromeプロファイル（オーナー作業済み）
- `note-ai` / `note-money` / `note-career` / `note-spiritual` / `note-love` の5プロファイル作成・全ログイン完了

### 3-4. 週次バッチ試運転（love アカウント1記事）
- 記事生成 → 画像生成 → note下書き保存 まで成功
- 下書き: `https://editor.note.com/notes/ndbbb05a6ccae/edit/`（タイトル＋本文＋見出し画像）
- 出力フォルダ: `.company/outputs/note-articles/2026-05-14-love-satsushite-wo-yameta/`
- 品質チェック94点

---

## 4. 残課題（フルバッチ前に解決すべき）

試運転で判明した4つの課題。これがCodexの主タスク。

### 課題1: 本文中の挿絵が未挿入
見出し画像（カバー）はnoteにアップロードできたが、本文中の挿絵2枚は未挿入。
note エディタ（editor.note.com、ProseMirrorベース）で、本文の指定位置に画像ブロックを
挿入する処理を実装する必要がある。`image-placement.md` に配置位置の指定あり。

### 課題2: 本文の見出しが段落扱い
セクション見出し（例:「言わなくても伝わるはず」の罠）が、太字見出し（h2/h3）でなく
通常段落として入力されている。note エディタの見出し書式を適用する処理が必要。
note-post-ready.md 側で見出し行を判別できるマークアップ（例: `## 見出し`）にしておくと良い。

### 課題3: 本文入力時の文字化け
Playwright の `fill()` で長文本文を入力した際、1文字ゴミ（"gă"）が混入した。
分割入力、または入力後の検証＋修正処理が必要。

### 課題4: Playwrightは1ブラウザ＝1アカウント
Playwright MCP は単一ブラウザインスタンス。35記事フルバッチでは
アカウント切替（ログアウト→ログイン、またはプロファイル別起動）の設計が必要。
- 案A: アカウントごとにログアウト→ログイン（パスワード必要）
- 案B: Playwright を userDataDir 指定で5プロファイル別に起動（要 persistent context）
- 案C: Chromeの実プロファイルに Playwright を接続（CDP接続）

---

## 5. 投稿フロー（試運転で確立した手順）

note エディタへの下書き投入手順（love試運転で実証済み）:

1. `https://note.com/notes/new` を開く（→ editor.note.com にリダイレクト、note IDが発番される）
2. 「記事タイトル」textbox にタイトル入力
3. 本文 textbox にクリック → 本文を入力（改行で段落分割される）
4. 「画像を追加」ボタン → メニューから「画像をアップロード」→ file chooser で画像指定
   - **重要**: Playwright MCP は `g:\マイドライブ\YNFactory-cc` 配下のファイルのみアップロード可。
     画像は `.playwright-mcp/` フォルダ（英語パス）にコピーしてから指定すること。
5. 画像サイズ変更ダイアログ → 「保存」
6. 「下書き保存」ボタン → 「下書きを保存しました」表示を確認
7. 公開ボタン（「公開に進む」）は**押さない**

reCAPTCHA: signup時のみ発生。ログイン済みプロファイルでの投稿には出ない。

---

## 6. 重要な制約・注意

- **公開は絶対にしない**。下書き保存までがスキルの責務。公開はオーナーが手動。
- 画像ファイルは日本語パス（Googleドライブ配下）だと file chooser が詰まる場合あり。
  `.playwright-mcp/` か英語パスの一時フォルダにコピーしてから使う。
- history.json は UTF-8。ターミナル表示は文字化けするがファイル自体は正常。
- accounts.json の各アカウントに `persona_file` と `topic_file` のパスあり。記事生成時に必ず参照。
- 記事生成は executor サブエージェント方式が有効だった（1記事 約5.5分、71k tokens）。

---

## 7. 次にやること（推奨順）

1. career の実 note ID を確認し、accounts.json と一致させる
2. spiritual のメール認証完了を確認
3. 課題2（見出し書式）と課題3（文字化け）を解決 — 比較的軽い
4. 課題1（挿絵挿入）を解決 — note エディタの画像ブロック挿入を実装
5. 課題4（アカウント切替）を設計・実装
6. 5アカウント各1記事の小バッチでテスト
7. 35記事フルバッチ → Task Scheduler 登録（references/task-scheduler-setup.md）

---

## 8. 主要ファイルパス一覧

```
.agents/skills/note-article-publisher/
├── SKILL.md                          # スキル本体・ワークフロー
├── references/
│   ├── personas/*.md                 # 5アカウントのペルソナ
│   ├── weekly-batch.md               # 週次バッチ手順
│   └── task-scheduler-setup.md       # 自動起動設定
├── scripts/run_weekly_batch.ps1      # バッチ起動スクリプト
└── templates/                        # 初期テンプレート

.company/outputs/note-articles/
├── accounts.json                     # 5アカウント設定（v3）
├── accounts.archive-2026-05-13.json  # 旧構成バックアップ
├── history.json                      # 投稿履歴
├── topics/*.md                       # トピックキュー
├── HANDOFF-codex.md                  # この引き継ぎ書
└── 2026-05-14-love-satsushite-wo-yameta/  # 試運転の成果物
    ├── article.md
    ├── note-post-ready.md
    ├── image-placement.md
    ├── quality-check.md
    └── images/{top,inside}-love-*.png
```
