# 絵本LPから自分史LPへの導線追加

作成日: 2026-06-10 (水)

## ゴール

既存の個別絵本販売LPに、自分史LPへ遷移する導線を追加する。

## スコープ

実施:

- 公開中の絵本LPリポジトリ `yuichi4107-lab/yn-ehon-lp` をローカル複製
- `index.html` に `#jibunshi` セクションを追加
- ナビゲーションに「自分史」を追加
- `styles.css` にレスポンシブ対応のスタイルを追加
- デスクトップ/モバイルでレンダリング確認

未実施:

- GitHub Pagesへのpush
- `https://www.ynfactory.online/jibunshi/` の本番公開確認
- 決済・フォーム接続

## 追加した導線

リンク先:

```text
https://www.ynfactory.online/jibunshi/
```

セクション見出し:

```text
お子さまの絵本だけでなく、
祖父母の人生も一冊に。
```

## 検証

- デスクトップ幅 `1440 x 1100` でレンダリング
- モバイル幅 `390 x 844` でレンダリング
- どちらも横はみ出しなし
- CTAリンク先が `https://www.ynfactory.online/jibunshi/` であることを確認

## 品質スコア

91 / 100 PASS

## 残り

本番公開は外部反映に当たるため、オーナーの明示承認後に `yn-ehon-lp` リポジトリでcommit/pushする。
