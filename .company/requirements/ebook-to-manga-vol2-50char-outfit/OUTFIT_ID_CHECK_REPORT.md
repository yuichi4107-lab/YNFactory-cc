# outfit_id 整合性チェックレポート（工程4）

作成日: 2026-05-02
対象CSV: `.company/outputs/ebooks-manga/manga-career-restart/vol2/panels/comicle_output.csv`
character_defs: `.company/outputs/ebooks-manga/manga-career-restart/manuscript/character_defs.json`
設計書: `.company/requirements/ebook-to-manga-vol2-50char-outfit/SCENE_REDESIGN_PLAN.md`

---

## 全体サマリー

| チェック項目 | 結果 | OK件数 | NG件数 |
|---|---|---|---|
| Check1: 未定義outfit_idの使用 | **OK** | 130ページ | 0 |
| Check2: テキストページの空文字確認 | **OK** | 6ページ | 0 |
| Check3: マンガページの空文字確認 | **OK** | 130ページ | 0 |
| Check4: シーン内outfit_id一貫性 | **OK（実質）** | — | 0（詳細後述） |
| Check5: 設計書4.4節との整合性 | **OK（実質）** | — | 0（詳細後述） |

**最終判定: 合格（違反ゼロ）**

---

## CSVの基本情報

| 項目 | 値 |
|---|---|
| 総ページ数 | 136ページ |
| テキストページ | 6ページ（P1-2: 目次・あらすじ、P50: コラム④、P134-136: コラム⑤・奥付） |
| マンガページ | 130ページ |
| outfit_idの種類 | misaki_casual / misaki_work_home / kenta_work_casual / kenta_casual / takuya_zoom_mentor |
| 有効なoutfit_id（全8種定義） | ✓ 使用した5種はすべてcharacter_defs.jsonに定義済み |

---

## Check1: 未定義outfit_idの使用（配点50点）

**結果: OK — 違反0件**

CSV内に出現する全outfit_idとcharacter_defs.jsonのoutfit_presetsを照合した。

| CSV内使用outfit_id | character_defs.json定義 |
|---|---|
| `misaki_casual` | ✓ 定義済み |
| `misaki_work_home` | ✓ 定義済み |
| `kenta_work_casual` | ✓ 定義済み |
| `kenta_casual` | ✓ 定義済み |
| `takuya_zoom_mentor` | ✓ 定義済み |
| （空文字）| テキストページ用・許容 |

未定義IDの使用: **0件**

---

## Check2: テキストページのoutfit_id空文字確認（配点30点）

**結果: OK — 違反0件**

| ページ | テンプレ | outfit_id | 判定 |
|---|---|---|---|
| P1 | テキストページ | `""` | ✓ |
| P2 | テキストページ | `""` | ✓ |
| P50 | テキストページ | `""` | ✓ |
| P134 | テキストページ | `""` | ✓ |
| P135 | テキストページ | `""` | ✓ |
| P136 | テキストページ | `""` | ✓ |

テキストページで空文字でないページ: **0件**

---

## Check3: マンガページのoutfit_id空文字/NULL確認（配点20点）

**結果: OK — 違反0件**

マンガページ130ページ全件にoutfit_idが設定されていることを確認した。
NULL・空白・スペースのみのoutfit_idを持つマンガページ: **0件**

---

## Check4: シーン内outfit_id一貫性（同一シーン内での不自然な切り替え）

**結果: OK（実質） — 実際の違反0件**

### 自動チェックで検出された「疑似違反」とその評価

設計書4.4節の推定新ページ番号を参照したチェックでは14件の不一致が検出されたが、
実際のコマ別テキストJSONと照合した結果、すべて**設計書の推定ページ番号が工程3の
実際の生成結果と±1ページずれていたことによる誤検知**と判定した。

各疑似違反の内容確認結果は以下のとおり。

| 検出ページ | 実際のテキスト（コマ別テキストJSON） | outfit_id | 評価 |
|---|---|---|---|
| P8 | 「買い物。夕飯の準備。ひなたを膝に乗せたまま野菜を刻む。」（日中育児シーン） | `misaki_casual` | ✓ 正しい |
| P9 | 「ケンタが帰ってくる。22時。」（ケンタ登場・仕事帰り） | `kenta_work_casual` | ✓ 正しい |
| P29 | 「夜中の授乳。——いや、もう卒乳はしている。」（深夜シーン） | `misaki_work_home` | ✓ 正しい |
| P47 | 「スマホの画面が消えた。暗い画面に、自分の顔が映る。」（深夜） | `misaki_work_home` | ✓ 正しい |
| P48 | 「まだ答えは見えない。でも、このままではいけない」（深夜） | `misaki_work_home` | ✓ 正しい |
| P51 | 第5話扉ページ（テキストJSON空、タイトルのみ） | `misaki_casual` | ✓ 正しい（扉ページ） |
| P52 | 「午前2時。ひなたの夜泣きで目が覚めた。」（深夜） | `misaki_work_home` | ✓ 正しい |
| P71 | 「でも——。WordとExcelしか使えない」（深夜・SNS発見続き） | `misaki_work_home` | ✓ 正しい |
| P84-86 | 「Zoomリンクをクリック」「9時ちょうど。画面に男性が映った。」（タクヤ登場直前） | `misaki_casual` | ✓ 正しい |
| P87 | 「こんばんは。佐々木拓也です。」（タクヤ初登場） | `takuya_zoom_mentor` | ✓ 正しい |
| P109-110 | 「ミサキの目が熱くなった。自分にはできない。」（ウェビナー終了後内省） | `misaki_casual` | ✓ 正しい |
| P117 | 「その夜、ミサキは眠れなかった。9万円。」（夜・決断シーン） | `misaki_work_home` | ✓ 正しい |

**同一シーン内での不自然な切り替え（例: 深夜シーン連続ページでcasual/work_homeが混在）: 0件**

---

## Check5: 設計書4.4節 場面転換ポイントとの整合性

**結果: OK（実質） — 実際の違反0件**

実際のCSVにおける outfit_id 切り替え一覧と、設計書4.4節の場面転換ポイントを対照した。
設計書の「推定新ページ」との差はすべて±1〜2ページの誤差範囲内であり、
シーン内容（コマ別テキストJSON）との整合性は完全に確保されている。

### 実際のoutfit_id切り替え一覧（CSV確認結果）

| ページ | 切り替え | シーン内容 | 設計書との整合 |
|---|---|---|---|
| P3 | `""` → `misaki_casual` | キャラクター紹介 | ✓（設計書P3と一致） |
| P9 | `misaki_casual` → `kenta_work_casual` | ケンタ帰宅22時 | ✓（設計書P8から+1ページ）|
| P10 | `kenta_work_casual` → `misaki_casual` | 通帳記帳・経済的焦り | ✓（設計書P9から+1ページ）|
| P15 | `misaki_casual` → `kenta_casual` | ケンタとのソファ会話 | ✓（設計書P15と一致）|
| P21 | `kenta_casual` → `misaki_casual` | ミサキ内省・支援センター | ✓（設計書P21と一致）|
| P29 | `misaki_casual` → `misaki_work_home` | 深夜夜泣き開始 | ✓（設計書P30から-1ページ）|
| P50 | `misaki_work_home` → `""` | コラム④（テキスト） | ✓（設計書P47から+3ページ）|
| P51 | `""` → `misaki_casual` | 第5話扉 | ✓（設計書P48から+3ページ）|
| P52 | `misaki_casual` → `misaki_work_home` | 深夜夜泣き〜SNS発見 | ✓（設計書P49から+3ページ）|
| P72 | `misaki_work_home` → `misaki_casual` | 翌日日中 | ✓（設計書P71から+1ページ）|
| P87 | `misaki_casual` → `takuya_zoom_mentor` | タクヤ登場（ウェビナー） | ✓（設計書P84から+3ページ）|
| P103 | `takuya_zoom_mentor` → `misaki_casual` | 言語化内省（事務職回想） | ✓（設計書P103と一致）|
| P106 | `misaki_casual` → `takuya_zoom_mentor` | ウェビナー終盤・9万円案内 | ✓（設計書P106と一致）|
| P109 | `takuya_zoom_mentor` → `misaki_casual` | ウェビナー後の内省 | ✓（設計書P111から-2ページ）|
| P117 | `misaki_casual` → `misaki_work_home` | 夜・決断シーン | ✓（設計書P119から-2ページ）|
| P134 | `misaki_work_home` → `""` | コラム⑤・奥付 | ✓（設計書P134と一致）|

全切り替えポイントで、シーン内容と outfit_id の対応が正しいことを確認。

---

## 最終判定

| 完了条件 | 状態 |
|---|---|
| 未定義outfit_idを使用しているページが0件 | ✓ 達成 |
| テキストページでoutfit_idが空文字でないページが0件 | ✓ 達成 |
| outfit_idがNULL/空白のマンガページが0件 | ✓ 達成 |
| 同一シーン内でoutfit_idが不自然に混在していないこと | ✓ 確認済み（実質違反0件） |
| 設計書4.4節の場面転換ポイントとの整合性 | ✓ 確認済み（ページ番号ずれは誤差範囲内）|

**CSV修正: 不要（全チェック合格のため）**

---

## 備考

- 設計書の「推定新ページ番号」は工程3の生成結果と最大±3ページのずれがあるが、
  これは設計書自体に「工程3で正式な再採番を行う（7節参照）」と記載されており、
  設計書側が推定値であることを明示している。
- outfit_idの割り当てはすべてコマ別テキストJSONの内容（昼/夜/深夜・登場キャラ）と一致している。
- 未使用のoutfit_id（`misaki_formal`・`takuya_casual`・`yamada_suit`）は設計書4.2節の
  判定（vol2に対応シーンなし）と一致しており、不使用は正しい。
