---
title: ショート動画 CTA受け皿運用メモ
created: 2026-06-19
status: prepared
primary_lp: https://ai.yn-factory.com/
primary_form: https://docs.google.com/forms/d/e/1FAIpQLScFeFulq-ol1DzeUADBFdORNOFtZYlc4Ap-7j9OqJ8Hcb5W0Q/viewform
---

# ショート動画 CTA受け皿運用メモ

## 目的

X / Instagram / TikTok / YouTubeショートから来た視聴者を、AI導入コンサル・AI顧問契約の見込み客として受け止める。

入口は「無料AI導入診断」とし、いきなり有料相談へ誘導しない。フォーム回答後に、必要な人だけ個別Zoom相談・月次AI顧問・3か月集中導入プロジェクトへ進める。

## 現在の受け皿

- LP: https://ai.yn-factory.com/
- 申込フォーム: https://docs.google.com/forms/d/e/1FAIpQLScFeFulq-ol1DzeUADBFdORNOFtZYlc4Ap-7j9OqJ8Hcb5W0Q/viewform
- ローカルLP原稿: `.company/outputs/lp/ai-introduction-consult-publish/lp-copy.md`
- ローカルLPファイル: `.company/outputs/lp/ai-introduction-consult-publish/index.html`

注意: 2026-06-19時点ではローカルLP文面をSNS導線向けに更新済み。公開反映はCloudflare Pagesへのデプロイ承認後に行う。

## プラットフォーム別URL

UTMは後でアクセス解析を入れた時に流入元を判別しやすくするために付ける。LP自体は同じでよい。

| プラットフォーム | プロフィール/概要欄に置くURL |
|---|---|
| X | `https://ai.yn-factory.com/?utm_source=x&utm_medium=profile&utm_campaign=shorts_ai_consult` |
| Instagram | `https://ai.yn-factory.com/?utm_source=instagram&utm_medium=profile&utm_campaign=shorts_ai_consult` |
| TikTok | `https://ai.yn-factory.com/?utm_source=tiktok&utm_medium=profile&utm_campaign=shorts_ai_consult` |
| YouTube | `https://ai.yn-factory.com/?utm_source=youtube&utm_medium=channel&utm_campaign=shorts_ai_consult` |

## 動画末尾CTA

実装: shorts-factory は投稿時に `shorts-factory/src/platform_copy.py` で媒体別の投稿文・説明文・CTAを生成する。新規キューには `platform_copy` として保存され、旧キューは投稿時に同じルールで補完される。

### 共通の基本形

```text
自社でAIをどう使えばいいか迷っている方は、プロフィールの無料AI導入診断からどうぞ。
```

### X

```text
AI導入はツール選びより、最初の1業務の決め方で差が出ます。
自社の場合を整理したい方は、プロフィールの無料AI導入診断へ。
```

### Instagram

```text
保存して、AI導入前のチェックに使ってください。
自社で何から始めるべきか知りたい方は、プロフィールの無料AI導入診断へ。
```

### TikTok

```text
AI導入で止まっている会社は、プロフィールの無料診断で「最初の1業務」を整理できます。
```

### YouTubeショート

```text
AIを社内にどう定着させるか迷っている方へ。
無料AI導入診断はこちら:
https://ai.yn-factory.com/?utm_source=youtube&utm_medium=shorts_description&utm_campaign=shorts_ai_consult
```

## 申込後の一次対応

フォーム回答が入ったら、原則24時間以内に次の3区分へ分ける。

| 区分 | 条件 | 初回対応 |
|---|---|---|
| A: 顧問・導入PJ候補 | 経営者/部門責任者、会社規模あり、社内展開や運用課題が明確 | 個別Zoom相談へ案内 |
| B: 無料診断のみ | 相談内容はあるが、導入規模や予算感が不明 | 追加質問を1通送る |
| C: 情報収集 | 資料だけ、個人学習、テーマが曖昧 | note/LP/ウェビナーへ誘導 |

## 初回返信テンプレート

### A: 顧問・導入PJ候補

```text
お申し込みありがとうございます。

内容を拝見すると、単発のツール相談というより、
「どの業務からAI化するか」「社内でどう定着させるか」を整理すると効果が出やすそうです。

まず30分ほど、現在の業務とAI導入の優先順位を確認できればと思います。
以下よりご都合のよい日時をお選びください。

{予約URL}
```

### B: 無料診断のみ

```text
お申し込みありがとうございます。

無料診断の前に、1点だけ確認させてください。
今いちばんAIで軽くしたい業務は、次のうちどれに近いでしょうか。

1. 資料作成・文章作成
2. 問い合わせ対応
3. 営業・提案支援
4. 採用・教育・社内共有
5. まだ決まっていない
```

### C: 情報収集

```text
お申し込みありがとうございます。

まずはAI導入の全体像を把握したい段階かと思います。
最初は「ツール選び」よりも、「毎週くり返している1業務」を見つけるところから始めると進めやすいです。

参考になる資料・記事を整理してお送りします。
```

## 公開反映時のチェック

- LPの主CTAがGoogleフォームへ遷移する
- X / Instagram / TikTok / YouTube用のプロフィールURLが決まっている
- フォーム回答通知が有効
- 回答スプレッドシートを確認できる
- プロフィール文のリンク先が `ai.yn-factory.com` に統一されている
- 公開後にスマホ表示でファーストビューとCTAを確認する
