---
created: "2026-04-24"
completed: "2026-05-05"
project: "ebook-to-manga"
assignee: "engineering"
priority: normal
status: done
goal_type: 仕組み
milestone: ""
depends_on: []
blocks: []
---

# Pillow合成フォールバック撤廃 + Vision-check 緩和 + OCR 正規化強化

## ゴール
- **種別**: 仕組み
- **概要**: `ebook-to-manga` スキルの Step 5 QC ロジックが gpt-image-2 の高品質生成に対して過剰反応し、誤った Pillow 合成オーバーレイを画像に貼り付けるバグの恒久対応。Pillow合成フォールバックを完全撤廃し、Vision-check を緩和し、OCR 正規化を強化する。

## 背景・経緯

### 発覚事象
2026-04-24 に manga-career-restart vol1 の page_004〜010 を新スクリプトで生成した際、次の問題が発生した:

1. **Vision-check が過剰厳しい**: gpt-image-2 が明らかにミサキ・ケンタを全身描画しているページで「全身が描かれていないため NO」と判定。クローズアップ・バストアップコマを不存在と誤認
2. **Blind-OCR の False FAIL**: 吹き出し内の正確なセリフ描画を、三点リーダ `…` vs `...` の差、引用符の差、句読点の差等で「不一致」と判定
3. **Pillow 合成フォールバック発動**: 3 iter 全部 FAIL → Step 5.5 フォールバック → Pillow で下部にテキストボックスを貼付 → **元画像の美しさを台無しにする醜いオーバーレイ**

### オーナー判定
- 「正直酷い出来です。絶対商品化できません。Pillow 合成オーバーレイは絶対やらないでください。」
- gpt-image-2 の純 iter_1 画像（Pillow合成前）は商品化できる品質
- 今後 iter_1 のみ運用に変更、Pillow 合成オーバーレイは**一切使わない**

### 即時対応（本チケットの対象外）
- vol1 page_004〜010 を iter_1 に差し替え済み（Pillow合成版は `_pillow_overlay_discarded/` に退避）
- vol1 残り + vol2-4 の本番生成は **iter_1 シンプルモード**（QC/Pillow 全オフ）で進行中
- skill.md の恒久改修は本チケットで実施（本番展開とは並行）

## 担当部署
- **部署**: engineering

## 対象ファイル
- `g:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md`
  - Step 5（画像生成ハイブリッドQCループ）
  - Step 5-QC（Blind-OCR + Vision-check 判定モジュール）
  - Step 5.5（Pillow合成フォールバック）→ **撤廃**
  - コスト試算テーブル
  - progress.json 仕様
  - E2E 動作確認手順

## 要件

### 1. Pillow合成フォールバック（Step 5.5）を完全撤廃
- Step 5.5 セクション全体を削除または「廃止」マーク付きで保持（履歴として）
- Step 5 ループから Step 5.5 呼び出しを削除
- `progress.json` の `fallback_pages`, `fallback_reasons`, `fallback_count` フィールドを削除 or 非推奨マーク
- 3 iter 全 FAIL 時の扱い: `failed` 配列に記録のみ（再生成なし、人間目視対応）
- `panel_regions.json` はスキル内に残すが使用しない旨を明記（将来復活の可能性を残す）

### 2. Vision-check の「全身」条件を緩和
- 現状: 「キャラクターが全身イラストとして存在するか」
- 変更後: 「このページのどこかのコマにキャラクターが描かれているか（バストアップ・クローズアップ含む、顔だけでも OK）」
- テキスト枠のみ（イラストなし、名前ラベルだけ）は引き続き NO
- プロンプト内の判定基準例を更新

### 3. Blind-OCR の正規化強化
- `normalize_text()` に以下の追加正規化を導入:
  - 三点リーダ: `…` (U+2026) / `...` / `‥` (U+2025) を統一（例: すべて `...` 3文字に寄せる）
  - ダッシュ: `—` / `―` / `ー` / `-` の統一
  - 引用符: `〝〟` / `"` / `「」` / `『』` の対称正規化
  - 波ダッシュ: `〜` / `～`
- 完全一致判定に fuzzy match を限定的に導入（編集距離 2文字以内を PASS 扱い、ただしキャラ名等の重要部分は完全一致維持）→ 要設計
- 正規化例とテストケース（page_005 の実データを使用）を skill.md に記載

### 4. Step 5 ループの再設計
- iter 上限 `max_iter`: 3 → 1 をデフォルトに変更（iter_1 で完結を基本運用）
- `max_iter=3` は品質問題が明確にある場合のオプションとして残す
- OCR/Vision-check の実施は引数フラグで任意化（`--qc off|lite|full`）
  - `off`: QC なし、iter_1 採用（今回の本番運用モード）
  - `lite`: Vision-check のみ、OCR スキップ（キャラ欠落のみ検出）
  - `full`: OCR + Vision-check 両方（従来動作、緩和版）

### 5. コスト試算テーブル更新
- iter_1 シンプルモード: 1ページ $0.21（画像生成のみ）
- QC lite モード（Vision-checkのみ）: 1ページ $0.22〜$0.23
- QC full モード: 1ページ $0.25〜$0.28（緩和版のため再生成発動率低下）
- 100ページ冊あたり: simple $21 / lite $23 / full $27

### 6. E2E 動作確認手順の更新
- page_002 相当のキャラ欠落バグ検出（Vision-check lite モードで）
- iter_1 シンプルモードの基本動作確認
- OCR 緩和後の三点リーダ差異吸収確認（page_005 実データ想定）
- Pillow 合成が**発動しない**ことの回帰確認

## 期待コスト影響
- gpt-4o Vision-check 呼び出し数削減: 1ページあたり 1回（現状3回最大）→ 60〜80% 削減
- gpt-4o OCR 呼び出し数削減: 同様（モードによっては 0）
- Pillow 処理: 廃止（ランタイムコスト削減）
- 合計: 1ページあたり **$0.20 前後**（simple）〜 **$0.28 前後**（full 緩和版）

## 完了条件
- [ ] skill.md から Step 5.5（Pillow合成フォールバック）セクションが削除または「廃止」マーク付きになっている
- [ ] Step 5 ループで Pillow 合成が呼び出されない仕様になっている
- [ ] Vision-check プロンプトの「全身」条件が削除され「どこかに描かれていれば YES」になっている
- [ ] Blind-OCR の `normalize_text()` に三点リーダ/ダッシュ/引用符/波ダッシュの正規化が追加されている
- [ ] Step 5 の `max_iter` デフォルトが 1、`--qc` フラグで off/lite/full が選べる設計になっている
- [ ] コスト試算テーブルが更新されている
- [ ] E2E 動作確認手順が更新され、page_002 相当のキャラ欠落検出が lite モードで動作することを想定した手順になっている
- [ ] `progress.json` の廃止フィールドが明記されている
- [ ] 既存の OCR 既存動作（fuzzy matching 導入前の完全一致）が option として残されている（`--strict-ocr` フラグ等）

## 成果物の保存先
- 修正対象: `g:\マイドライブ\YNFactory-cc\.claude\skills\ebook-to-manga\skill.md`

## 承認ポイント
- [ ] なし（engineering が自律実行・完了後に秘書経由でオーナーに報告）

## 優先度
- `normal`（本番 vol1-4 展開は iter_1 シンプルモードで完遂可能なため緊急ではない）
- ただし **次回の新規書籍着手前には完了必須**

## 作業ログ
| 日時 | 状態 | 内容 |
|------|------|------|
| 2026-04-24 | open | チケット起票（vol1 page_004-010 で Pillow合成オーバーレイ問題発覚 + オーナーからの撤廃厳命により） |
| 2026-05-05 | done | 5工程に分割して実施・全工程QA合格（工程1: 95点 / 工程2: 93点 / 工程3: 92点 / 工程4: 93点 / 工程5: 95点）。要件定義書: `.company/secretary/notes/2026-05-05-ebook-to-manga-skill-refactor-requirements.md`。Pillow関連3項目は実質完了済みのため検証のみ。チケット完了条件9/9充足。 |

## メモ
- 本チケットは **今回の 4冊再生成タスクとは並行** で進める（本番展開は iter_1 シンプルモードで別途完遂）
- 完了後に本番 vol1-4 で Vision-check の再実行は**不要**（iter_1 が商品化OK品質であることをオーナー承認済み）
- 関連先行チケット: `2026-04-23-ebook-to-manga-step5qc-character-presence-check.md`（Vision-check 追加、本チケットで緩和）
