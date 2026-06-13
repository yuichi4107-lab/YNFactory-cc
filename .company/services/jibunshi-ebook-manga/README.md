# 自分史 文字版＋フル漫画版サービス

祖父母・シニア層の人生を、家族に残せる「完全文字版」と「完全漫画版」の二本立てで制作するサービス運用パッケージです。

## 使い方

1. LPまたは紹介導線から問い合わせを受ける
2. `tools/create_order_package.py` で受注フォルダを作る
3. `input/` にヒアリング回答、写真、音声文字起こし、同意状況を保存する
4. 完全文字版を `theme-to-ebook` の文字版モードで作る
5. 文字版の承認後、`theme-to-ebook-to-manga` / `ebook-to-manga` で完全漫画版を作る
6. `qa/` で事実確認、表記、個人情報、公開範囲をチェックする
7. 承認済みの納品物だけを `delivery/` に置く

## 重要ルール

- 文字版は「本文中心」ではなく「完全文字版」。漫画ページや漫画パートを混ぜない
- 漫画版は文字版を要約したおまけではなく、独立して読めるフル漫画版として制作する
- 個人名、写真、病歴、家族関係、職歴、住所、学校名などは公開範囲を必ず確認する
- KDP公開、外部送信、決済、予約フォーム公開は、直前にオーナーの明示承認を取る

## 標準フォルダ

```text
.company/outputs/jibunshi-orders/{order-id}/
├── project.md
├── input/
├── production/
├── outputs/
│   ├── text-edition/
│   └── manga-edition/
├── qa/
└── delivery/
```

## 関連スキル

- `.agents/skills/jibunshi-ebook-manga-service/SKILL.md`
- `.codex/skills/theme-to-ebook/SKILL.md`
- `.codex/skills/theme-to-ebook-to-manga/SKILL.md`
- `.codex/skills/ebook-to-manga/SKILL.md`
