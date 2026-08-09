# Intake Raw Storage

`04_インプット/inputs/00_INPUT_BOX/` から取り込んだ外部インプットの raw 保存先。

## 構造

```text
intake/
  raw/
    YYYY-MM-DD/
      input-id/
        metadata.json
        files/
        normalized/
  state/
    drive_inbox_imported.json
```

## ルール

- `04_インプット/inputs/00_INPUT_BOX/` の原本は削除しない
- raw 保存先には、取り込み時点のコピーと metadata を保存する
- `normalized/` には、AIが読みやすいMarkdown化テキストを保存する
- organized から raw へ辿れるようにする
- `state/drive_inbox_imported.json` は重複取り込み防止用
- TODO候補は raw ではなく organized / indexes 側で確認する
