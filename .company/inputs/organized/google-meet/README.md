# Google Meet Organized Inputs

`00_GOOGLE_MEET_BOX/` から取り込んだGoogle Meet議事録・文字起こしの整理済み保存先。

`sync_google_meet.py` が raw / normalized / conversation を作成し、`organize_google_meet_inputs.py` がこのフォルダと `indexes/google-meet-*.md` を生成する。

## 生成内容

- 会議一覧
- 会議ごとの概要
- Notes / Transcript
- Next Steps / TODO候補
- raw原本と normalized Markdown への参照

TODO候補は確認前の候補として保存し、日別TODOへ直接反映しない。
