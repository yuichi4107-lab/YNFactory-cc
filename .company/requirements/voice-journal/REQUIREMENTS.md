---
project: voice-journal
title: 常時録音→自動文字起こし→inbox蓄積サービス 設計書(spec)
created: 2026-05-31
status: approved-design
related: voice-recorder (ブラウザ録音アプリ。別物)
---

# voice-journal 設計書

## 1. ゴール
PC起動中、マイク音声とPCの再生音(システム音声)を常時録音し、1時間ごとのセグメントを
ローカルWhisper(faster-whisper)で文字起こしして `.company/secretary/inbox/` に日付別で蓄積する。
文字起こしが完了した音声ファイルは削除する。全工程をPC起動時から自動・無人で回す。

## 2. スコープ
### やること
- マイク＋PC再生音(WASAPIループバック)の同時録音
- 1時間(クロック整列)ごとのセグメント自動ローテーション
- 各セグメントを16kHzモノにミックスし faster-whisper で文字起こし(日本語)
- 文字起こし結果を `.company/secretary/inbox/YYYY-MM-DD.md` に時刻見出し付きで追記
- 文字起こし成功後に該当音声を削除(失敗時は保持してリトライ)
- Windowsタスクスケジューラ「ログオン時」起動＋クラッシュ自動再起動
- 起動時の未処理セグメント回収(取りこぼし防止)
- PAUSE.flag による録音一時停止(プライバシー手段)

### やらないこと
- ブラウザUI / リアルタイム字幕表示 / 話者分離 / 要約・後処理AI
- クラウド保存・外部送信(音声は外部に出さない。ローカル完結)
- 1ファイル化のリアルタイム音声ミキシング(B案不採用)

## 3. 全体構成(A案: 2トラック録音→文字起こし時ミックス)
```
[録音スレッド] マイク(InputStream) + PC音(WASAPI loopback InputStream)
        │   それぞれ <ts>_mic.flac / <ts>_sys.flac に書き込み
        │   毎正時(SEGMENT_SECONDS)でローテーション→完成ペアをキューへ
        ▼
   [Queue] (start_ts, mic_path, sys_path)
        ▼
[ワーカースレッド] audio_mix で16kモノ合成 → faster-whisper transcribe
        ▼
   inbox_writer: .company/secretary/inbox/YYYY-MM-DD.md に「## HH:MM–HH:MM」見出し+本文を追記
        ▼
   成功 → 音声2ファイル削除 / 失敗 → 保持しリトライ(最大N回)→超過でfailed/へ退避
```
音声の一時ファイルは **Googleドライブ外のローカル(既定 `C:\voice-journal-temp\`)** に置く。
inbox(Drive)へ行くのは **テキストのみ**。

## 4. コンポーネント(独立・テスト可能)
| ファイル | 役割 | 主インターフェース |
|---|---|---|
| `service.py` | 統括(エントリ)。録音スレッド+ワーカースレッド起動、終了/ PAUSE / 孤児回収 | `main()` |
| `recorder.py` | `AudioRecorder`: mic+loopbackストリーム開閉、FLAC書込、1hローテーション | `start()/stop()`, `on_segment(callback)` |
| `audio_mix.py` | 純関数: FLAC読込→16kモノ resample→2系統mix(クリップ保護) | `mix_to_16k_mono(mic, sys)->np.ndarray` |
| `transcriber.py` | `Transcriber`: モデルロード、セグメント文字起こし | `transcribe(mic_path, sys_path)->{text,language,duration}` |
| `inbox_writer.py` | inbox日付ファイルへ追記(なければ生成) | `append(start_dt,end_dt,text)` |
| `config.json` | 設定値 | — |
| `requirements.txt` | 依存(sounddevice, soundfile, faster-whisper, numpy, soxr) | — |
| `setup_autostart.ps1`/`remove_autostart.ps1` | タスクスケジューラ登録/解除 | — |
| `start.bat` (ASCII) | 手動起動(テスト用) | — |
| `README.md` (日本語) | セットアップ・運用・停止・プライバシー・トラブル対応 | — |
| `tests/` | test_audio_mix / test_inbox_writer / test_rotation / 統合(短縮セグメント) | — |

## 5. 設定スキーマ(config.json)
```json
{
  "temp_dir": "C:\\voice-journal-temp",
  "inbox_dir": "g:\\マイドライブ\\YNFactory-cc\\.company\\secretary\\inbox",
  "segment_seconds": 3600,
  "align_to_clock_hour": true,
  "mic_device": null,
  "loopback_device": null,
  "capture_system_audio": true,
  "whisper_model": "small",
  "whisper_compute_type": "int8",
  "whisper_device": "auto",
  "language": "ja",
  "delete_audio_after_transcribe": true,
  "max_transcribe_retries": 3
}
```

## 6. 技術仕様の要点
- **ループバック**: Windows WASAPI。`sd.InputStream(..., extra_settings=sd.WasapiSettings(loopback=True))` を既定出力デバイスに対して開く。マイクは通常の `InputStream`。
- **保存形式**: FLAC(可逆圧縮, soundfile)。ネイティブのサンプルレート/チャンネルで録音。
- **ミックス**: 文字起こし直前に両FLACを soxr で16kHzへリサンプル→モノ化→加算→ピーク正規化(クリップ回避)。Whisperは16kモノ前提なので変換は1回で済む。
- **ローテーション**: `align_to_clock_hour=true` なら初回は次の正時まで、その後 `segment_seconds` 間隔。ファイル名は開始時刻 `YYYYMMDD_HHMMSS`。
- **モデル**: faster-whisper `small`/int8 を既定。`whisper_device:auto` でCUDA検出時はGPU。
- **スループット保護**: ワーカーは逐次処理。キュー長が閾値(例:3)超で警告ログ。24h運用は「文字起こしが録音より遅いと無限に滞留」するため導入後に実測し、必要ならモデル降格 or GPU化。

## 7. エラーハンドリング
- ループバック非対応/出力デバイス無 → ログ＋ `capture_system_audio=false`(マイクのみ)で継続、inbox先頭に注記。
- マイク取得失敗 → エラーログ、一定間隔で再オープン試行。
- 文字起こし例外 → リトライ計数(サイドカー `<ts>.retry`)、音声保持。`max_transcribe_retries` 超過で `temp_dir/failed/` へ退避しキューを止めない。
- inbox書込失敗 → 音声を削除せず保持、ログ。
- `PAUSE.flag` 検出 → 録音停止(ストリームclose)。除去で再開。
- クラッシュ → タスクスケジューラが再起動。起動時 `temp_dir` の未処理セグメントを回収。

## 8. inbox追記フォーマット例
```markdown
# 2026-05-31 音声ログ

## 14:00–15:00
（文字起こし本文…）

## 15:00–16:00
（文字起こし本文…）
```

## 9. テスト計画
- `test_audio_mix`: 合成サイン波で resample/mix の形状・クリップ無しを検証。
- `test_inbox_writer`: 新規生成・見出し整形・上書きでなく追記、を検証。
- `test_rotation`: 擬似クロックで正時整列のセグメント境界計算を検証。
- 統合(自動/手動): `segment_seconds=20` で約1分稼働→inbox日付ファイルに複数追記、temp音声が削除される、を確認。
- スループット実測: 選択モデルで「1セグメントの文字起こし時間 < セグメント長」を確認。

## 10. 受入(品質チェック)基準 — 100点満点 / 合格85点
| # | 項目 | 配点 |
|---|---|---|
| 1 | mic+loopback録音が動作し1hローテーションする | 20 |
| 2 | faster-whisperでセグメントが文字起こしされる(日本語) | 20 |
| 3 | inbox日付ファイルへ時刻見出し付きで正しく追記 | 15 |
| 4 | 成功時のみ音声削除・失敗時保持＋リトライ/退避 | 10 |
| 5 | タスクスケジューラ登録/解除スクリプトが機能(ログオン時起動・再起動設定) | 10 |
| 6 | ローカル一時保存(Drive非汚染)・FLAC・config外出し | 10 |
| 7 | エラーハンドリング(ループバック非対応/マイク無/例外/PAUSE) | 10 |
| 8 | README(日本語)＋テスト完備 | 5 |
| 加点 | GPU自動利用(+3) / バックログ警告(+2) | +5 |

## 11. 運用・プライバシー注意
- マイク＋PC音の24h録音は通話相手・同席者の声も記録する。録音/記録の同意など運用配慮はオーナー責任。
- 音声は外部送信せずローカルで完結(文字起こしもローカル)。テキストのみDriveのinboxへ。
- 一時音声は処理後削除。`failed/` の退避音声のみ手動確認が必要な場合がある。

## 12. 既知の制約
- WASAPIループバックは「既定の出力デバイス」を録る。出力先を切替えた場合は再起動 or デバイス再選択が必要。
- CPUのみ環境では大型モデル(medium/large)が実時間を超える可能性 → 既定small/int8、必要に応じ調整。
- マイクとPC音は別ストリームのため厳密な時刻同期はしない(文字起こし用途では実害なし)。
