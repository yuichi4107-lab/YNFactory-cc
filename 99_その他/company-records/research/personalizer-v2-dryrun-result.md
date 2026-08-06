# Personalizer v2 dryrun 実行結果

**実施日**: 2026-05-04  
**工程**: 工程7: VPSパイプライン改修  
**実行コマンド**: `SALES_OPS_DRY_RUN=true ./venv/bin/python3 scripts/run_personalizer.py`

---

## 実行サマリー

| 項目 | 値 |
|---|---|
| 実行モード | DRYRUN（実送信なし） |
| 処理件数 | 5件 |
| positioning | `ai_advisor`（全件） |
| テンプレート選択 | v1: 2件 / v2: 2件 / v3: 1件 |
| 規模不明企業（pending_unknown_size） | 1件（東北社会福祉さくら） |

---

## 業種別テンプレート選択結果

| 企業名 | 業種コード | テンプレート | 件名 |
|---|---|---|---|
| 信州テクノ工業 | E（製造業） | **v1** | 信州テクノ工業様 / 人手不足を「採用しない」で解決する方法があります |
| 東北介護サービス | Q（医療・福祉） | **v2** | 東北介護サービス様 / 今いる社員を「AI使える人材」に育てる方法 |
| 沖縄観光開発 | N（生活関連サービス） | **v3** | 沖縄観光開発様 / 経営判断のスピードを上げる「人とAIの役割分担」 |
| 東北社会福祉さくら | Q（医療・福祉）※規模不明 | **v2** | 東北社会福祉さくら様 / 今いる社員を「AI使える人材」に育てる方法 |
| 九州建設工業 | D（建設業） | **v1** | 九州建設工業様 / 人手不足を「採用しない」で解決する方法があります |

### 業種マッピング確認

- 製造業(E) / 建設業(D) → v1（人手不足対策）✓
- 医療・福祉(Q) → v2（キャリアアップ）✓
- 生活関連サービス(N) → v3（意思決定）✓

---

## 規模不明企業の処理確認（工程3b 指摘対応）

**対象**: 東北社会福祉さくら（社会福祉法人、資本金=0、size_employees_estimated=None）

```
size unknown for 東北社会福祉さくら — trying HP estimation
[DRYRUN] 東北社会福祉さくら | template=v2 | positioning=ai_advisor | size_unknown=True
```

**処理フロー**:
1. `size_employees_estimated = None` を検知 → HP推定を試みる
2. HP（example.co.jp）にアクセス → テキスト取得失敗（ダミーURL）
3. `size_unknown=True` のまま `pending_unknown_size` マークで通過
4. キューに入り、オーナーレビュー時に判断材料として表示

---

## プレースホルダー置換確認

**v1テンプレ（信州テクノ工業）**:
- `{{company_name}}` → 信州テクノ工業 ✓
- `{{contact_name}}` → ご担当者 ✓
- `{{industry_japanese}}` → 製造業 ✓
- `{{size_employees}}` → 約52名規模 ✓
- `{{location_prefecture}}` → 長野県 ✓
- `{{webinar_url}}` → https://ynfactory.online/webinar ✓
- `{{personalization_hint}}` → 貴社のホームページを拝見し、ご連絡差し上げました。 ✓

未処理プレースホルダー残留: **0件**（全件送信ブロック機能が正常動作）

---

## positioning='ai_advisor' 設定確認

全5件のログに `positioning=ai_advisor` が記録されており、旧 `yn_tools` ポジショニングからの切替が正常に機能している。

---

## run_list_builder.py（v2昇格版）動作確認

```
run_list_builder_v2 START  dry_run=True
--- Phase 1: gBizINFO フェッチャー ---
GBIZINFO_API_TOKEN found — using real gBizINFO API
（gBizINFO API 400エラー発生 — APIパラメータ調整が必要、工程8前に対応）

--- Phase 2: Google Maps API (a5) ---
[OK] 採用: 長野県中小企業団体中央会 都道府県=長野県 source=google_maps
[OK] 採用: 株式会社アールエフ 都道府県=長野県 source=google_maps
（以下続く）
```

**補足**: gBizINFO API が 400 エラーを返している。APIトークンは設定済みだが、
`prefecture_code` パラメータの仕様確認が必要。Google Maps経由は正常動作。
工程8（テスト5件生成）前に gBizINFO API パラメータを修正する必要がある。

---

## リネーム履歴

| 操作 | 元ファイル | 新ファイル |
|---|---|---|
| v1→legacy バックアップ | `scripts/run_list_builder.py`（旧v1） | `scripts/run_list_builder_legacy.py` |
| v2→メイン昇格 | `scripts/run_list_builder_v2.py` | `scripts/run_list_builder.py` |
| personalizer バックアップ | `src/tracks/c_outbound/personalizer.py`（旧v1） | `src/tracks/c_outbound/personalizer_v1.py` |
| personalizer 新版配置 | — | `src/tracks/c_outbound/personalizer.py`（新v2） |
| run_personalizer バックアップ | `scripts/run_personalizer.py`（旧v1） | `scripts/run_personalizer_v1.py` |
| run_personalizer 新版配置 | — | `scripts/run_personalizer.py`（新v2） |

---

## 既存 cron との互換性

- cron は `scripts/run_list_builder.py` / `scripts/run_personalizer.py` を参照している
- 両スクリプトのファイル名は変わっていないため cron 設定変更不要
- Sales OS cron（02:00 / 02:30）は `SALES_OPS_DRY_RUN=true` のため実送信なし
- 既存の JRA 予想・ばんえい・YN Tools cron は一切変更なし

---

## pytest テスト結果

```
============================== 40 passed in 0.67s ==============================
```

既存の `src/tests/test_list_builder_v2.py`（40件）が全件PASS。
回帰なし確認済み。

---

## DB バックアップ確認

- `/opt/sales-ops/data/sales_ops_pre_step7_20260504.db` — 工程7開始前のバックアップ
- `/opt/sales-ops/data/sales_ops_pre_migration002_20260504.db` — 工程3b前バックアップ
- `/opt/sales-ops/data/sales_ops_backup_20260430.db` — 既存バックアップ
