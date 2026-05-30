# cost_simple.md — vol1 / iter_1 シンプルモード コスト記録

## セッション履歴

| 日時 (JST) | 実行内容 | 生成ページ数 | 実コスト ($) | 備考 |
|---|---|---|---|---|
| 2026-04-24 04:15:34〜04:16:10 | iter_1 simple 本番実行 (dry-run=False) | 0 | $0.00 | page_011 の最初の API 呼び出しで Billing hard limit エラー（400）。2回リトライ後にスクリプト停止。実際に生成・課金されたページなし |

## dry-run セッション（参考・非課金）

| 日時 (JST) | 対象 | dry-run 生成成功（カウントのみ）| 推定コスト | 備考 |
|---|---|---|---|---|
| 2026-04-24 04:14:01 | pages=11-12, skip-existing=False | 2 | $0.42 | dry-run |
| 2026-04-24 04:14:09 | pages=all, skip-existing=False | 78 | $16.38 | dry-run |
| 2026-04-24 04:15:23 | pages=all, skip-existing=True | 46 | $9.66 | dry-run (page_002〜010 スキップ) |

## 実際の累計コスト（iter_1 simple）

- **今セッション（iter_1 simple）実費**: $0.00
- **前セッション（iter_0 ocr+vision）推定**: $5.46（progress.json v1 より）
- **cumulative total**: ~$5.46

## ページ状況まとめ（2026-04-24 04:16 時点）

| 状態 | ページ | 枚数 |
|---|---|---|
| テキストページ（スキップ対象） | 1, 33, 53, 82, 83, 84 | 6 |
| iter_1 simple 生成済み | なし（0枚） | 0 |
| 前セッション生成済み（iter_0）で pages/ に残存 | 2〜10 | 9 |
| Billing エラーで未生成（pending） | 11〜32, 34〜52, 54〜81 | 69 |
| failed_billing（エラー初発） | 11 | 1 |

## 次回実行時の想定コスト

- pending 69 ページ × $0.21/ページ ≒ **$14.49**（参考: dry-run 推定 $9.66 は skip-existing=True で 46 ページ対象）
