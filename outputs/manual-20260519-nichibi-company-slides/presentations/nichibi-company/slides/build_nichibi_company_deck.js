const pptxgen = require("pptxgenjs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const assets = path.join(root, "assets");
const out = path.join(root, "output", "nichibi-company-profile-20260519.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "YNFactory";
pptx.company = "YNFactory";
pptx.subject = "日美株式会社 会社説明資料";
pptx.title = "日美株式会社 会社説明資料";
pptx.lang = "ja-JP";
pptx.theme = {
  headFontFace: "Hiragino Sans",
  bodyFontFace: "Hiragino Sans",
  lang: "ja-JP",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";

const C = {
  green: "008A65",
  green2: "3BA77C",
  mint: "EAF6F0",
  navy: "183047",
  blue: "34699A",
  yellow: "F5C84C",
  coral: "EE7D5A",
  ink: "24313C",
  gray: "64717D",
  line: "DCE4E8",
  paper: "FAFBF7",
  white: "FFFFFF",
};

function addBg(slide, opts = {}) {
  slide.background = { color: opts.dark ? C.navy : C.paper };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.12,
    fill: { color: opts.dark ? C.yellow : C.green },
    line: { color: opts.dark ? C.yellow : C.green },
  });
  slide.addImage({
    path: path.join(assets, "nichibi-logo.png"),
    x: 11.08,
    y: 0.28,
    w: 1.55,
    h: 0.37,
  });
}

function footer(slide, n, source = "Source: nichibi-web.co.jp") {
  slide.addText(`${String(n).padStart(2, "0")}  ${source}`, {
    x: 0.55,
    y: 7.05,
    w: 8.5,
    h: 0.18,
    fontFace: "Aptos",
    fontSize: 5.8,
    color: C.gray,
    margin: 0,
  });
}

function title(slide, kicker, headline, sub) {
  slide.addText(kicker, {
    x: 0.62,
    y: 0.55,
    w: 2.7,
    h: 0.25,
    fontSize: 8,
    bold: true,
    color: C.green,
    charSpace: 0,
    margin: 0,
  });
  slide.addText(headline, {
    x: 0.58,
    y: 0.92,
    w: 8.6,
    h: 0.72,
    fontSize: 25,
    bold: true,
    color: C.ink,
    fit: "shrink",
    margin: 0,
    breakLine: false,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.62,
      y: 1.64,
      w: 8.9,
      h: 0.32,
      fontSize: 9,
      color: C.gray,
      margin: 0,
      fit: "shrink",
    });
  }
}

function pill(slide, text, x, y, w, color = C.green) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.32,
    rectRadius: 0.06,
    fill: { color },
    line: { color },
  });
  slide.addText(text, {
    x: x + 0.1,
    y: y + 0.075,
    w: w - 0.2,
    h: 0.12,
    fontSize: 7.8,
    bold: true,
    color: C.white,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    fill: { color: opts.fill || C.white, transparency: opts.transparency || 0 },
    line: { color: opts.line || C.line, width: opts.width || 1 },
    shadow: opts.shadow === false ? undefined : { type: "outer", color: "D6DEE2", opacity: 0.18, blur: 1, angle: 45, distance: 1 },
  });
}

function metric(slide, value, label, x, y, w, accent = C.green) {
  slide.addText(value, {
    x,
    y,
    w,
    h: 0.45,
    fontSize: 26,
    bold: true,
    color: accent,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
  slide.addText(label, {
    x,
    y: y + 0.52,
    w,
    h: 0.38,
    fontSize: 8.5,
    color: C.ink,
    align: "center",
    margin: 0,
    fit: "shrink",
  });
}

function sectionLabel(slide, text, x, y, color = C.green) {
  slide.addText(text, {
    x,
    y,
    w: 2.2,
    h: 0.18,
    fontSize: 7.2,
    bold: true,
    color,
    margin: 0,
  });
}

// 1
{
  const s = pptx.addSlide();
  s.background = { color: C.paper };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.paper }, line: { color: C.paper } });
  s.addShape(pptx.ShapeType.rect, { x: 8.15, y: 0, w: 5.18, h: 7.5, fill: { color: C.green }, line: { color: C.green } });
  s.addShape(pptx.ShapeType.arc, { x: 7.1, y: -0.45, w: 3.0, h: 8.7, line: { color: C.yellow, width: 2.2, transparency: 15 }, adjustPoint: 0.35 });
  s.addImage({ path: path.join(assets, "nichibi-logo.png"), x: 0.72, y: 0.55, w: 2.0, h: 0.48 });
  s.addText("会社説明資料", { x: 0.74, y: 1.68, w: 2.3, h: 0.24, fontSize: 9, bold: true, color: C.green, margin: 0 });
  s.addText("企業の未来を支える\n人材の総合コーディネーター", {
    x: 0.7,
    y: 2.05,
    w: 6.9,
    h: 1.55,
    fontSize: 32,
    bold: true,
    color: C.ink,
    breakLine: false,
    fit: "shrink",
    margin: 0,
  });
  s.addText("東海エリアを中心に、人材派遣・紹介予定派遣・人材紹介・アウトソーシングで企業の合理化と成長を支援。", {
    x: 0.74,
    y: 4.05,
    w: 5.9,
    h: 0.58,
    fontSize: 13,
    color: C.gray,
    breakLine: false,
    fit: "shrink",
    margin: 0,
  });
  [["30年以上", "経験・ノウハウ"], ["20,000人超", "登録者基盤"], ["4つ", "就業形態"]].forEach((m, i) => {
    card(s, 8.82, 1.12 + i * 1.43, 3.25, 0.92, { fill: "FFFFFF", transparency: 5, line: "B8E3D3", shadow: false });
    s.addText(m[0], { x: 9.05, y: 1.27 + i * 1.43, w: 1.35, h: 0.3, fontSize: 18, bold: true, color: C.yellow, margin: 0, fit: "shrink" });
    s.addText(m[1], { x: 10.38, y: 1.36 + i * 1.43, w: 1.35, h: 0.2, fontSize: 8.5, bold: true, color: C.navy, margin: 0, fit: "shrink" });
  });
  footer(s, 1, "Sources: company / looking-for-human-resource");
}

// 2
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "CORE MESSAGE", "理念は、人を起点に企業の明日を設計すること", "単なる人員補充ではなく、企業ニーズに合わせた人材投入・提案・アウトソーシングまで支援する。");
  s.addText("“企業の未来を支えるのは人”", {
    x: 0.92, y: 2.25, w: 4.9, h: 0.8, fontSize: 24, bold: true, color: C.green, margin: 0, fit: "shrink",
  });
  const blocks = [
    ["人材投入", "必要な時に、必要な人材を適材適所へ"],
    ["柔軟な提案", "短時間・短期間・短日数などの要望に対応"],
    ["経営合理化", "業務委託・コンサルティングで効率化を支援"],
  ];
  blocks.forEach((b, i) => {
    card(s, 6.25, 2.0 + i * 1.05, 5.65, 0.78, { fill: i === 1 ? C.mint : C.white });
    s.addShape(pptx.ShapeType.rect, { x: 6.25, y: 2.0 + i * 1.05, w: 0.08, h: 0.78, fill: { color: [C.green, C.blue, C.coral][i] }, line: { color: [C.green, C.blue, C.coral][i] } });
    s.addText(b[0], { x: 6.55, y: 2.16 + i * 1.05, w: 1.45, h: 0.23, fontSize: 12, bold: true, color: C.ink, margin: 0 });
    s.addText(b[1], { x: 8.1, y: 2.17 + i * 1.05, w: 3.45, h: 0.22, fontSize: 9, color: C.gray, margin: 0, fit: "shrink" });
  });
  s.addShape(pptx.ShapeType.chevron, { x: 2.3, y: 4.8, w: 8.1, h: 0.55, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("企業とスタッフ双方の成長に貢献", { x: 3.58, y: 4.98, w: 5.3, h: 0.18, fontSize: 11.5, bold: true, color: C.white, align: "center", margin: 0 });
  footer(s, 2, "Source: company page");
}

// 3
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "AT A GLANCE", "数字で見る日美株式会社", "公開会社概要と企業向けページに基づく基本情報。");
  const ms = [
    ["1984年", "会社設立\n昭和59年5月", C.green],
    ["5,000万円", "資本金", C.blue],
    ["派23-020031", "人材派遣業許可", C.coral],
    ["23-ユ-020188", "有料職業紹介事業", C.green],
    ["250名", "派遣業務員\n2021年5月現在", C.blue],
    ["20,000人超", "登録者基盤\n企業向けページ記載", C.coral],
  ];
  ms.forEach((m, i) => {
    const x = 0.72 + (i % 3) * 4.05;
    const y = 2.02 + Math.floor(i / 3) * 1.58;
    card(s, x, y, 3.48, 1.05, { fill: C.white });
    metric(s, m[0], m[1], x + 0.15, y + 0.17, 3.18, m[2]);
  });
  s.addShape(pptx.ShapeType.rect, { x: 0.72, y: 5.62, w: 11.8, h: 0.58, fill: { color: C.mint }, line: { color: C.mint } });
  s.addText("本社: 名古屋市中区錦一丁目5番13号 オリックス名古屋錦ビル9階", { x: 0.95, y: 5.82, w: 10.9, h: 0.18, fontSize: 10, bold: true, color: C.ink, margin: 0, fit: "shrink" });
  footer(s, 3, "Sources: company overview / employer page");
}

// 4
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "WHY NICHIBI", "選ばれる理由は、地域密着と人材理解の掛け合わせ", "企業の採用・配置・定着に効く7つの強み。");
  const reasons = [
    ["安定のマッチング", "専任スタッフが適性を把握"],
    ["給与設計", "応募率と定着率を意識"],
    ["地域密着", "愛知・岐阜・三重中心"],
    ["リピート率", "技術と人柄を重視"],
    ["柔軟な活用", "短時間・短期にも対応"],
    ["専門性", "医療・教育・多言語も対応"],
    ["4つの就業形態", "人材計画を広く支援"],
  ];
  reasons.forEach((r, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.65 + col * 3.12;
    const y = 2.0 + row * 1.55;
    card(s, x, y, 2.72, 1.07, { fill: i === 6 ? C.navy : C.white, line: i === 6 ? C.navy : C.line });
    s.addText(`0${i + 1}`, { x: x + 0.18, y: y + 0.17, w: 0.45, h: 0.17, fontSize: 8, bold: true, color: i === 6 ? C.yellow : C.green, margin: 0 });
    s.addText(r[0], { x: x + 0.18, y: y + 0.42, w: 2.25, h: 0.22, fontSize: 10.5, bold: true, color: i === 6 ? C.white : C.ink, margin: 0, fit: "shrink" });
    s.addText(r[1], { x: x + 0.18, y: y + 0.71, w: 2.25, h: 0.2, fontSize: 7.6, color: i === 6 ? "CFE7DC" : C.gray, margin: 0, fit: "shrink" });
  });
  s.addText("採用だけでなく、配置後に活躍し続けることまで見据える", { x: 0.75, y: 5.53, w: 6.9, h: 0.28, fontSize: 14, bold: true, color: C.green, margin: 0 });
  footer(s, 4, "Source: employer page, 7 reasons");
}

// 5
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "SERVICE PORTFOLIO", "課題に合わせて選べる4つの就業形態", "人材派遣、紹介予定派遣、人材紹介、アウトソーシングを組み合わせて人事計画を支援。");
  const services = [
    ["人材派遣", "必要な時、必要な人材を適材適所へ。リーズナブルかつタイムリーに提供。", C.green],
    ["紹介予定派遣", "派遣期間で能力・適性を確認し、ミスマッチを抑えて直接雇用へ。", C.blue],
    ["人材紹介", "採用条件に合う候補者を推薦。採用活動の手間と費用を削減。", C.coral],
    ["アウトソーシング", "業務一括委託で品質・生産性向上、コア業務への集中を支援。", C.navy],
  ];
  services.forEach((r, i) => {
    const x = 0.75 + (i % 2) * 5.95;
    const y = 2.02 + Math.floor(i / 2) * 1.65;
    card(s, x, y, 5.25, 1.18, { fill: C.white, line: r[2] });
    s.addShape(pptx.ShapeType.roundRect, { x: x + 0.18, y: y + 0.22, w: 0.58, h: 0.58, rectRadius: 0.05, fill: { color: r[2] }, line: { color: r[2] } });
    s.addText(String(i + 1), { x: x + 0.35, y: y + 0.42, w: 0.24, h: 0.12, fontSize: 9, bold: true, color: C.white, margin: 0, align: "center" });
    s.addText(r[0], { x: x + 0.98, y: y + 0.25, w: 1.7, h: 0.24, fontSize: 12, bold: true, color: C.ink, margin: 0 });
    s.addText(r[1], { x: x + 0.98, y: y + 0.58, w: 3.82, h: 0.34, fontSize: 8.2, color: C.gray, margin: 0, fit: "shrink" });
  });
  s.addText("短期の欠員補充から長期の採用・業務合理化まで、一つの窓口で相談可能。", { x: 1.25, y: 5.73, w: 10.0, h: 0.22, fontSize: 12, bold: true, color: C.ink, align: "center", margin: 0 });
  footer(s, 5, "Source: employer page, business forms");
}

// 6
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "MATCHING MODEL", "人材要件を聞き取り、適性・経験・定着まで見る", "10年以上のキャリアを持つ専任スタッフによる人選と、就業後のフォローで安定稼働を目指す。");
  const steps = [
    ["1", "要件ヒアリング", "職務内容・期間・働き方を具体化"],
    ["2", "候補者選定", "適性・経験・希望条件を照合"],
    ["3", "就業開始", "スキルチェックと研修を組み合わせる"],
    ["4", "定着支援", "定期訪問・相談対応で不安を早期把握"],
  ];
  steps.forEach((st, i) => {
    const x = 0.82 + i * 3.05;
    s.addShape(pptx.ShapeType.chevron, { x, y: 2.58, w: 2.55, h: 1.15, fill: { color: [C.green, C.blue, C.coral, C.navy][i] }, line: { color: [C.green, C.blue, C.coral, C.navy][i] } });
    s.addText(st[0], { x: x + 0.23, y: 2.91, w: 0.35, h: 0.18, fontSize: 11, bold: true, color: C.white, margin: 0 });
    s.addText(st[1], { x: x + 0.67, y: 2.82, w: 1.42, h: 0.2, fontSize: 10.5, bold: true, color: C.white, margin: 0, fit: "shrink" });
    s.addText(st[2], { x: x + 0.67, y: 3.12, w: 1.55, h: 0.23, fontSize: 6.7, color: "EEF6F3", margin: 0, fit: "shrink" });
  });
  card(s, 1.05, 4.65, 11.1, 0.74, { fill: C.mint, line: "CFE7DC" });
  s.addText("人材派遣・紹介予定派遣・人材紹介・アウトソーシングを、企業課題に合わせて接続する", { x: 1.4, y: 4.91, w: 10.3, h: 0.16, fontSize: 10.8, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
  footer(s, 6, "Sources: employer page / about Nichibi");
}

// 7
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "CAPABILITY AREAS", "オフィスから医療・教育・ITまで幅広い職種に対応", "専門職と実務経験者の登録基盤により、企業の現場課題に合わせた人材提案が可能。");
  const areas = [
    ["company-office.png", "オフィスワーク", "一般事務・経理・総務・受付など"],
    ["company-medic.png", "医療・介護", "医療事務・受付・看護補助・介護など"],
    ["company-it.png", "IT関連", "SE・プログラミング・ヘルプデスクなど"],
    ["company-bilingual.png", "バイリンガル", "翻訳・通訳・英文事務など"],
    ["company-area.png", "教育機関", "教学部事務・図書司書・研究助手など"],
    ["company-nenrei.png", "財務・会計", "仕訳・試算表・決算書作成など"],
  ];
  areas.forEach((a, i) => {
    const x = 0.75 + (i % 3) * 4.05;
    const y = 2.0 + Math.floor(i / 3) * 1.55;
    card(s, x, y, 3.45, 1.1, { fill: C.white });
    s.addImage({ path: path.join(assets, a[0]), x: x + 0.18, y: y + 0.22, w: 0.56, h: 0.56 });
    s.addText(a[1], { x: x + 0.92, y: y + 0.25, w: 2.15, h: 0.2, fontSize: 10.5, bold: true, color: C.ink, margin: 0, fit: "shrink" });
    s.addText(a[2], { x: x + 0.92, y: y + 0.58, w: 2.25, h: 0.22, fontSize: 7.4, color: C.gray, margin: 0, fit: "shrink" });
  });
  footer(s, 7, "Sources: company / about Nichibi occupation list");
}

// 8
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "STAFF SUPPORT", "安心して働ける環境づくりが、紹介品質を支える", "福利厚生、就業中フォロー、eラーニングまで、登録スタッフの継続的な活躍を支援。");
  card(s, 0.78, 2.1, 5.72, 2.6, { fill: C.white });
  s.addImage({ path: path.join(assets, "about-nichibi-fukuri.png"), x: 1.05, y: 2.37, w: 1.12, h: 1.12 });
  s.addText("福利厚生", { x: 2.45, y: 2.38, w: 2.2, h: 0.26, fontSize: 15, bold: true, color: C.green, margin: 0 });
  s.addText("社会保険・雇用保険・有給休暇・産休育休・健康診断など、安心して働くための制度を整備。", { x: 2.45, y: 2.86, w: 3.32, h: 0.48, fontSize: 9, color: C.gray, margin: 0, fit: "shrink" });
  card(s, 6.83, 2.1, 5.72, 2.6, { fill: C.white });
  s.addImage({ path: path.join(assets, "about-nichibi-support.png"), x: 7.1, y: 2.37, w: 1.12, h: 1.12 });
  s.addText("就業中サポート", { x: 8.5, y: 2.38, w: 2.3, h: 0.26, fontSize: 15, bold: true, color: C.blue, margin: 0 });
  s.addText("定期訪問、相談対応、ストレスチェック、各種証明書対応で就業中の不安を軽減。", { x: 8.5, y: 2.86, w: 3.32, h: 0.48, fontSize: 9, color: C.gray, margin: 0, fit: "shrink" });
  s.addShape(pptx.ShapeType.rect, { x: 0.78, y: 5.28, w: 11.78, h: 0.62, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("eラーニング: ビジネスマナー / OA基礎 / 経理・財務 / セルフマネジメント など", { x: 1.05, y: 5.5, w: 11.1, h: 0.18, fontSize: 10, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink" });
  footer(s, 8, "Sources: about Nichibi / e-learning");
}

// 9
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "REGIONAL NETWORK", "東海エリアの現場課題に近い人材サービス", "名古屋本社を起点に、愛知・岐阜・三重・静岡の企業・求職者を結ぶ。");
  s.addShape(pptx.ShapeType.rect, { x: 0.95, y: 2.0, w: 5.05, h: 3.52, fill: { color: C.mint }, line: { color: "CFE7DC" } });
  [["愛知", 2.65, 3.2, C.green], ["岐阜", 2.2, 2.6, C.blue], ["三重", 2.25, 4.08, C.coral], ["静岡", 3.35, 4.18, C.yellow]].forEach(([name, x, y, color]) => {
    s.addShape(pptx.ShapeType.ellipse, { x, y, w: 1.1, h: 0.58, fill: { color }, line: { color } });
    s.addText(name, { x: x + 0.22, y: y + 0.2, w: 0.66, h: 0.12, fontSize: 9.5, bold: true, color: color === C.yellow ? C.ink : C.white, align: "center", margin: 0 });
  });
  const items = [
    ["地域密着", "創業以来蓄積してきた登録者基盤で、現場に近い人材提案。"],
    ["スピード", "ニーズに合う人材をスピーディーに提供。"],
    ["職種横断", "オフィス・医療・教育・ITなど複数領域をカバー。"],
  ];
  items.forEach((it, i) => {
    card(s, 6.65, 2.05 + i * 1.08, 5.42, 0.76, { fill: C.white });
    sectionLabel(s, it[0], 6.92, 2.28 + i * 1.08, [C.green, C.blue, C.coral][i]);
    s.addText(it[1], { x: 8.0, y: 2.25 + i * 1.08, w: 3.65, h: 0.2, fontSize: 8.4, color: C.gray, margin: 0, fit: "shrink" });
  });
  footer(s, 9, "Source: employer page");
}

// 10
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "USE CASES", "企業の“今すぐ困っている”から“構造的に変えたい”まで対応", "人材確保と業務合理化の両面から、現場の継続稼働を支える。");
  const cases = [
    ["欠員補充", "急な退職・休職時の業務停止を防ぐ"],
    ["繁忙期対応", "短期・短時間で必要人数を確保"],
    ["医療事務", "受付会計・病棟事務などを支援"],
    ["学校事務", "教学・入試・図書司書などに対応"],
    ["業務委託", "受付案内・総務人事・製造管理などを合理化"],
  ];
  cases.forEach((c, i) => {
    const y = 1.92 + i * 0.73;
    s.addShape(pptx.ShapeType.rect, { x: 0.92, y, w: 0.08, h: 0.42, fill: { color: [C.green, C.blue, C.coral, C.yellow, C.navy][i] }, line: { color: [C.green, C.blue, C.coral, C.yellow, C.navy][i] } });
    s.addText(c[0], { x: 1.16, y: y + 0.05, w: 1.6, h: 0.18, fontSize: 10.5, bold: true, color: C.ink, margin: 0 });
    s.addText(c[1], { x: 3.02, y: y + 0.06, w: 4.3, h: 0.18, fontSize: 8.5, color: C.gray, margin: 0, fit: "shrink" });
  });
  card(s, 8.1, 2.0, 3.95, 2.65, { fill: C.navy, line: C.navy });
  s.addText("提案の焦点", { x: 8.42, y: 2.35, w: 1.5, h: 0.2, fontSize: 10, bold: true, color: C.yellow, margin: 0 });
  s.addText("人数を埋めるだけでなく、業務の切り出し方・雇用形態・定着支援まで含めて設計する。", { x: 8.42, y: 2.85, w: 3.18, h: 0.78, fontSize: 13, bold: true, color: C.white, margin: 0, fit: "shrink" });
  footer(s, 10, "Sources: employer page / company occupation list");
}

// 11
{
  const s = pptx.addSlide(); addBg(s);
  title(s, "START FLOW", "相談から就業・フォローまでの基本ステップ", "企業側の求人条件を明確化し、候補者推薦・就業開始・入社後フォローまで伴走。");
  const flow = [
    ["お問い合わせ", "サービス内容・資料請求・人材相談"],
    ["求人要件整理", "職務・期間・給与・働き方を具体化"],
    ["人選・推薦", "条件に合うスタッフ・候補者を提案"],
    ["就業・採用", "派遣開始、紹介予定派遣、内定・入社"],
    ["フォロー", "就業中相談、入社後半年フォロー等"],
  ];
  flow.forEach((f, i) => {
    const x = 0.8 + i * 2.45;
    s.addShape(pptx.ShapeType.ellipse, { x, y: 2.35, w: 1.28, h: 1.28, fill: { color: [C.green, C.blue, C.coral, C.yellow, C.navy][i] }, line: { color: C.white, width: 1.5 } });
    s.addText(String(i + 1), { x: x + 0.48, y: 2.78, w: 0.3, h: 0.18, fontSize: 16, bold: true, color: i === 3 ? C.ink : C.white, align: "center", margin: 0 });
    if (i < 4) s.addShape(pptx.ShapeType.line, { x: x + 1.32, y: 2.99, w: 1.05, h: 0, line: { color: C.line, width: 2, beginArrowType: "none", endArrowType: "triangle" } });
    s.addText(f[0], { x: x - 0.18, y: 3.86, w: 1.62, h: 0.2, fontSize: 9.5, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    s.addText(f[1], { x: x - 0.42, y: 4.22, w: 2.08, h: 0.34, fontSize: 7.3, color: C.gray, align: "center", margin: 0, fit: "shrink" });
  });
  s.addText("企業向け問い合わせ: 052-265-5553", { x: 0.95, y: 5.56, w: 4.2, h: 0.24, fontSize: 13, bold: true, color: C.green, margin: 0 });
  footer(s, 11, "Sources: employer contact / employer page");
}

// 12
{
  const s = pptx.addSlide(); addBg(s, { dark: true });
  s.addImage({ path: path.join(assets, "nichibi-logo.png"), x: 0.75, y: 0.65, w: 2.2, h: 0.53 });
  s.addText("日美株式会社", { x: 0.75, y: 1.62, w: 4.2, h: 0.4, fontSize: 22, bold: true, color: C.white, margin: 0 });
  s.addText("人材派遣業 許可番号: 派23-020031\n有料職業紹介事業 許可番号: 23-ユ-020188", { x: 0.78, y: 2.28, w: 5.2, h: 0.45, fontSize: 10, color: "D7E5E0", margin: 0, fit: "shrink" });
  const rows = [
    ["代表者", "代表取締役社長 長谷川裕一"],
    ["所在地", "〒460-0003 名古屋市中区錦一丁目5番13号 オリックス名古屋錦ビル9階"],
    ["設立", "昭和59年5月"],
    ["資本金", "5,000万円"],
    ["TEL", "052-265-5553"],
    ["URL", "https://nichibi-web.co.jp"],
  ];
  rows.forEach((r, i) => {
    const y = 1.35 + i * 0.68;
    s.addText(r[0], { x: 6.45, y, w: 1.0, h: 0.18, fontSize: 8, bold: true, color: C.yellow, margin: 0 });
    s.addText(r[1], { x: 7.58, y, w: 4.6, h: 0.25, fontSize: 8.8, color: C.white, margin: 0, fit: "shrink" });
    s.addShape(pptx.ShapeType.line, { x: 6.45, y: y + 0.38, w: 5.6, h: 0, line: { color: "496070", transparency: 15, width: 0.7 } });
  });
  s.addText("人材の総合コーディネーターとして、企業経営の合理化をサポートします。", { x: 0.78, y: 5.95, w: 7.2, h: 0.28, fontSize: 14, bold: true, color: C.yellow, margin: 0 });
  footer(s, 12, "Source: company overview");
}

pptx.writeFile({ fileName: out });
