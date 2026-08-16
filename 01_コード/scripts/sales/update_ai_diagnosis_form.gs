/**
 * 無料AI導入診断フォームを v2仕様（14項目）へ更新し、あわせて編集権限を付与する。
 *
 * 仕様: 99_その他/company-records/marketing/social-auto-ops/forms/
 *       free-ai-diagnosis-v2-sns-consult-form-spec.md
 *
 * 実行方法:
 *   1. y-nakada@yn-factory.com でログインした状態で https://script.google.com/ を開く
 *   2. 「新しいプロジェクト」→ このファイルの中身を全部貼り付け
 *   3. 関数 backupCurrentForm を実行（現状のバックアップ。先にこれだけ実行する）
 *   4. 問題なければ 関数 updateForm を実行
 *
 * 注意:
 *   - 既存の回答データは消えない。回答スプレッドシートには新しい列が追加され、
 *     旧回答は旧列に残る。
 *   - 質問項目は総入れ替えになる。実行前に必ず backupCurrentForm を通すこと。
 */

var FORM_ID = '1-LCSyhjzq1PaCaWTKMR96zMiUpwTbIaUFv2dHKMa2f8';
var GRANT_EDITOR_TO = 'yuichi4107@gmail.com';

var FORM_TITLE = '無料AI導入診断 お申し込みフォーム';

var FORM_DESCRIPTION = [
  'AIを使ってみたい、または使い始めたものの、社内展開・業務整理・ルール作りで止まっている方向けの無料診断です。',
  '',
  '現在の業務を整理し、AI化しやすい業務、人が判断すべき業務、最初の30日で試す1業務を一緒に確認します。',
  '必要な場合のみ、AI顧問・導入プロジェクトについてご案内します。'
].join('\n');

var CONFIRMATION_MESSAGE = [
  'お申し込みありがとうございます。',
  '',
  '内容を確認し、無料AI導入診断についてご連絡します。',
  'AI顧問・導入支援が必要そうな場合も、まずは現在地の整理から進めます。'
].join('\n');

/** 仕様書の質問項目。順番がそのままフォームの並び順になる。 */
var ITEMS = [
  { type: 'text', title: 'お名前', required: true },
  { type: 'email', title: 'メールアドレス', required: true },
  { type: 'text', title: '会社名・屋号', required: false },
  {
    type: 'radio', title: 'あなたの立場に近いものを選んでください', required: true,
    choices: ['経営者・役員', '部門責任者・管理職', '実務担当者', '個人事業主', '情報収集', 'その他']
  },
  {
    type: 'radio', title: '会社・組織の規模を選んでください', required: true,
    choices: ['1名', '2〜9名', '10〜29名', '30〜100名', '101名以上', '回答しない']
  },
  {
    type: 'radio', title: '業種に近いものを選んでください', required: true,
    choices: ['士業・専門サービス', '制作・クリエイティブ', '製造業', '医療・福祉',
              '建設・不動産', '輸送・物流', '小売・店舗', 'その他']
  },
  {
    type: 'radio', title: '現在のAI活用状況を選んでください', required: true,
    choices: ['まだ使っていない', '個人で少し使っている', '一部の社員が使っている',
              '社内でルールを作り始めている', 'すでに業務利用しているが定着に課題がある']
  },
  {
    type: 'checkbox', title: '相談したい内容を選んでください', required: true,
    choices: ['業務効率化', '問い合わせ対応', '資料作成・提案書作成', '営業支援',
              '採用・教育・社内共有', 'AI利用ルール作り', '社内研修・AI定着',
              'AIチャットボット', 'SNS・note・ショート動画発信', 'まだ決まっていない']
  },
  { type: 'paragraph', title: '今いちばん困っている業務や、AIで軽くしたい作業を教えてください', required: true },
  {
    type: 'checkbox', title: '社内導入で不安なことを選んでください', required: false,
    choices: ['何から始めればよいか分からない', '社員が使ってくれるか不安',
              'AIに任せてよい範囲が分からない', '情報漏えい・著作権が不安',
              '利用ルールを作れていない', '費用対効果を説明しづらい', '特にない']
  },
  {
    type: 'radio', title: '希望する次のアクション', required: true,
    choices: ['無料診断を受けたい', 'まずはメールで相談したい',
              'AI顧問・導入支援も含めて相談したい', '資料だけ見たい', 'まだ決めていない']
  },
  {
    type: 'radio', title: 'どこでこの案内を見ましたか', required: false,
    choices: ['X', 'Instagram', 'TikTok', 'YouTube', 'note', '紹介', 'その他']
  },
  {
    type: 'radio', title: 'ご希望の連絡方法', required: true,
    choices: ['メール', 'オンライン面談', 'どちらでもよい']
  },
  { type: 'paragraph', title: '補足・事前に伝えておきたいこと', required: false }
];

/**
 * 現状のフォーム構成をJSONでDriveに保存する。updateForm より先に実行する。
 */
function backupCurrentForm() {
  var form = FormApp.openById(FORM_ID);
  var snapshot = {
    savedAt: new Date().toISOString(),
    title: form.getTitle(),
    description: form.getDescription(),
    confirmationMessage: form.getConfirmationMessage(),
    items: form.getItems().map(function (item) {
      var record = { title: item.getTitle(), type: String(item.getType()) };
      try {
        var typeName = String(item.getType());
        if (typeName === 'MULTIPLE_CHOICE') {
          record.choices = item.asMultipleChoiceItem().getChoices().map(function (c) { return c.getValue(); });
        } else if (typeName === 'CHECKBOX') {
          record.choices = item.asCheckboxItem().getChoices().map(function (c) { return c.getValue(); });
        } else if (typeName === 'LIST') {
          record.choices = item.asListItem().getChoices().map(function (c) { return c.getValue(); });
        }
      } catch (e) {
        record.choicesError = String(e);
      }
      return record;
    })
  };

  var name = 'form-backup-' + FORM_ID + '-' +
    Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd-HHmmss') + '.json';
  var file = DriveApp.createFile(name, JSON.stringify(snapshot, null, 2), MimeType.PLAIN_TEXT);

  Logger.log('バックアップを保存した: ' + file.getUrl());
  Logger.log('現在の質問数: ' + snapshot.items.length);
  return file.getUrl();
}

/**
 * フォームを v2仕様へ更新し、編集権限を付与する。
 */
function updateForm() {
  var form = FormApp.openById(FORM_ID);

  form.setTitle(FORM_TITLE);
  form.setDescription(FORM_DESCRIPTION);
  form.setConfirmationMessage(CONFIRMATION_MESSAGE);
  form.setCollectEmail(false);

  // 既存項目を削除する。インデックスがずれるので後ろから消す。
  var existing = form.getItems();
  for (var i = existing.length - 1; i >= 0; i--) {
    form.deleteItem(existing[i]);
  }

  ITEMS.forEach(function (spec) {
    switch (spec.type) {
      case 'text':
        form.addTextItem().setTitle(spec.title).setRequired(spec.required);
        break;
      case 'email':
        form.addTextItem()
          .setTitle(spec.title)
          .setRequired(spec.required)
          .setValidation(FormApp.createTextValidation()
            .setHelpText('メールアドレスの形式で入力してください')
            .requireTextIsEmail()
            .build());
        break;
      case 'paragraph':
        form.addParagraphTextItem().setTitle(spec.title).setRequired(spec.required);
        break;
      case 'radio':
        form.addMultipleChoiceItem()
          .setTitle(spec.title)
          .setChoiceValues(spec.choices)
          .setRequired(spec.required);
        break;
      case 'checkbox':
        form.addCheckboxItem()
          .setTitle(spec.title)
          .setChoiceValues(spec.choices)
          .setRequired(spec.required);
        break;
      default:
        throw new Error('未対応の項目種別: ' + spec.type);
    }
  });

  var granted = grantEditorAccess(form);

  Logger.log('更新完了。質問数: ' + form.getItems().length);
  Logger.log('回答用URL: ' + form.getPublishedUrl());
  granted.forEach(function (line) { Logger.log(line); });
}

/**
 * フォームと回答スプレッドシートに編集権限を付与する。
 * updateForm から呼ばれるが、単独でも実行できる。
 */
function grantEditorAccess(form) {
  form = form || FormApp.openById(FORM_ID);
  var results = [];

  try {
    form.addEditor(GRANT_EDITOR_TO);
    results.push('フォームに編集権限を付与: ' + GRANT_EDITOR_TO);
  } catch (e) {
    results.push('フォームへの権限付与に失敗: ' + String(e));
  }

  try {
    var destId = form.getDestinationId();
    if (destId) {
      SpreadsheetApp.openById(destId).addEditor(GRANT_EDITOR_TO);
      results.push('回答スプレッドシートに編集権限を付与: ' + destId);
    } else {
      results.push('回答スプレッドシートが未リンク。フォーム編集画面の「回答」タブでスプレッドシートを作成すること');
    }
  } catch (e) {
    results.push('スプレッドシートへの権限付与に失敗: ' + String(e));
  }

  results.forEach(function (line) { Logger.log(line); });
  return results;
}
