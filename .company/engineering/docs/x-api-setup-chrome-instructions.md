# X API セットアップ指示（Claude in Chrome用）

Xにはログイン済みです。以下の手順を実行してください。

## Step 1: Developer Portal にアクセス

https://developer.x.com/en/portal/dashboard を開いてください。

初回の場合はDeveloper Agreementへの同意画面が出るので、同意してください。

## Step 2: Free プランを選択

プラン選択画面が表示されたら **Free** を選択してください。

## Step 3: アプリの作成

アプリ名を聞かれたら `yn-auto-post` と入力してください。

## Step 4: User Authentication Settings の設定

アプリのダッシュボードで：

1. 「User authentication settings」の「Set up」をクリック
2. 設定値：
   - **App permissions**: Read and Write
   - **Type of App**: Web App, Automated App or Bot
   - **Callback URL / Redirect URL**: `http://localhost`
   - **Website URL**: `https://ynfactory.online`
3. Save

## Step 5: Keys and Tokens の取得

「Keys and Tokens」タブで以下の4つを取得してください。Access Token / Secretが表示されていなければ「Generate」で生成してください。

- API Key
- API Key Secret
- Access Token
- Access Token Secret

4つの値を報告してください。

以上です。
