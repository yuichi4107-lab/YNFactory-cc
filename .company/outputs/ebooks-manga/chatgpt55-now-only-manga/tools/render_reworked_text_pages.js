const fs = require("fs");
const path = require("path");
const { chromium } = require("/Users/yuichi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");

const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "panels", "text_pages_reworked");

const pageCss = `
  @font-face {
    font-family: "HiraginoLocal";
    src: local("Hiragino Sans"), local("Hiragino Kaku Gothic ProN");
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0;
    width: 1024px;
    height: 1536px;
    overflow: hidden;
    font-family: "HiraginoLocal", "Yu Gothic", sans-serif;
    color: #102033;
    background: #f8fbff;
  }
  .page {
    position: relative;
    width: 1024px;
    height: 1536px;
    overflow: hidden;
    padding: 82px 76px;
    background:
      radial-gradient(circle at 82% 12%, rgba(69, 196, 180, .18) 0, rgba(69, 196, 180, 0) 260px),
      radial-gradient(circle at 5% 94%, rgba(255, 202, 78, .24) 0, rgba(255, 202, 78, 0) 320px),
      linear-gradient(180deg, #ffffff 0%, #f3f8fb 100%);
  }
  .page::before {
    content: "";
    position: absolute;
    left: -160px;
    top: -110px;
    width: 720px;
    height: 260px;
    background: #123253;
    transform: rotate(-8deg);
  }
  .page::after {
    content: "";
    position: absolute;
    right: -140px;
    bottom: -80px;
    width: 760px;
    height: 230px;
    background: #ffd15a;
    transform: rotate(-6deg);
  }
  .kicker {
    position: relative;
    z-index: 2;
    display: inline-block;
    padding: 13px 24px;
    border-radius: 999px;
    background: #16a7a1;
    color: #fff;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: 0;
  }
  h1 {
    position: relative;
    z-index: 2;
    margin: 34px 0 42px;
    color: #102033;
    font-size: 72px;
    line-height: 1.12;
    font-weight: 900;
    letter-spacing: 0;
  }
  .card {
    position: relative;
    z-index: 2;
    background: rgba(255,255,255,.96);
    border: 4px solid #123253;
    border-radius: 18px;
    box-shadow: 0 18px 0 rgba(18,50,83,.08);
  }
  .toc { padding: 34px 38px 30px; }
  .toc-row {
    display: grid;
    grid-template-columns: 1fr 92px;
    gap: 22px;
    align-items: center;
    min-height: 86px;
    border-bottom: 2px solid #dbe8ee;
  }
  .toc-row:last-child { border-bottom: 0; }
  .toc-main { font-size: 31px; font-weight: 850; line-height: 1.22; }
  .toc-sub { margin-top: 7px; font-size: 21px; color: #436071; line-height: 1.28; font-weight: 650; }
  .toc-page {
    justify-self: end;
    min-width: 74px;
    padding: 10px 12px;
    border-radius: 10px;
    background: #ffd15a;
    font-size: 27px;
    font-weight: 900;
    text-align: center;
  }
  .profile { padding: 46px 52px; }
  .name {
    margin: 0 0 28px;
    font-size: 54px;
    line-height: 1.15;
    font-weight: 900;
    text-align: center;
  }
  .lead {
    margin: 0 0 34px;
    padding: 22px 28px;
    border-radius: 14px;
    background: #eef9f8;
    font-size: 32px;
    line-height: 1.5;
    font-weight: 800;
  }
  .body-text p {
    margin: 0 0 24px;
    font-size: 30px;
    line-height: 1.56;
    font-weight: 600;
  }
  .info-table { padding: 38px 44px; }
  .info-row {
    display: grid;
    grid-template-columns: 210px 1fr;
    gap: 26px;
    padding: 21px 0;
    border-bottom: 2px solid #dbe8ee;
    align-items: start;
  }
  .info-row:last-child { border-bottom: 0; }
  .info-key { font-size: 27px; font-weight: 900; color: #123253; }
  .info-value { font-size: 28px; line-height: 1.38; font-weight: 650; }
  .note {
    position: relative;
    z-index: 2;
    margin-top: 36px;
    padding: 24px 30px;
    border-left: 12px solid #16a7a1;
    background: rgba(255,255,255,.92);
    font-size: 25px;
    line-height: 1.48;
    font-weight: 650;
  }
  .footer {
    position: absolute;
    z-index: 2;
    left: 76px;
    right: 76px;
    bottom: 62px;
    color: #385365;
    font-size: 22px;
    font-weight: 800;
    text-align: center;
  }
`;

function htmlFor(kind) {
  if (kind === "toc") {
    const rows = [
      ["登場人物紹介", "ミナ・レン・ユイの役割", "3"],
      ["プロローグ", "Claude＋Geminiの二刀流からChatGPT一本へ", "4"],
      ["第1話", "GPT-5.5で何が変わったのか", "10"],
      ["第2話", "なぜ『いまはChatGPTだけでいい』と言えるのか", "22"],
      ["第3話", "ClaudeとGeminiをどう見るべきか", "41"],
      ["第4話", "ChatGPT中心の実務ワークフロー", "64"],
      ["第5話", "固定せず、乗り遅れないためのAI戦略", "88"],
      ["エピローグ", "今日の正解を使い、明日の変化に備える", "108"],
      ["実践補足・巻末", "今日から使うための補足と著者情報", "114"],
    ];
    return base("目次", "CONTENTS", `
      <div class="card toc">
        ${rows.map(([main, sub, page]) => `
          <div class="toc-row">
            <div>
              <div class="toc-main">${main}</div>
              <div class="toc-sub">${sub}</div>
            </div>
            <div class="toc-page">P${page}</div>
          </div>
        `).join("")}
      </div>
      <div class="footer">マンガでわかる ChatGPT 5.5時代の結論</div>
    `);
  }
  if (kind === "author") {
    return base("著者紹介", "AUTHOR", `
      <div class="card profile">
        <div class="name">Yuichi</div>
        <div class="lead">生成AIを、仕事と出版制作にどう組み込むかを実践しながら発信している。</div>
        <div class="body-text">
          <p>AI活用、電子書籍制作、コンテンツ制作、業務改善をテーマに、日々の実務で使える生成AIの使い方を研究・実践している。</p>
          <p>本書では、ChatGPT・Claude・Geminiを比較したうえで、「自分の仕事に合う中心を持つこと」と「変化に合わせて更新できること」を重視した。</p>
          <p>完璧な正解を探し続けるより、今日の仕事を一つ進める。そのための現実的なAI活用を、これからも整理していく。</p>
        </div>
      </div>
      <div class="footer">YN出版</div>
    `);
  }
  return base("奥付", "COLOPHON", `
    <div class="card info-table">
      ${[
        ["書名", "マンガでわかる ChatGPT 5.5時代の結論"],
        ["サブタイトル", "一周回って、いまはChatGPTだけでいい"],
        ["著者", "Yuichi"],
        ["発行", "YN出版"],
        ["制作日", "2026年5月14日"],
        ["形式", "固定レイアウトEPUB"],
        ["本文基準日", "2026年5月時点"],
        ["著作権", "Copyright © 2026 Yuichi. All rights reserved."],
      ].map(([key, value]) => `
        <div class="info-row">
          <div class="info-key">${key}</div>
          <div class="info-value">${value}</div>
        </div>
      `).join("")}
    </div>
    <div class="note">本書は生成AIの変化が速い領域を扱っています。最新の仕様、料金、利用条件は、各サービスの公式情報を確認してください。</div>
  `);
}

function base(title, kicker, body) {
  return `<!doctype html><html lang="ja"><head><meta charset="utf-8" />
  <style>${pageCss}</style></head><body>
  <main class="page">
    <div class="kicker">${kicker}</div>
    <h1>${title}</h1>
    ${body}
  </main>
  </body></html>`;
}

async function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1024, height: 1536 }, deviceScaleFactor: 1 });
  for (const kind of ["toc", "author", "colophon"]) {
    const html = htmlFor(kind);
    const htmlPath = path.join(OUT_DIR, `${kind}.html`);
    const pngPath = path.join(OUT_DIR, `${kind}.png`);
    fs.writeFileSync(htmlPath, html, "utf8");
    await page.goto(`file://${htmlPath}`);
    await page.screenshot({ path: pngPath, fullPage: false, type: "png" });
  }
  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
