# KDP表紙 JPEG納品 要件定義書

- 確定日: 2026-08-02
- 対象書籍: 『日本の左派・リベラルは、なぜ自滅するのか』

## ゴール

現行のKDP表紙PNGを視覚品質を保ったJPEGへ変換し、KDPへそのまま渡せる `cover.jpg` を作成する。変換処理はJPEG圧縮とRGB化だけに限定し、原本PNGと既存EPUB 2点を一切変更しない。

## 入出力

### 入力

- `KDP出版用/cover.png`

### 出力

- `KDP出版用/cover.jpg`

### 変更禁止・不変確認対象

- `KDP出版用/cover.png`
- `KDP出版用/日本の左派リベラルはなぜ自滅するのか.epub`
- `epub/日本の左派リベラルはなぜ自滅するのか.epub`

## スコープ

### 実施すること

1. Pillowを使ってPNGをRGB JPEGへ変換する。
2. JPEG保存パラメータを次の値に固定する。
   - `quality=95`
   - `subsampling=0`
   - `optimize=True`
   - `progressive=True`
3. 出力を1024×1536、RGB、JPEGとして保存する。
4. PNGと既存EPUB 2点の変換前SHA-256を記録する。
5. 変換後に同じ3点のSHA-256を再計算し、不変を確認する。
6. PNGをRGBとして読み込んだ画素と、JPEGを復号したRGB画素のPSNRを計算する。
7. JPEGの形式、寸法、モード、progressive、subsampling、ファイルサイズ、SHA-256を検証する。

### 実施しないこと

- リサイズ、クロップ、回転、色調補正、シャープ化、ノイズ除去、文字・画像の追加または削除。
- PNG原本の上書き・再保存。
- EPUBの展開、再圧縮、再生成、上書き。
- KDPへのアップロード・公開。

## 完了条件

- [ ] `cover.jpg` がJPEG形式で生成されている。
- [ ] 寸法が1024×1536、モードがRGBである。
- [ ] `quality=95`、`subsampling=0`、`optimize=True`、`progressive=True` で保存している。
- [ ] JPEGファイルからprogressive設定とsubsampling 0を確認できる。
- [ ] 原本RGB画素とJPEG復号画素のPSNRが35 dB以上である。
- [ ] PNGと既存EPUB 2点の変換前後SHA-256がそれぞれ一致する。
- [ ] JPEGのファイルサイズとSHA-256を記録している。
- [ ] PNG・EPUBには書き込みを行っていない。

## 品質基準（100点）

| 項目 | 配点 |
|---|---:|
| quality 95・subsampling 0・optimize・progressiveの指定 | 20 |
| JPEG・1024×1536・RGBの技術仕様 | 15 |
| PSNR 35 dB以上 | 20 |
| PNG原本のSHA-256不変 | 15 |
| 既存EPUB 2点のSHA-256不変 | 20 |
| ファイルサイズ・SHA-256・検証値の記録 | 10 |

合格基準: 85点以上。寸法違い、RGB以外、PSNR 35 dB未満、PNGまたはいずれかのEPUBのハッシュ変化は配点にかかわらず不合格とする。

