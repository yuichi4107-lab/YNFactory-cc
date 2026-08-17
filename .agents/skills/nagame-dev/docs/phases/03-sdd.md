# Phase 3: 設計 SDD（IEEE 1016 準拠）

## 目的

Phase 2（SRS）で定義した要件を、実装可能な設計に変換する。
IEEE 1016 の4つの設計ビューで構造を記述し、全ての設計判断に根拠（ADR）を残す。

---

## 1. IEEE 1016 4つの設計ビュー

### 1-1. 論理ビュー（コンポーネント構成）

システムを構成するコンポーネントとその関係を定義する。

```markdown
## 論理ビュー

### コンポーネント一覧

| ID | コンポーネント名 | 責務 | 依存先 | 対応要件 |
|---|---|---|---|---|
| C-01 | ScriptParser | 台本テキストの解析と検証 | なし | FR-DATA-001 |
| C-02 | AudioGenerator | テキストから音声を生成 | C-01, 外部API | FR-DATA-002 |
| C-03 | VideoRenderer | 音声+字幕から動画を合成 | C-02 | FR-DATA-003 |

### コンポーネント間の依存関係

C-01 → C-02 → C-03 → 出力

### インターフェース定義

各コンポーネント間のインターフェースを定義する:
- 入力の型
- 出力の型
- エラー時の振る舞い
```

### 1-2. プロセスビュー（フロー/並行性）

処理の流れ、並行処理、非同期処理を定義する。

```markdown
## プロセスビュー

### メインフロー

1. ユーザーがCLIコマンドを実行
2. ScriptParser が台本を検証
3. AudioGenerator が音声を生成（外部API呼び出し）
4. VideoRenderer が動画を合成
5. 完了メッセージを出力

### 並行処理

- 音声生成: セクション単位で並列化可能（最大同時3リクエスト）
- 動画レンダリング: シングルスレッド（FFmpegの制約）

### エラーハンドリングフロー

- 外部APIタイムアウト → 3回リトライ → 失敗時はエラー終了
- ディスク容量不足 → 処理開始前にチェック → 不足時はエラー終了
```

### 1-3. データビュー（モデル/ER）

データの構造、保存方法、ライフサイクルを定義する。

```markdown
## データビュー

### データモデル

| エンティティ | 属性 | 型 | 制約 |
|---|---|---|---|
| Script | id, text, char_count, created_at | str, str, int, datetime | text: 500-10000文字 |
| Audio | id, script_id, file_path, duration | str, str, str, float | script_id: FK |
| Video | id, audio_id, file_path, size_mb | str, str, str, float | audio_id: FK |

### 保存方式

- メタデータ: SQLite（ローカルDB）
- メディアファイル: ローカルファイルシステム（output/ディレクトリ）

### データライフサイクル

- 生成後30日で自動削除（設定変更可能）
- バックアップ: 手動（MVPでは自動化しない）
```

### 1-4. 物理ビュー（デプロイ構成）

実行環境、デプロイ方法、インフラ構成を定義する。

```markdown
## 物理ビュー

### 実行環境

- OS: macOS / Linux
- ランタイム: Python 3.11+
- 外部依存: FFmpeg（システムインストール）

### デプロイ方法

- pip install（ローカル実行）
- Docker（オプション）

### ディレクトリ構成

project-root/
  src/           # ソースコード
  tests/         # テストコード
  output/        # 生成物出力先
  config/        # 設定ファイル
  docs/          # ドキュメント
```

---

## 2. C4モデル（Container / Component）

### Container図

システム全体を構成する「箱」（実行単位）を示す。

```markdown
### Container図

| Container | 技術 | 責務 |
|---|---|---|
| CLI Application | Python | ユーザー操作の受付、処理の統制 |
| Local Database | SQLite | メタデータの永続化 |
| File Storage | Local FS | メディアファイルの保存 |
| External API | OpenAI等 | 音声合成サービス |
```

### Component図

各 Container の内部構造を示す（論理ビューの詳細版）。

```markdown
### CLI Application のComponent図

| Component | 責務 | 公開API |
|---|---|---|
| CLI Entry | コマンド解析、引数バリデーション | main() |
| ScriptParser | 台本テキストの解析 | parse(text) → Script |
| AudioGenerator | 音声生成の統制 | generate(script) → Audio |
| APIAdapter | 外部API呼び出しの抽象化 | call(request) → response |
| VideoRenderer | 動画合成 | render(audio, subtitles) → Video |
| ConfigManager | 設定値の管理 | get(key) → value |
```

---

## 3. ADR（Architecture Decision Record）

全ての重要な設計判断に ADR を作成する。

### ADR テンプレート

```markdown
## ADR-[連番3桁]: [タイトル]

### 状態
提案 / 承認 / 廃止

### 決定
[何を決めたか、1-2文で]

### 理由
[なぜその決定をしたか]

### 代替案
| 案 | メリット | デメリット | 不採用理由 |
|---|---|---|---|
| 代替案A | ... | ... | ... |
| 代替案B | ... | ... | ... |

### 変更禁止レベル
| レベル | 意味 |
|---|---|
| L1-不変 | プロジェクト完了まで変更禁止 |
| L2-慎重 | 変更時は全ステークホルダーの承認必要 |
| L3-柔軟 | 技術的根拠があれば変更可 |

この ADR のレベル: [L1/L2/L3]

### 影響を受ける要件
[FR-XXX-001, NFR-XXX-001 等]
```

### ADR 作成基準

以下の判断には必ず ADR を作成する:

- [ ] 言語・フレームワークの選定
- [ ] データベースの選定
- [ ] 外部APIの選定
- [ ] 認証方式の選定
- [ ] アーキテクチャパターンの選定
- [ ] デプロイ方式の選定
- [ ] テスト戦略の選定

---

## 4. 横断的ルール（Cross-Cutting Concerns）

全コンポーネントに共通するルールを定義する。

| # | ルール | 内容 | 適用範囲 |
|---|---|---|---|
| CC-01 | **エラーハンドリング** | 全ての外部呼び出しに try-catch、リトライ3回 | 全コンポーネント |
| CC-02 | **ログ出力** | 処理開始/終了/エラーをログ出力、機密情報は含めない | 全コンポーネント |
| CC-03 | **設定値管理** | ハードコード禁止、設定ファイルまたは環境変数で管理 | 全コンポーネント |
| CC-04 | **入力バリデーション** | 外部入力は必ず検証、信頼しない | 境界コンポーネント |
| CC-05 | **冪等性** | 同じ入力で同じ結果を返す（外部APIの非決定性は除く） | データ処理系 |

---

## 5. ディレクトリ構成

```
project-root/
├── src/
│   ├── __init__.py
│   ├── main.py              # エントリポイント
│   ├── cli.py               # CLI引数解析
│   ├── parser/              # 台本解析
│   ├── generator/           # 音声生成
│   ├── renderer/            # 動画合成
│   ├── adapters/            # 外部API アダプター
│   └── config.py            # 設定管理
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── output/                  # 生成物（gitignore対象）
├── config/
│   └── settings.yaml        # 設定ファイル
├── docs/
│   ├── srs.md
│   ├── sdd.md
│   └── adr/
├── CLAUDE.md                # プロジェクトルール
├── CONSTRAINTS.md           # 制約条件
└── PROGRESS.md              # 進捗管理
```

---

## 6. トレーサビリティマトリクス

要件→設計→テストの追跡表を作成する。

```markdown
| 要件ID | 設計コンポーネント | ADR | テストID | 状態 |
|---|---|---|---|---|
| FR-DATA-001 | C-01 ScriptParser | ADR-001 | TC-001 | 設計済 |
| FR-DATA-002 | C-02 AudioGenerator | ADR-002 | TC-002 | 設計済 |
| FR-DATA-003 | C-03 VideoRenderer | ADR-003 | TC-003 | 設計済 |
| NFR-PERF-001 | CC-01 (横断) | - | TC-P01 | 設計済 |
```

---

## 7. 設計原則

### 7-1. 最小依存原則

- 外部ライブラリは必要最小限に抑える
- 標準ライブラリで実現できることは標準ライブラリを使う
- 依存追加時は ADR に理由を記載する

### 7-2. アダプターパターン + DRY_RUN モック

- 全ての外部サービス呼び出しはアダプター経由にする
- アダプターは `DRY_RUN=true` でモックレスポンスを返す
- 実API と モック の切り替えは環境変数1つで行う

```python
# アダプターの構造例
class APIAdapter:
    def call(self, request):
        if os.environ.get("DRY_RUN") == "true":
            return self._mock_response(request)
        return self._real_call(request)
```

### 7-3. キーオプショナル設計

- APIキーがなくてもシステムが起動・テストできる
- APIキーがない場合は DRY_RUN モードで動作する
- 「APIキーを設定してください」ではなく「DRY_RUNモードで動作中」と表示する

---

## 8. CLAUDE.md 生成トリガー

SDD 完成時点で、プロジェクトルートに `CLAUDE.md` を生成する。

### CLAUDE.md に記載する内容

- プロジェクト概要（SRS の章1-2 から抽出）
- 技術スタック（SDD の物理ビューから抽出）
- ディレクトリ構成（SDD から転記）
- 横断的ルール（CC-01〜CC-05）
- コマンド一覧（ビルド、テスト、実行）
- ADR の要約（変更禁止事項）

---

## 9. Phase 3 完了条件

### 完了チェックリスト

- [ ] 4つの設計ビュー（論理/プロセス/データ/物理）が記述済み
- [ ] C4 モデル（Container/Component）が作成済み
- [ ] 主要な設計判断に ADR が作成済み
- [ ] 横断的ルールが定義済み
- [ ] ディレクトリ構成が確定済み
- [ ] トレーサビリティマトリクスで全要件がカバーされている
- [ ] アダプターパターン + DRY_RUN の設計が完了
- [ ] CLAUDE.md の草案が作成済み
- [ ] 社長が設計を承認した

---

## 10. 次フェーズへの引き継ぎ

| ファイル | 内容 |
|---|---|
| `sdd.md` | 設計書本体（4ビュー + C4） |
| `adr/` | ADR 一覧 |
| `CLAUDE.md` | プロジェクトルール（草案） |
| `traceability_matrix.md` | 追跡マトリクス |
| Phase 0-2 の全ファイル | ヒアリング、リサーチ、SRS |
