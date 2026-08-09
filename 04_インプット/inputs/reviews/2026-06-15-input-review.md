---
date: 2026-06-15
type: input-review
source: process_daily_inputs.py
generated_at: 2026-06-15T14:17:02+09:00
lookback_days: 14
todo_auto_apply: false
---

# Input Review - 2026-06-15

## 判定

- Phase 1 output only: 日別TODO、HANDOFF、プロジェクト状態ファイルは自動更新しない。
- TODO候補は未判定として扱い、重複・完了済み・優先度を確認してから別工程で反映する。
- 機密・個人情報候補は本文を広げず、出典と検出語だけを確認対象にする。

## 選別ルール

- 今日見る: 期限が 14 日以内の未期限切れ候補、または直近 3 日以内の high / 機密候補。
- 期限切れ: 今日より前が期限の候補。自動で今日のTODOには上げず、棚卸しとして扱う。
- 通常バックログ: high でも古いもの、期限なしで直近性が弱いもの。必要な時だけ確認する。

## 更新結果

- skipped

## 在庫サマリ

- raw conversations: 202
- raw lifelogs: 127
- organized lifelogs: 63
- unorganized lifelog dates: 64
- latest missing lifelog dates: 2026-03-29, 2026-03-30, 2026-03-31, 2026-04-01, 2026-04-02, 2026-04-03, 2026-04-04, 2026-04-05, 2026-05-01, 2026-06-01
- raw Zoom files: 18
- organized Zoom files: 18
- raw Google Meet files: 0
- organized Google Meet files: 0
- external organized inputs: 2
- indexes: 15
- secretary inbox lifelog insights: 63

## 今日見るべきTODO候補

- [ ] 税務申告日の調整（確定日29日、申告日1日）
  - date: 2026-06-03
  - source: `.company/inputs/organized/lifelogs/2026-06-03-lifelog-insights.md`
  - index: lifelog TODO:190
  - priority: high
  - due: 2026-06-29
  - route_decision: 未判定
- [ ] LINE友だち追加、または概要欄からの追加を促し、AI勉強会へ案内する
  - date: 2026-06-13
  - source: `.company/inputs/organized/lifelogs/2026-06-13-lifelog-insights.md`
  - index: lifelog TODO:17
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 日本語字幕付きショート動画の自動生成・自動投稿システムを開発する。正確性の確保も重視する。
  - date: 2026-06-13
  - source: `.company/inputs/organized/lifelogs/2026-06-13-lifelog-insights.md`
  - index: lifelog TODO:18
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuichi氏の新しい仕事に関する連絡を継続し、進捗を確認する。
  - date: 2026-06-12
  - source: `.company/inputs/organized/lifelogs/2026-06-12-lifelog-insights.md`
  - index: lifelog TODO:23
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuichi氏の新しい仕事のデスクトップデータを整理し、サーバー（または適切な場所）へ移行する。
  - date: 2026-06-12
  - source: `.company/inputs/organized/lifelogs/2026-06-12-lifelog-insights.md`
  - index: lifelog TODO:24
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuichi氏のアドレスのメール受信設定を行う。
  - date: 2026-06-12
  - source: `.company/inputs/organized/lifelogs/2026-06-12-lifelog-insights.md`
  - index: lifelog TODO:25
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 有料AIプラン（例: ChatGPTの有料プラン）の導入を検討・実施する。
  - date: 2026-06-12
  - source: `.company/inputs/organized/lifelogs/2026-06-12-lifelog-insights.md`
  - index: lifelog TODO:28
  - priority: high
  - due: -
  - route_decision: 未判定

## 期限切れ・棚卸し候補

- [ ] デューダ取材対応を行う（夕方）
  - date: 2026-06-10
  - source: `.company/inputs/organized/lifelogs/2026-06-10-lifelog-insights.md`
  - index: lifelog TODO:63
  - priority: high
  - due: 2026-06-10
  - route_decision: 未判定
- [ ] Yuichi氏との打ち合わせ設定（今週土曜日10時半頃）
  - date: 2026-06-08
  - source: `.company/inputs/organized/lifelogs/2026-06-08-lifelog-insights.md`
  - index: lifelog TODO:91
  - priority: high
  - due: 2026-06-13
  - route_decision: 未判定
- [ ] 取材対応の準備と実施（10日16時半頃）
  - date: 2026-06-05
  - source: `.company/inputs/organized/lifelogs/2026-06-05-lifelog-insights.md`
  - index: lifelog TODO:134
  - priority: high
  - due: 2026-06-10
  - route_decision: 未判定
- [ ] コンサルティング面談の実施（2026-06-08 10:30、30分程度）
  - date: 2026-06-05
  - source: `.company/inputs/organized/lifelogs/2026-06-05-lifelog-insights.md`
  - index: lifelog TODO:138
  - priority: high
  - due: 2026-06-08
  - route_decision: 未判定
- [ ] 出張者説明会（午前10時8階会議室、午後3時6階会議室）に参加または確認する
  - date: 2026-06-04
  - source: `.company/inputs/organized/lifelogs/2026-06-04-lifelog-insights.md`
  - index: lifelog TODO:174
  - priority: high
  - due: 2026-06-04
  - route_decision: 未判定

## 通常バックログ候補

- [ ] 2026年6月分の給料チェックを開始し、7月上旬の支払いに間に合わせる
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:36
  - priority: high
  - due: 2026-07-01
  - route_decision: 未判定
- [ ] パスワード関連の問題を確認・解決する
  - date: 2026-06-09
  - source: `.company/inputs/organized/lifelogs/2026-06-09-lifelog-insights.md`
  - index: lifelog TODO:70
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuichiに対し、写真や個人情報利用に関する個人情報取り扱いの文章を作成するよう指示。
  - date: 2026-06-06
  - source: `.company/inputs/organized/lifelogs/2026-06-06-lifelog-insights.md`
  - index: lifelog TODO:126
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] マイナンバーの提出要否を確認し、郵送で送る形にする
  - date: 2026-06-04
  - source: `.company/inputs/organized/lifelogs/2026-06-04-lifelog-insights.md`
  - index: lifelog TODO:183
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuumi-sanの管理表を作成する
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:37
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] Yuichi関連の請求書とセコムの書類が不足しているため、再発送を依頼する
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:38
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 採用活動のため、来週から「龍蛇」で8週間募集をかける
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:39
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 「アイコーダー」の「基本給食品対応」という運用が正しいか確認し、履歴を残す
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:40
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 休憩時間運用の実態（17時以降の休憩報告、休憩時間ゼロの記載）について、いつからの運用か病院側の認識を含め調査し記録する
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:42
  - priority: high
  - due: -
  - route_decision: 未判定
- [ ] 未払いの請求書が到着次第、振り込みを実行する
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog TODO:44
  - priority: high
  - due: -
  - route_decision: 未判定

## 決定事項候補

- [ ] 仕事の一つとして動画編集に取り組むことを決定。
  - date: 2026-06-13
  - source: `.company/inputs/organized/lifelogs/2026-06-13-lifelog-insights.md`
  - index: lifelog decisions:16
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 費用対効果を鑑み、人件費削減のため、組織的または個人的な業務においてAI活用を積極的に推進する方針。
  - date: 2026-06-12
  - source: `.company/inputs/organized/lifelogs/2026-06-12-lifelog-insights.md`
  - index: lifelog decisions:20
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 新規営業を一時的に封印し、組織の管理体制の立て直しを優先する。
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog decisions:24
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 新規事業よりも既存事業の立て直しを最優先課題とする。
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog decisions:25
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 事業拡大には慎重な姿勢を保ちつつも、面接は継続して実施する。
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog decisions:26
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 入社処理関連書類の作成・回送は、押印のタイミングを考慮して先行して進める方針とする。
  - date: 2026-06-11
  - source: `.company/inputs/organized/lifelogs/2026-06-11-lifelog-insights.md`
  - index: lifelog decisions:27
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 求人票に「スタッフ管理・指導、現場作業も発生する」旨の記載を米印程度で追加する。
  - date: 2026-06-10
  - source: `.company/inputs/organized/lifelogs/2026-06-10-lifelog-insights.md`
  - index: lifelog decisions:31
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 給与体系を経験者・未経験者で二段階に設定する。
  - date: 2026-06-10
  - source: `.company/inputs/organized/lifelogs/2026-06-10-lifelog-insights.md`
  - index: lifelog decisions:32
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 職種名を「現場管理」「管理マネージャー」のように求職者に伝わりやすく柔らかな表現に変更する。
  - date: 2026-06-10
  - source: `.company/inputs/organized/lifelogs/2026-06-10-lifelog-insights.md`
  - index: lifelog decisions:33
  - priority: -
  - due: -
  - route_decision: 未判定
- [ ] 求人掲載日を一旦6月18日に設定し、準備が間に合わない場合は6月22日に延期する。
  - date: 2026-06-10
  - source: `.company/inputs/organized/lifelogs/2026-06-10-lifelog-insights.md`
  - index: lifelog decisions:34
  - priority: -
  - due: -
  - route_decision: 未判定

## 機密・個人情報候補

- [ ] 機密・個人情報候補を確認
  - date: 2026-06-09
  - matched_terms: パスワード
  - source: `.company/inputs/organized/lifelogs/2026-06-09-lifelog-insights.md`
  - index: lifelog TODO:70
  - route_decision: 要確認
- [ ] 機密・個人情報候補を確認
  - date: 2026-06-09
  - matched_terms: パスワード
  - source: `.company/inputs/organized/lifelogs/2026-06-09-lifelog-insights.md`
  - index: lifelog TODO:75
  - route_decision: 要確認
- [ ] 機密・個人情報候補を確認
  - date: 2026-06-06
  - matched_terms: 個人情報
  - source: `.company/inputs/organized/lifelogs/2026-06-06-lifelog-insights.md`
  - index: lifelog TODO:126
  - route_decision: 要確認
- [ ] 機密・個人情報候補を確認
  - date: 2026-06-04
  - matched_terms: マイナンバー
  - source: `.company/inputs/organized/lifelogs/2026-06-04-lifelog-insights.md`
  - index: lifelog TODO:183
  - route_decision: 要確認
- [ ] 機密・個人情報候補を確認
  - date: 2026-06-04
  - matched_terms: マイナンバー
  - source: `.company/inputs/organized/lifelogs/2026-06-04-lifelog-insights.md`
  - index: lifelog decisions:68
  - route_decision: 要確認

## 未整理バックログ

- unorganized lifelog dates: 64
- sample: 2025-11-08, 2025-12-21, 2025-12-22, 2025-12-23, 2025-12-24, 2025-12-25, 2025-12-26, 2026-01-06
- latest: 2026-03-31, 2026-04-01, 2026-04-02, 2026-04-03, 2026-04-04, 2026-04-05, 2026-05-01, 2026-06-01

## 次の処理

- レビュー内の `route_decision` を見て、必要なものだけ今日のTODO・プロジェクトファイル・保留へ振り分ける。
- `--force` で再生成するとこのファイルは上書きされるため、手動判定を書き込んだ後は再生成しない。
- Phase 2 で承認付きの TODO 反映コマンドを追加する。
