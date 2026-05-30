const pptxgen = require("pptxgenjs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const assets = path.join(root, "assets");
const out = path.join(root, "output", "nichibi-company-profile-stylish-20260519.pptx");

const pptx = new pptxgen();
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.author = "YNFactory";
pptx.company = "YNFactory";
pptx.subject = "日美株式会社 会社説明資料 stylish version";
pptx.title = "日美株式会社 会社説明資料";
pptx.lang = "ja-JP";
pptx.theme = {
  headFontFace: "Hiragino Sans",
  bodyFontFace: "Hiragino Sans",
  lang: "ja-JP",
};

const C = {
  bone: "F8F3E8",
  cream: "FFF8EC",
  paper: "FBFBF6",
  ink: "182635",
  ink2: "243544",
  mist: "EEF3EF",
  green: "008A65",
  teal: "00A7A0",
  cobalt: "2667FF",
  sky: "78B7FF",
  coral: "F26D5B",
  orange: "FF9F1C",
  yellow: "FFD166",
  magenta: "C23B75",
  violet: "7561E8",
  white: "FFFFFF",
  gray: "63707A",
};

const A = [C.green, C.cobalt, C.coral, C.orange, C.teal, C.magenta, C.violet, C.yellow];

function logo(slide, dark = false) {
  slide.addImage({ path: path.join(assets, "nichibi-logo.png"), x: 0.58, y: 0.42, w: 1.72, h: 0.41 });
  slide.addText("NICHIBI COMPANY PROFILE", {
    x: 10.15, y: 0.46, w: 2.55, h: 0.16,
    fontFace: "Aptos", fontSize: 6.5, bold: true,
    color: dark ? "DCE8E2" : C.gray, margin: 0, fit: "shrink",
  });
}

function footer(slide, n, source = "nichibi-web.co.jp") {
  slide.addText(`${String(n).padStart(2, "0")} / ${source}`, {
    x: 0.58, y: 7.05, w: 4.6, h: 0.12,
    fontFace: "Aptos", fontSize: 5.4, color: C.gray, margin: 0,
  });
}

function headline(slide, label, main, sub, dark = false) {
  slide.addText(label, {
    x: 0.62, y: 0.96, w: 2.8, h: 0.16,
    fontFace: "Aptos", fontSize: 7, bold: true,
    color: dark ? C.yellow : C.green, margin: 0,
  });
  slide.addText(main, {
    x: 0.58, y: 1.22, w: 7.8, h: 0.72,
    fontSize: 24, bold: true, color: dark ? C.white : C.ink,
    margin: 0, fit: "shrink",
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.62, y: 1.94, w: 7.5, h: 0.32,
      fontSize: 8.6, color: dark ? "D4E1DD" : C.gray,
      margin: 0, fit: "shrink",
    });
  }
}

function chip(slide, text, x, y, w, color, darkText = false) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h: 0.29,
    fill: { color }, line: { color },
  });
  slide.addText(text, {
    x: x + 0.12, y: y + 0.075, w: w - 0.24, h: 0.1,
    fontSize: 6.9, bold: true, color: darkText ? C.ink : C.white,
    align: "center", margin: 0, fit: "shrink",
  });
}

function band(slide, x, y, w, h, color, t = 0) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h,
    fill: { color, transparency: t },
    line: { color, transparency: 100 },
  });
}

function bigNum(slide, value, label, x, y, color) {
  slide.addText(value, {
    x, y, w: 2.2, h: 0.48,
    fontSize: 27, bold: true, color, margin: 0, fit: "shrink",
  });
  slide.addText(label, {
    x, y: y + 0.53, w: 2.3, h: 0.28,
    fontSize: 8, color: C.ink2, margin: 0, fit: "shrink",
  });
}

function colorTitle(slide, text, x, y, color, dark = false) {
  slide.addText(text, {
    x, y, w: 3.1, h: 0.2,
    fontSize: 12.5, bold: true,
    color: dark ? C.white : color, margin: 0, fit: "shrink",
  });
}

// 1 Cover
{
  const s = pptx.addSlide();
  s.background = { color: C.bone };
  band(s, 8.05, 0, 5.28, 7.5, C.ink);
  band(s, 8.05, 0, 1.35, 7.5, C.green);
  band(s, 9.4, 0, 0.72, 7.5, C.cobalt);
  band(s, 10.12, 0, 0.72, 7.5, C.coral);
  band(s, 10.84, 0, 0.72, 7.5, C.orange);
  band(s, 11.56, 0, 1.77, 7.5, C.teal);
  logo(s);
  s.addText("会社説明資料", { x: 0.68, y: 1.42, w: 2.1, h: 0.18, fontSize: 8.5, bold: true, color: C.green, margin: 0 });
  s.addText("企業の未来を支える\n人材の総合\nコーディネーター", {
    x: 0.63, y: 1.9, w: 6.35, h: 2.1,
    fontSize: 33, bold: true, color: C.ink, margin: 0,
    breakLine: false, fit: "shrink",
  });
  s.addText("東海エリアを中心に、人材派遣・紹介予定派遣・人材紹介・アウトソーシングで企業の合理化と成長を支援。", {
    x: 0.68, y: 4.72, w: 5.72, h: 0.42,
    fontSize: 11.5, color: C.gray, margin: 0, fit: "shrink",
  });
  [["30年以上", "経験・ノウハウ"], ["20,000人超", "登録者基盤"], ["4つ", "就業形態"]].forEach((m, i) => {
    s.addText(m[0], { x: 8.8, y: 1.55 + i * 1.45, w: 2.5, h: 0.35, fontSize: 23, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(m[1], { x: 11.12, y: 1.66 + i * 1.45, w: 1.2, h: 0.16, fontSize: 7, bold: true, color: C.white, margin: 0, fit: "shrink" });
    band(s, 8.8, 2.02 + i * 1.45, 3.42, 0.05, [C.yellow, C.sky, C.orange][i]);
  });
  footer(s, 1, "company / employer page");
}

// 2 Manifesto
{
  const s = pptx.addSlide();
  s.background = { color: C.ink };
  logo(s, true);
  headline(s, "CORE MESSAGE", "人材は、企業の持つ力そのもの。", "日美の会社説明では、派遣を単なる事務処理ではなく、成長のためのコーディネートとして伝える。", true);
  band(s, 0.62, 2.72, 7.95, 0.1, C.yellow);
  s.addText("“企業の未来を支えるのは人”", {
    x: 0.68, y: 3.05, w: 6.2, h: 0.68,
    fontSize: 25, bold: true, color: C.yellow, margin: 0, fit: "shrink",
  });
  const blocks = [
    ["人材投入", "企業ニーズに合わせて必要な人材を投入"],
    ["提案", "短時間・短期など、柔軟な人材活用を設計"],
    ["業務合理化", "アウトソーシングで経営資源をコア業務へ"],
  ];
  blocks.forEach((b, i) => {
    band(s, 8.55, 1.65 + i * 1.28, 3.6, 0.78, A[i]);
    s.addText(b[0], { x: 8.82, y: 1.83 + i * 1.28, w: 1.4, h: 0.17, fontSize: 10.5, bold: true, color: C.white, margin: 0 });
    s.addText(b[1], { x: 10.08, y: 1.82 + i * 1.28, w: 1.78, h: 0.22, fontSize: 6.8, color: C.white, margin: 0, fit: "shrink" });
  });
  footer(s, 2, "company page");
}

// 3 Numbers
{
  const s = pptx.addSlide();
  s.background = { color: C.paper };
  logo(s);
  headline(s, "AT A GLANCE", "数字で見る日美株式会社", "公式サイトに掲載された会社概要と企業向け情報から、説明で使いやすい基本情報を整理。");
  band(s, 0.68, 2.58, 11.85, 0.08, C.ink);
  const data = [
    ["1984年", "会社設立\n昭和59年5月", C.green],
    ["5,000万円", "資本金", C.cobalt],
    ["250名", "派遣業務員\n2021年5月現在", C.coral],
    ["20,000人超", "登録者基盤", C.orange],
    ["派23-020031", "人材派遣業許可", C.teal],
    ["23-ユ-020188", "有料職業紹介事業", C.magenta],
  ];
  data.forEach((d, i) => {
    const x = 0.82 + (i % 3) * 4.05;
    const y = 3.05 + Math.floor(i / 3) * 1.2;
    bigNum(s, d[0], d[1], x, y, d[2]);
  });
  band(s, 8.9, 5.78, 3.3, 0.48, C.ink);
  s.addText("名古屋市中区錦一丁目", { x: 9.15, y: 5.95, w: 2.75, h: 0.12, fontSize: 8.8, bold: true, color: C.white, align: "center", margin: 0 });
  footer(s, 3, "company overview / employer page");
}

// 4 Why Nichibi
{
  const s = pptx.addSlide();
  s.background = { color: C.cream };
  logo(s);
  headline(s, "WHY NICHIBI", "選ばれる理由を、7つの色で見せる", "地域密着、専門性、柔軟性、定着支援を一枚で伝えるモザイク型の説明ページ。");
  const reasons = [
    ["安定の\nマッチング", "専任スタッフが適性を把握", C.green, 0.75, 2.28, 2.3, 1.2],
    ["給与\n設計", "魅力ある給与提示で定着へ", C.orange, 3.25, 2.28, 1.75, 1.2],
    ["地域\n密着", "愛知・岐阜・三重中心", C.cobalt, 5.2, 2.28, 2.25, 1.2],
    ["リピート率", "技術だけでなく人柄も重視", C.magenta, 7.65, 2.28, 2.25, 1.2],
    ["柔軟な\n人材活用", "短時間・短期間にも対応", C.teal, 0.75, 3.78, 3.0, 1.28],
    ["専門性", "医療・教育・多言語も対応", C.coral, 3.95, 3.78, 2.4, 1.28],
    ["4つの\n就業形態", "人材計画を広く支援", C.ink, 6.55, 3.78, 3.35, 1.28],
  ];
  reasons.forEach((r, i) => {
    band(s, r[3], r[4], r[5], r[6], r[2]);
    s.addText(String(i + 1).padStart(2, "0"), { x: r[3] + 0.18, y: r[4] + 0.16, w: 0.35, h: 0.14, fontSize: 7, bold: true, color: C.white, margin: 0 });
    s.addText(r[0], { x: r[3] + 0.22, y: r[4] + 0.42, w: r[5] - 0.44, h: 0.37, fontSize: 15, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(r[1], { x: r[3] + 0.22, y: r[4] + r[6] - 0.32, w: r[5] - 0.44, h: 0.14, fontSize: 6.3, color: C.white, margin: 0, fit: "shrink" });
  });
  footer(s, 4, "employer page, 7 reasons");
}

// 5 Services
{
  const s = pptx.addSlide();
  s.background = { color: C.paper };
  logo(s);
  headline(s, "SERVICE PORTFOLIO", "課題別に選べる4つの就業形態", "人材の確保から業務合理化まで、相談内容に応じてサービスを組み合わせる。");
  const services = [
    ["人材派遣", "必要な時、必要な人材を適材適所へ", C.green],
    ["紹介予定派遣", "派遣期間でミスマッチを抑えて直接雇用へ", C.cobalt],
    ["人材紹介", "採用活動の手間と費用を削減", C.coral],
    ["アウトソーシング", "業務委託で品質・生産性向上", C.ink],
  ];
  services.forEach((sv, i) => {
    const x = 0.82 + (i % 2) * 5.7;
    const y = 2.52 + Math.floor(i / 2) * 1.55;
    band(s, x, y, 4.95, 0.94, sv[2]);
    s.addText(`0${i + 1}`, { x: x + 0.24, y: y + 0.25, w: 0.44, h: 0.16, fontSize: 9, bold: true, color: C.white, margin: 0 });
    s.addText(sv[0], { x: x + 0.88, y: y + 0.22, w: 1.72, h: 0.18, fontSize: 12, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(sv[1], { x: x + 0.88, y: y + 0.54, w: 3.4, h: 0.16, fontSize: 7.3, color: C.white, margin: 0, fit: "shrink" });
  });
  band(s, 0.82, 5.98, 10.7, 0.08, C.yellow);
  s.addText("短期の欠員補充から長期採用・業務委託まで、一つの窓口で相談可能。", { x: 0.82, y: 6.18, w: 7.8, h: 0.16, fontSize: 10, bold: true, color: C.ink, margin: 0 });
  footer(s, 5, "employer page, business forms");
}

// 6 Flow
{
  const s = pptx.addSlide();
  s.background = { color: C.bone };
  logo(s);
  headline(s, "MATCHING MODEL", "聞き取り、見極め、支える。", "要件整理から就業後フォローまで、企業とスタッフの双方に無理のない接点をつくる。");
  const steps = [
    ["要件\nヒアリング", "職務・期間・条件を具体化"],
    ["候補者\n選定", "適性・経験・希望条件を照合"],
    ["就業\n開始", "スキルチェックと研修を接続"],
    ["定着\n支援", "相談・定期訪問で不安を軽減"],
  ];
  steps.forEach((st, i) => {
    const x = 1.0 + i * 3.0;
    band(s, x, 3.0 - i * 0.18, 2.12, 1.42, A[i]);
    s.addText(`0${i + 1}`, { x: x + 0.18, y: 3.18 - i * 0.18, w: 0.34, h: 0.13, fontSize: 7.5, bold: true, color: C.white, margin: 0 });
    s.addText(st[0], { x: x + 0.18, y: 3.48 - i * 0.18, w: 1.15, h: 0.42, fontSize: 14, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(st[1], { x: x + 0.18, y: 4.05 - i * 0.18, w: 1.72, h: 0.18, fontSize: 6.5, color: C.white, margin: 0, fit: "shrink" });
    if (i < 3) band(s, x + 2.25, 3.67 - i * 0.18, 0.46, 0.07, C.ink);
  });
  footer(s, 6, "employer page / about Nichibi");
}

// 7 Occupations
{
  const s = pptx.addSlide();
  s.background = { color: C.ink };
  logo(s, true);
  headline(s, "CAPABILITY AREAS", "対応職種を、面で広く持つ。", "オフィスワークから専門領域まで、現場課題に合わせて人材提案できることを見せるページ。", true);
  const areas = [
    ["company-office.png", "オフィス\nワーク", C.green],
    ["company-medic.png", "医療・\n介護", C.coral],
    ["company-it.png", "IT\n関連", C.cobalt],
    ["company-bilingual.png", "バイ\nリンガル", C.orange],
    ["company-area.png", "教育\n機関", C.teal],
    ["company-nenrei.png", "財務・\n会計", C.magenta],
  ];
  areas.forEach((a, i) => {
    const x = 0.82 + (i % 6) * 2.02;
    band(s, x, 3.0, 1.6, 2.02, a[2]);
    s.addImage({ path: path.join(assets, a[0]), x: x + 0.42, y: 3.28, w: 0.62, h: 0.62 });
    s.addText(a[1], { x: x + 0.2, y: 4.08, w: 1.18, h: 0.38, fontSize: 13, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink" });
  });
  s.addText("一般事務 / 医療事務 / SE / 翻訳通訳 / 教学部事務 / 仕訳・決算書作成 など", { x: 0.92, y: 5.72, w: 10.9, h: 0.2, fontSize: 8.2, color: "DCE8E2", margin: 0, fit: "shrink" });
  footer(s, 7, "company / about Nichibi occupation list");
}

// 8 Support
{
  const s = pptx.addSlide();
  s.background = { color: C.paper };
  logo(s);
  headline(s, "STAFF SUPPORT", "働く人の安心が、紹介品質を底上げする。", "福利厚生・就業中サポート・eラーニングを、企業にとっての定着支援として見せる。");
  band(s, 0.85, 2.65, 3.4, 2.15, C.green);
  s.addImage({ path: path.join(assets, "about-nichibi-fukuri.png"), x: 1.18, y: 3.02, w: 0.82, h: 0.82 });
  s.addText("福利厚生", { x: 2.22, y: 3.12, w: 1.3, h: 0.2, fontSize: 13, bold: true, color: C.white, margin: 0 });
  s.addText("社会保険・雇用保険・有給休暇・産休育休・健康診断", { x: 2.22, y: 3.5, w: 1.7, h: 0.3, fontSize: 6.5, color: C.white, margin: 0, fit: "shrink" });
  band(s, 4.55, 2.65, 3.4, 2.15, C.cobalt);
  s.addImage({ path: path.join(assets, "about-nichibi-support.png"), x: 4.88, y: 3.02, w: 0.82, h: 0.82 });
  s.addText("就業中\nサポート", { x: 5.92, y: 3.02, w: 1.3, h: 0.35, fontSize: 13, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("定期訪問・相談対応・ストレスチェック・証明書対応", { x: 5.92, y: 3.55, w: 1.7, h: 0.3, fontSize: 6.5, color: C.white, margin: 0, fit: "shrink" });
  band(s, 8.25, 2.65, 3.4, 2.15, C.orange);
  s.addText("e\nLearning", { x: 8.62, y: 2.98, w: 1.05, h: 0.55, fontFace: "Aptos", fontSize: 22, bold: true, color: C.white, margin: 0, fit: "shrink" });
  s.addText("ビジネスマナー / OA基礎 / 経理・財務 / セルフマネジメント", { x: 9.88, y: 3.46, w: 1.38, h: 0.32, fontSize: 6.2, color: C.white, margin: 0, fit: "shrink" });
  footer(s, 8, "about Nichibi / e-learning");
}

// 9 Region
{
  const s = pptx.addSlide();
  s.background = { color: C.cream };
  logo(s);
  headline(s, "REGIONAL NETWORK", "東海エリアの現場に近い。", "名古屋本社を起点に、愛知・岐阜・三重・静岡の企業・求職者を結ぶ。");
  band(s, 0.78, 2.65, 3.0, 1.6, C.green);
  band(s, 3.95, 2.05, 2.1, 1.6, C.cobalt);
  band(s, 5.25, 4.05, 2.2, 1.25, C.coral);
  band(s, 7.7, 3.05, 3.45, 1.32, C.orange);
  [["愛知", 1.55, 3.22], ["岐阜", 4.68, 2.62], ["三重", 6.02, 4.52], ["静岡", 8.68, 3.52]].forEach(([t, x, y]) => {
    s.addText(t, { x, y, w: 0.8, h: 0.22, fontSize: 17, bold: true, color: C.white, align: "center", margin: 0 });
  });
  s.addText("地域密着 / スピード / 職種横断", { x: 0.82, y: 5.92, w: 5.8, h: 0.22, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  footer(s, 9, "employer page");
}

// 10 Use cases
{
  const s = pptx.addSlide();
  s.background = { color: C.paper };
  logo(s);
  headline(s, "USE CASES", "今すぐ困っていることから、構造的な改善まで。", "人材確保と業務合理化の両面から、現場の継続稼働を支える。");
  const cases = [
    ["欠員補充", "急な退職・休職時の業務停止を防ぐ", C.green],
    ["繁忙期対応", "短期・短時間で必要人数を確保", C.cobalt],
    ["医療事務", "受付会計・病棟事務などを支援", C.coral],
    ["学校事務", "教学・入試・図書司書などに対応", C.orange],
    ["業務委託", "受付案内・総務人事・製造管理などを合理化", C.ink],
  ];
  cases.forEach((c, i) => {
    const y = 2.35 + i * 0.68;
    band(s, 0.92, y, 2.1, 0.42, c[2]);
    s.addText(c[0], { x: 1.12, y: y + 0.13, w: 1.4, h: 0.1, fontSize: 8.5, bold: true, color: C.white, margin: 0 });
    s.addText(c[1], { x: 3.35, y: y + 0.13, w: 4.2, h: 0.1, fontSize: 8, color: C.ink, margin: 0, fit: "shrink" });
  });
  band(s, 8.35, 2.35, 3.55, 2.65, C.ink);
  s.addText("提案の焦点", { x: 8.7, y: 2.73, w: 1.5, h: 0.16, fontSize: 9, bold: true, color: C.yellow, margin: 0 });
  s.addText("人数を埋めるだけでなく、業務の切り出し方・雇用形態・定着支援まで設計する。", { x: 8.7, y: 3.25, w: 2.72, h: 0.74, fontSize: 14, bold: true, color: C.white, margin: 0, fit: "shrink" });
  footer(s, 10, "employer page / company occupation list");
}

// 11 Start flow
{
  const s = pptx.addSlide();
  s.background = { color: C.bone };
  logo(s);
  headline(s, "START FLOW", "相談から就業・フォローまで。", "企業側の求人条件を明確化し、候補者推薦・就業開始・入社後フォローまで伴走。");
  const flow = ["お問い合わせ", "求人要件整理", "人選・推薦", "就業・採用", "フォロー"];
  flow.forEach((f, i) => {
    const x = 0.86 + i * 2.34;
    band(s, x, 3.05, 1.72, 1.72, A[i]);
    s.addText(`0${i + 1}`, { x: x + 0.18, y: 3.25, w: 0.38, h: 0.14, fontSize: 8, bold: true, color: C.white, margin: 0 });
    s.addText(f, { x: x + 0.2, y: 3.88, w: 1.3, h: 0.22, fontSize: 10.5, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink" });
  });
  chip(s, "企業向け問い合わせ  052-265-5553", 3.6, 5.62, 5.5, C.ink);
  footer(s, 11, "employer contact / employer page");
}

// 12 Company overview
{
  const s = pptx.addSlide();
  s.background = { color: C.ink };
  logo(s, true);
  s.addText("日美株式会社", { x: 0.72, y: 1.18, w: 4.5, h: 0.5, fontSize: 28, bold: true, color: C.white, margin: 0 });
  s.addText("人材の総合コーディネーターとして、企業経営の合理化をサポートします。", { x: 0.76, y: 1.95, w: 6.6, h: 0.25, fontSize: 12, bold: true, color: C.yellow, margin: 0, fit: "shrink" });
  const rows = [
    ["代表者", "代表取締役社長 長谷川裕一"],
    ["所在地", "名古屋市中区錦一丁目5番13号 オリックス名古屋錦ビル9階"],
    ["設立", "昭和59年5月"],
    ["資本金", "5,000万円"],
    ["許可", "派23-020031 / 23-ユ-020188"],
    ["URL", "https://nichibi-web.co.jp"],
  ];
  rows.forEach((r, i) => {
    const y = 3.0 + i * 0.45;
    s.addText(r[0], { x: 0.82, y, w: 0.9, h: 0.12, fontSize: 7.2, bold: true, color: A[i], margin: 0 });
    s.addText(r[1], { x: 1.95, y, w: 5.45, h: 0.14, fontSize: 7.8, color: C.white, margin: 0, fit: "shrink" });
  });
  band(s, 8.15, 0, 1.0, 7.5, C.green);
  band(s, 9.15, 0, 1.0, 7.5, C.cobalt);
  band(s, 10.15, 0, 1.0, 7.5, C.coral);
  band(s, 11.15, 0, 1.0, 7.5, C.orange);
  band(s, 12.15, 0, 1.18, 7.5, C.teal);
  footer(s, 12, "company overview");
}

pptx.writeFile({ fileName: out });
