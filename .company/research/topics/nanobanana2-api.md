---
date: "2026-03-24"
topic: NanoBanana2 API仕様
status: completed
---

# NanoBanana2（Gemini画像生成）API仕様

## 概要

NanoBanana2は、Googleが提供するGemini 3.1 Flash Imageモデルの開発者向けブランド名。高速・高効率な画像生成・編集が可能で、Gemini APIを通じて利用できる。

**モデルID**: `gemini-3.1-flash-image-preview`

### 関連モデル一覧

| ブランド名 | モデルID | 特徴 |
|-----------|---------|------|
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 高速・高効率、大量生成向け（Preview） |
| Nano Banana Pro | `gemini-3-pro-image-preview` | スタジオ品質4K、複雑レイアウト・テキスト描画（Preview） |
| Nano Banana | `gemini-2.5-flash-image` | 初代モデル（Stable、2026-10-02終了予定） |

## エンドポイント

### REST API

```
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent
```

## 認証方法

APIキーを`x-goog-api-key`ヘッダーで渡す:

```
-H "x-goog-api-key: $GEMINI_API_KEY"
```

環境変数 `GOOGLE_AI_STUDIO_API_KEY` に設定済み（プロジェクト内）。
Python SDKを使う場合は `GOOGLE_API_KEY` 環境変数を自動検出する。

## リクエスト形式

### 必須フィールド

```json
{
  "contents": [
    {
      "parts": [
        {"text": "画像生成プロンプト"}
      ]
    }
  ],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"]
  }
}
```

### オプションパラメータ

| パラメータ | パス | 値 | 説明 |
|-----------|------|-----|------|
| aspectRatio | generationConfig.imageConfig.aspectRatio | "1:1", "16:9", "4:1" 等 | アスペクト比 |
| imageSize | generationConfig.imageConfig.imageSize | "512", "1K", "2K", "4K" | 画像サイズ |
| google_search | tools[].google_search | {} | Google検索グラウンディング（実在の対象を正確に描画） |

### フル例（JSON）

```json
{
  "contents": [
    {
      "parts": [
        {"text": "高級レストランの料理の写真を生成してください"}
      ]
    }
  ],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {
      "aspectRatio": "16:9",
      "imageSize": "2K"
    }
  }
}
```

## レスポンス形式

画像はbase64エンコードされた`inline_data`として返される:

```json
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "説明テキスト（TEXT modality指定時）"
          },
          {
            "inline_data": {
              "mime_type": "image/png",
              "data": "<base64エンコードされた画像データ>"
            }
          }
        ]
      }
    }
  ]
}
```

- `mime_type`: 通常 `image/png`
- `data`: base64エンコードされたバイナリデータ
- レスポンスにはテキストパートと画像パートの両方が含まれる可能性がある
- 全生成画像にはSynthIDウォーターマークが埋め込まれる

## 画像保存処理

### Python SDK使用時

```python
for part in response.parts:
    if part.inline_data:
        image = part.as_image()  # PIL.Imageオブジェクトに変換
        image.save("output.png")
```

### REST API（base64デコード）

```python
import base64

for part in response_json["candidates"][0]["content"]["parts"]:
    if "inline_data" in part:
        image_data = base64.b64decode(part["inline_data"]["data"])
        with open("output.png", "wb") as f:
            f.write(image_data)
```

### JavaScript

```javascript
for (const part of response.parts) {
  if (part.inlineData) {
    const buffer = Buffer.from(part.inlineData.data, 'base64');
    fs.writeFileSync('output.png', buffer);
  }
}
```

## サンプルコード（Python）

### 方法1: Google Gen AI SDK（推奨）

```python
from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.environ.get("GOOGLE_AI_STUDIO_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="猫が宇宙で浮かんでいるイラストを生成してください",
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="16:9",
            image_size="2K"
        ),
    )
)

# レスポンスから画像を保存
for i, part in enumerate(response.parts):
    if part.inline_data:
        image = part.as_image()
        image.save(f"output_{i}.png")
        print(f"画像を output_{i}.png に保存しました")
    elif part.text:
        print(f"テキスト: {part.text}")
```

### 方法2: curlコマンド

```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent" \
  -H "x-goog-api-key: $GOOGLE_AI_STUDIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{"text": "猫が宇宙で浮かんでいるイラスト"}]
    }],
    "generationConfig": {
      "responseModalities": ["TEXT", "IMAGE"],
      "imageConfig": {
        "aspectRatio": "16:9",
        "imageSize": "2K"
      }
    }
  }' | python3 -c "
import sys, json, base64
resp = json.load(sys.stdin)
for part in resp['candidates'][0]['content']['parts']:
    if 'inline_data' in part:
        data = base64.b64decode(part['inline_data']['data'])
        with open('output.png', 'wb') as f:
            f.write(data)
        print('画像を保存しました')
"
```

### 方法3: 画像編集（マルチターン）

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key=os.environ.get("GOOGLE_AI_STUDIO_API_KEY"))

# 既存画像を読み込んで編集
image = Image.open("input.png")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Content(parts=[
            types.Part.from_image(image),
            types.Part.from_text("背景を夕焼けに変更してください")
        ])
    ],
    config=types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    )
)

for part in response.parts:
    if part.inline_data:
        part.as_image().save("edited_output.png")
```

## 料金

| モデル | テキスト/画像入力 | 画像出力 |
|--------|-----------------|---------|
| gemini-3.1-flash-image-preview | $0.50/1Mトークン | $60.00/1Mトークン |
| gemini-3-pro-image-preview | $2.00/1Mトークン | $120.00/1Mトークン |
| gemini-2.5-flash-image | $0.30/1Mトークン | $0.039/画像 |

- 無料枠は現在なし（Preview期間中）
- Google Searchグラウンディング: 月5,000プロンプト無料、以降$14/1,000クエリ

## 注意事項

- `responseModalities`に`"IMAGE"`を含めないと画像が生成されない
- 全画像にSynthIDウォーターマークが自動付与される
- Preview版のため、モデルIDやパラメータが変更される可能性がある
- Python SDKでは`google-genai`パッケージをインストールする（`pip install google-genai`）

## 結論

NanoBanana2（gemini-3.1-flash-image-preview）は、Google AI Studio APIのgenerateContentエンドポイントで利用可能。認証はAPIキーヘッダー方式、レスポンスはbase64エンコードのinline_data形式で返される。Python SDKを使えば`as_image().save()`で簡潔に保存可能。スキル実装においては、Python SDKの利用が最も効率的。

## ネクストアクション

- [ ] Python SDKでの動作確認テスト
- [ ] スキル実装（engineering部署）: プロンプトからの画像生成関数の実装
- [ ] エラーハンドリングの設計（レート制限、不適切コンテンツフィルター等）
- [ ] コスト最適化: imageSize/aspectRatioのデフォルト値の決定
