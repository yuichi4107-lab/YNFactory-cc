---
topic: "Surface運用パターン比較（A/B/C）"
project: "jp-stock-daytrade"
status: "completed"
created: "2026-04-15"
assignee: "research"
sources:
  - url: "https://kabu.com/support/requirements.html"
    title: "推奨OS・ブラウザ・動作環境 - 三菱UFJ eスマート証券"
  - url: "https://kojinteki.net/2020/11/29/kabucomapi-auto-trading/"
    title: "kabuステーションAPIで完全自動売買を行う環境設定 - コジンテキネット"
  - url: "https://kojinteki.net/2021/07/11/sakura-vps-kabucomapi/"
    title: "VPSサーバ上でkabuステーションAPIを自動実行する方法 - コジンテキネット"
  - url: "http://snowballrichdad.xyz/post-3927/"
    title: "auカブコムのkabuステーションをWindowsのVPSで自動起動する方法"
  - url: "https://deep.tacoskingdom.com/blog/273"
    title: "Wine/Conoha VPS(Linux)にKabuステーションが入らなくなったのでPuppeteerで操作を代替 - Deep"
  - url: "https://www.onamae-desktop.com/spec/"
    title: "お名前.com デスクトップクラウド スペック・価格"
  - url: "https://www.onamae-desktop.com/"
    title: "お名前.com デスクトップクラウド 公式"
  - url: "https://www.kagoya.jp/vps/windows/"
    title: "KAGOYA CLOUD VPS Windows Server"
  - url: "https://support.kagoya.jp/vps/charge/charge_win.html"
    title: "KAGOYA CLOUD VPS サービス・料金一覧表"
  - url: "https://streamrental.com/vps-windows/"
    title: "Windows VPS比較: おすすめ仮想専用サーバー"
  - url: "https://note.com/hraps/n/n5f9b2092a6a5"
    title: "kabuステーション 自動ログイン＆二要素認証（Gmail API） - HRAPS"
  - url: "https://algo-trading.tokyo/python-line-notify-trade/"
    title: "Pythonで「買いシグナル」をLINEに届けるシステム構築 - algo-trading.tokyo"
---

# Surface運用パターン比較（A/B/C）

## サマリー
kabuステーションAPIはWindowsアプリ常駐が必須のためLinux VPS不可。Surface据置（A）は初期費用0円で月額0円だが停電/Wi-Fi断のリスクあり。Windows VPS（B）は月額2,400〜5,000円で99.99% SLA、運用安定。シグナル通知のみ自動＋手動発注（C）は月額ゼロ円で始められ学習コストも低い。**初期は(C)→慣れたら(A)で常時運用→資金拡大後(B)に移行** を推奨。

## 調査結果

### 前提: kabuステーション必須条件
- **Windows版kabuステーションアプリの起動＆ログイン状態が必須**。このアプリが動いていないとAPI（localhost:18080）は応答しない。
- **Linux VPS単体は不可**（ネイティブ版なし）。Wine経由での稼働はかつて一部報告あるが、現在のバージョンではインストール不可（tacoskingdom blog）。
- **アプリ自体の24時間連続稼働は非推奨**、1日1回再起動が無難（要検証）。
- ログイン時に2要素認証（メール認証コード）が求められるケースあり → Gmail API等で自動受信する工夫が必要。

### パターンA: Surface据置＋電源常時接続（自宅）

| 項目 | 内容 |
|---|---|
| **初期費用** | 0円（既存Surface利用） |
| **月額費用** | 0円（電気代月300〜500円程度、Wi-Fiは既存） |
| **安定性** | ★★☆☆☆ 停電、Wi-Fi切断、Windows Update強制再起動のリスク |
| **運用負荷** | ★★★☆☆ 毎朝8:00前に起動確認・アプリログイン確認 |
| **障害時影響** | 当日取引不可、復旧は在宅時のみ |
| **推奨用途** | 初期学習、フォワードテスト、小ロット運用 |

**実施要点**:
- 電源設定: スリープ/休止/ディスプレイオフを「なし」に設定、電源ボタンで何もしない設定
- Windows Update: アクティブ時間設定（取引時間外に更新）＋再起動を通知
- Wi-Fi: 可能なら有線LAN化、UPS（無停電電源装置、5,000〜15,000円）併用推奨
- kabuステーション: スタートアップに登録、自動ログインは公式には非対応（HRAPSのPuppeteer自動化は参考）
- リモートアクセス: 外出先からChrome Remote Desktop / Windows Remote Desktop でSurface操作
- **2026/10 Windows 10 サポート終了**: Surfaceが Windows 10の場合は要アップグレード

### パターンB: Windows VPS（主要プロバイダ比較）

**2025年時点の主要Windows VPS月額料金**:

| プロバイダ | プラン | スペック | 月額（1年契約） | 初期費用 | SLA |
|---|---|---|---|---|---|
| **お名前.com デスクトップクラウド** | 1.5G（FX特化） | CPU3コア/1.5GB/60GB SSD | 1,578円（初月980円） | 0円 | 99.99% |
| お名前.com | 2G | CPU3コア/2GB/60GB SSD | 2,408円 | 0円 | 99.99% |
| お名前.com | 4G | CPU3コア/4GB/80GB SSD | 3,758円 | 0円 | 99.99% |
| **KAGOYA CLOUD VPS Windows** | 3GB | CPU3コア/3GB/60GB SSD | 2,420円 | 0円 | 99.999% |
| KAGOYA CLOUD VPS Windows | 8GB | CPU4コア/8GB/100GB SSD | 4,840円 | 0円 | 99.999% |
| **Microsoft Azure B2s** | Windows Server | 2vCPU/4GB/30GB SSD | 約5,000〜8,000円（従量課金） | 0円 | 99.95% |
| **AWS EC2 t3.medium Windows** | Windows Server | 2vCPU/4GB | 約7,000〜9,000円（従量課金＋Windows License） | 0円 | 99.95% |
| **ConoHa for Windows Server** | 2GB | 3コア/2GB/100GB | 2,035円 | 0円 | 99.99% |

**kabuステーション稼働実績**:
- お名前.com デスクトップクラウド: FX用途が大半だがkabuステーション稼働報告あり（非公式）
- KAGOYA CLOUD VPS Windows: 個人ブログでkabuステーション常駐の事例あり（コジンテキネット等）
- ConoHa for Windows Server: 実績あり（国内ホスティング）

| 項目 | 内容 |
|---|---|
| **初期費用** | 0円〜（一部サービスで事務手数料あり） |
| **月額費用** | 2,000〜5,000円（KAGOYA 3GBが最小構成の推奨） |
| **安定性** | ★★★★★ データセンター運用、99.99% SLA |
| **運用負荷** | ★★★★☆ 一度構築すれば放置可能（月1回の保守のみ） |
| **障害時影響** | プロバイダ障害のみ（年数時間程度） |
| **推奨用途** | 本番運用、資金拡大後の安定稼働 |

**Windows VPSの具体要件**:
- メモリ: **3GB以上推奨**（kabuステーション2GB + OS 1GB程度）
- CPU: 3コア以上
- ストレージ: 60GB SSD 以上
- OS: Windows Server 2022 (Datacenter)
- RDP（リモートデスクトップ）でアクセス

### パターンC: シグナル検知のみ自動＋発注手動

| 項目 | 内容 |
|---|---|
| **初期費用** | 0円 |
| **月額費用** | 0円（LINE Messaging API無料枠・ConoHa Linux既存VPS利用） |
| **安定性** | ★★★★☆ 通知は既存のLinux VPSで24/365稼働可能 |
| **運用負荷** | ★★☆☆☆ スマホ通知を見て自分で発注、リアルタイム反応が必要 |
| **障害時影響** | 発注漏れリスク、就寝・外出時の機会損失 |
| **推奨用途** | 初期学習、戦略検証、手動確認しながら育てる |

**アーキテクチャ**:
1. 既存のConoHa Linux VPS上でPythonスクリプト常駐
2. データソースは **J-Quants API（無料/Light）・yfinance・株探スクレイプ** 等（kabu APIは使わない）
3. 8:45にシグナル条件を計算、ヒット銘柄を検出
4. LINE Messaging API（or Telegram Bot）でスマホにPUSH通知
5. オーナーがスマホからkabu.comアプリ / kabuステーション（自宅Surface）で手動発注

**LINE Notify代替**:
- LINE Notifyは 2025/3 でサービス終了 → **LINE Messaging API 無料プラン（月200通）** or **Telegram Bot（無料・無制限）** に移行
- 本プロジェクトで既に Telegram Bot運用実績あり → Telegramを推奨

**メリット**:
- Windowsアプリ/VPS不要で始められる
- kabuステーションAPIのProfessionalプラン条件を満たしていなくてOK
- 戦略のウォークフォワード評価に最適（実発注せずにシグナル履歴だけ貯められる）

**デメリット**:
- リアルタイム性が人間依存（寄付き9:00にスマホ見てない日は機会損失）
- 寄付き直前の発注（8:59）は手動では難しい、寄成 or 9:00以降のザラ場成行になる

### セクション4: kabuステーションがLinux VPS不可の理由
- **Windows専用アプリ**: .NET/WPFベースのWindowsネイティブアプリ。macOS/Linuxネイティブ版は提供されない。
- **Wine経由での稼働**: 過去バージョンでは一部稼働報告あり（kojinteki.net等）、**現行バージョンは不可**との報告（tacoskingdom）。
- 代替案（非公式）: Linux VPS上でPuppeteer + 仮想ブラウザ操作で「kabuステーションの代替」を構築する高難度手法。メンテ負荷大。
- **結論**: **Windowsアプリ常駐が必須条件**。Linux VPSのみでの運用は実質不可能。

### セクション5: 推奨パターン（オーナー向け）

**段階的移行プラン**:

1. **Phase 0〜1（〜3ヶ月）: パターンC（シグナル通知のみ）**
   - 既存のConoHa Linux VPS + Telegramで戦略検証
   - J-Quants API（無料）＋公開板スクリーニングで実運用前の勝率確認
   - 初期費用ほぼゼロで戦略の筋の良し悪しを見極める

2. **Phase 2（3〜6ヶ月）: パターンA（Surface据置）**
   - 戦略の勝率が見えたら、Surface自宅据置で実発注開始
   - UPS（5,000〜10,000円）導入で停電対策
   - 小ロット（1銘柄10〜30万円）で実績蓄積

3. **Phase 3（6ヶ月〜）: パターンB（Windows VPS）へ移行**
   - 運用資金100万円超 or 週10取引以上になったら Windows VPS へ
   - 推奨は **KAGOYA CLOUD VPS Windows 3GBプラン（月額2,420円）**（SLA 99.999%・電話サポートあり・個人ブログでkabu実績）
   - Surfaceは「開発・検証機」に降格、VPSは「本番機」

**なぜこの順序か**:
- 初期の戦略が「実用的勝率」に達するまでは発注自動化よりシグナル検証の方が価値が高い
- 小額時点で月額固定費（VPS）を払うのは損益インパクト大
- Surface据置は「無料だがリスク中」、慣らし運転に最適
- VPS移行は「資金と習熟が揃ったタイミング」で

## 結論
- kabuステーションはWindows必須、Linux VPS単体運用は実質不可。
- Phase 0はパターンC（Telegram通知＋手動発注）で月額0円・リスク最小スタートを推奨。
- Phase 2でパターンA（Surface据置＋UPS＋有線LAN）へ、Phase 3でパターンB（KAGOYA Windows VPS 3GB=月2,420円）に移行。
- Windows VPS選定の最有力は **KAGOYA CLOUD VPS Windows 3GB（月2,420円、SLA 99.999%、電話サポート）**。
- FX自動売買で実績豊富な **お名前.com デスクトップクラウド 2G（月2,408円）** も候補（ただしkabu稼働は非公式）。
- Surface既存機をフル活用できるため、初期費用0円で始められるのは大きなメリット。

## ネクストアクション
- [ ] Phase 0: 既存ConoHa Linux VPSにTelegram通知用Pythonスクリプトを設置、J-Quants無料プランで夜間バッチ実装
- [ ] Phase 0: テレグラムで朝の気配スナップショットが届く最小PoCを2週間運用
- [ ] Surface Windowsバージョン確認（Win10ならWin11アップグレード計画）
- [ ] Phase 2移行前にUPS（CyberPower CP550等、5,000円前後）購入
- [ ] Phase 3移行時はKAGOYA 3GBプランで1ヶ月試用→本契約（日割りや月額契約の条件要確認）
- [ ] kabuステーションの自動ログイン（二要素認証含む）の検証は Phase 2 段階で実施
