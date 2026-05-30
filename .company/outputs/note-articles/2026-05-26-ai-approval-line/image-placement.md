# Image Placement

## 見出し画像

- ファイル: `images/top.png`
- 配置: note見出し画像として設定。本文中には重複挿入しない。
- 役割: AI活用の前に、仕事の承認ラインを話し合う主題を一目で伝える。

## 本文中画像

1. `images/inside-01.png`
   - 挿入位置: 「AI活用で怖いのは、AIのミスだけではない」の後
   - 役割: AIが作った文章を人間が確認して止める場面。
2. `images/inside-02.png`
   - 挿入位置: 「決裁ラインは、細かすぎなくていい」の後
   - 役割: 社内ルールを軽く線引きしている場面。
3. `images/inside-03.png`
   - 挿入位置: 「うまくいかなかった使い方」の後
   - 役割: AI下書きをそのまま出さず、自分の言葉に戻す場面。

## 画像生成制約

- OpenAI API、openai-image-genスキル、APIキー、課金APIは使わない。
- ChatGPT Pro Web画面の gpt-image-2 / ChatGPT Images で生成する。
- Web生成不可の場合、APIへフォールバックせず `draft-status.md` に blocker を記録する。
- 基本スタイル: マンガ調、日本人、文字なし、読めるUIなし。
