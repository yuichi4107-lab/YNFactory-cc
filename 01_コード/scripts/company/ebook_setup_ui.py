#!/usr/bin/env python3
"""Local click-choice setup UI for ebook projects.

This is a small localhost-only form used when Codex's built-in selectable
question UI is unavailable in the current collaboration mode.
"""

from __future__ import annotations

import argparse
import json
import re
import socket
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "03_成果物" / "outputs" / "ebook-setup-inputs"
JST = ZoneInfo("Asia/Tokyo")


QUESTIONS = [
    {
        "id": "theme_handling",
        "title": "テーマの扱い",
        "options": [
            {
                "value": "use_input",
                "label": "入力内容のテーマで進める (Recommended)",
                "description": "入力されたテーマを中心に据えて進めます。",
                "recommended": True,
            },
            {
                "value": "expand",
                "label": "入力内容を少し広げて進める",
                "description": "周辺テーマや背景も含めて扱います。",
            },
            {
                "value": "narrow",
                "label": "入力内容を絞り込んで進める",
                "description": "対象や論点を絞り、焦点を明確にします。",
            },
            {
                "value": "other_theme",
                "label": "別テーマを指定する",
                "description": "自由記述欄に新しいテーマを入力します。",
            },
        ],
    },
    {
        "id": "target_reader",
        "title": "想定読者",
        "options": [
            {
                "value": "beginner",
                "label": "初心者・これから始める人 (Recommended)",
                "description": "初めて知る人にもわかる、やさしい導入にします。",
                "recommended": True,
            },
            {
                "value": "business_manager",
                "label": "中小企業の経営者・管理職",
                "description": "経営や組織運営の判断に役立つ内容にします。",
            },
            {
                "value": "practitioner",
                "label": "実務担当者・現場リーダー",
                "description": "現場で実践しやすい内容にします。",
            },
            {
                "value": "expert",
                "label": "専門家・上級者",
                "description": "基礎知識がある読者にも読み応えのある内容にします。",
            },
        ],
    },
    {
        "id": "book_type",
        "title": "本の型",
        "options": [
            {
                "value": "practical",
                "label": "実践書・手順書 (Recommended)",
                "description": "読者が行動に移せる手順と実例を中心にします。",
                "recommended": True,
            },
            {
                "value": "intro",
                "label": "やさしい入門書",
                "description": "基礎から順番に全体像を整理します。",
            },
            {
                "value": "case_story",
                "label": "ストーリー・事例中心",
                "description": "ストーリーや事例を軸に読みやすく構成します。",
            },
            {
                "value": "ideas",
                "label": "考え方・思想を伝える本",
                "description": "主張や考え方の背景を掘り下げて伝えます。",
            },
        ],
    },
    {
        "id": "tone",
        "title": "文体",
        "options": [
            {
                "value": "gentle",
                "label": "やさしいです・ます調 (Recommended)",
                "description": "です・ます調で、専門用語をかみ砕きます。",
                "recommended": True,
            },
            {
                "value": "business",
                "label": "端的でビジネス寄り",
                "description": "要点を簡潔に、実務的な表現で書きます。",
            },
            {
                "value": "conversational",
                "label": "親しみやすい会話調",
                "description": "読みやすさと親しみやすさを優先します。",
            },
            {
                "value": "calm_expert",
                "label": "専門家らしい落ち着いた文体",
                "description": "落ち着きと信頼感を重視して書きます。",
            },
        ],
    },
    {
        "id": "length",
        "title": "文字量",
        "options": [
            {
                "value": "100000",
                "label": "約100,000字 (Recommended)",
                "description": "本格的に掘り下げる長編にします。",
                "recommended": True,
            },
            {
                "value": "50000",
                "label": "約50,000字",
                "description": "深さと制作速度のバランスを取ります。",
            },
            {
                "value": "25000",
                "label": "約25,000字",
                "description": "短めにまとめ、早く出版できる形にします。",
            },
            {
                "value": "custom",
                "label": "自由記述で指定",
                "description": "自由記述欄に希望する文字量を入力します。",
            },
        ],
    },
    {
        "id": "image_density",
        "title": "画像密度",
        "options": [
            {
                "value": "standard",
                "label": "標準（章ごとに数点） (Recommended)",
                "description": "章ごとに数点、本文を補う画像を入れます。",
                "recommended": True,
            },
            {
                "value": "few",
                "label": "少なめ",
                "description": "文字中心で、必要な箇所だけ画像を入れます。",
            },
            {
                "value": "many",
                "label": "多め",
                "description": "挿絵や図解を多めに配置します。",
            },
            {
                "value": "diagram_rich",
                "label": "図解中心",
                "description": "概念や手順を図解で理解しやすくします。",
            },
        ],
    },
]

SAFETY_POLICY = "医療・健康・投資・法律などの該当ジャンルでは、断定を避け、根拠を確認して表現する"


def slugify(text: str) -> str:
    text = text.strip().lower()
    if not text:
        return "ebook"
    ascii_text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    if ascii_text:
        return ascii_text[:60]
    return "ebook-setup"


def pick_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"ポート {preferred}〜{preferred + 49} に空きがありません。ほかのアプリを終了してから、もう一度お試しください。")


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def json_for_inline_script(value: object) -> str:
    """Serialize JSON without allowing data to terminate the script element."""
    return (
        json.dumps(value, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def validate_submission(payload: object, expected_theme: str, expected_mode: str) -> dict:
    """Validate and normalize a submitted setup document.

    Labels are checked as well as values so stored ``{value, label}`` pairs are
    always canonical and cannot contain injected markup.
    """
    if not isinstance(payload, dict):
        raise ValueError("入力データはJSONオブジェクトで送信してください。")
    if payload.get("theme") != expected_theme or payload.get("mode") != expected_mode:
        raise ValueError("テーマまたは制作モードが起動画面と一致しません。")

    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise ValueError("すべての質問に回答してください。")

    expected_ids = {question["id"] for question in QUESTIONS}
    if set(answers) != expected_ids:
        missing = [question["title"] for question in QUESTIONS if question["id"] not in answers]
        if missing:
            raise ValueError(f"未回答の質問があります: {', '.join(missing)}")
        raise ValueError("定義されていない質問が含まれています。")

    normalized_answers: dict[str, dict[str, str]] = {}
    for question in QUESTIONS:
        answer = answers[question["id"]]
        if not isinstance(answer, dict):
            raise ValueError(f"{question['title']}の回答形式が正しくありません。")
        value = answer.get("value")
        label = answer.get("label")
        option = next((item for item in question["options"] if item["value"] == value), None)
        if option is None:
            raise ValueError(f"{question['title']}に定義されていない選択肢が含まれています。")
        if label != option["label"]:
            raise ValueError(f"{question['title']}の選択肢ラベルが正しくありません。")
        normalized_answers[question["id"]] = {"value": value, "label": label}

    free_text = payload.get("free_text", "")
    if not isinstance(free_text, str):
        raise ValueError("自由記述は文字列で入力してください。")
    free_text = free_text.strip()
    if normalized_answers["theme_handling"]["value"] == "other_theme" and not free_text:
        raise ValueError("別テーマを指定する場合は、自由記述欄にテーマを入力してください。")
    if normalized_answers["length"]["value"] == "custom" and not free_text:
        raise ValueError("文字量を自由指定する場合は、自由記述欄に希望文字量を入力してください。")

    return {
        "theme": expected_theme,
        "mode": expected_mode,
        "answers": normalized_answers,
        "free_text": free_text,
        "safety_policy": SAFETY_POLICY,
    }


def render_page(theme: str, mode: str) -> bytes:
    questions_json = json_for_inline_script(QUESTIONS)
    theme_json = json_for_inline_script(theme)
    mode_json = json_for_inline_script(mode)
    safe_theme = html_escape(theme)
    safe_mode = html_escape(mode)
    html = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>電子書籍 初回設定</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5b6472;
      --line: #d9dee7;
      --paper: #fbfcfe;
      --panel: #ffffff;
      --accent: #0f766e;
      --accent-soft: #e6f3f1;
      --warn: #9a5b13;
      --blue: #1d4ed8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic", sans-serif;
      background: var(--paper);
      color: var(--ink);
      line-height: 1.6;
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 28px 0 44px;
    }}
    header {{
      display: grid;
      gap: 8px;
      padding: 18px 0 22px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0;
      font-size: clamp(24px, 3vw, 36px);
      letter-spacing: 0;
    }}
    .meta, .note {{
      color: var(--muted);
      font-size: 14px;
    }}
    .note {{
      padding: 12px 14px;
      background: #fff7ed;
      border: 1px solid #fed7aa;
      color: var(--warn);
      border-radius: 8px;
      margin-top: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 22px;
    }}
    fieldset {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 16px;
      margin: 0;
    }}
    legend {{
      font-weight: 700;
      padding: 0 6px;
    }}
    .choices {{
      display: grid;
      gap: 10px;
      margin-top: 10px;
    }}
    .choice {{
      display: grid;
      grid-template-columns: 22px 1fr;
      gap: 10px;
      align-items: start;
      min-height: 76px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      cursor: pointer;
      background: #fff;
    }}
    .choice:hover {{
      border-color: #9fb6c5;
      background: #f8fbfc;
    }}
    .choice:has(input:checked) {{
      border-color: var(--accent);
      background: var(--accent-soft);
      box-shadow: inset 0 0 0 1px var(--accent);
    }}
    input[type="radio"] {{
      width: 18px;
      height: 18px;
      margin-top: 3px;
      accent-color: var(--accent);
    }}
    .choice-title {{
      font-weight: 700;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .badge {{
      font-size: 12px;
      color: var(--blue);
      border: 1px solid #bfdbfe;
      background: #eff6ff;
      border-radius: 999px;
      padding: 1px 8px;
      font-weight: 600;
    }}
    .desc {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 3px;
    }}
    .free {{
      margin-top: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 16px;
    }}
    textarea {{
      width: 100%;
      min-height: 118px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: inherit;
    }}
    .actions {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 18px;
      flex-wrap: wrap;
    }}
    button {{
      border: 0;
      border-radius: 8px;
      background: var(--accent);
      color: #fff;
      padding: 12px 18px;
      font-weight: 700;
      font-size: 15px;
      cursor: pointer;
    }}
    button:hover {{ filter: brightness(0.96); }}
    #status {{
      color: var(--muted);
      font-size: 14px;
    }}
    .saved {{
      margin-top: 16px;
      padding: 14px;
      border: 1px solid #bbf7d0;
      background: #f0fdf4;
      color: #166534;
      border-radius: 8px;
      display: none;
      word-break: break-all;
    }}
    @media (max-width: 780px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>電子書籍 初回設定</h1>
      <div class="meta">テーマ: <strong>{safe_theme}</strong> / モード: {safe_mode}</div>
      <div class="note">医療・健康・投資・法律などの該当ジャンルでは、断定を避け、根拠を確認して表現します。</div>
    </header>

    <form id="setup-form">
      <section id="questions" class="grid"></section>

      <section class="free">
        <label for="free_text"><strong>自由記述</strong></label>
        <p class="meta">入れたい論点、避けたい表現、タイトル案、著者名などがあれば書いてください。</p>
        <textarea id="free_text" name="free_text" placeholder="例: 入れたい事例、避けたい表現、希望する著者名など"></textarea>
      </section>

      <div class="actions">
        <button type="submit">この内容を保存</button>
        <span id="status">選択後、保存ボタンを押してください。</span>
      </div>
      <div id="saved" class="saved"></div>
    </form>
  </main>

  <script>
    const questions = {questions_json};
    const container = document.getElementById("questions");

    function render() {{
      container.innerHTML = questions.map((q) => `
        <fieldset>
          <legend>${{q.title}}</legend>
          <div class="choices">
            ${{q.options.map((opt, index) => `
              <label class="choice">
                <input type="radio" name="${{q.id}}" value="${{opt.value}}" ${{opt.recommended ? "checked" : ""}}>
                <span>
                  <span class="choice-title">
                    ${{opt.label}}
                  </span>
                  <span class="desc">${{opt.description}}</span>
                </span>
              </label>
            `).join("")}}
          </div>
        </fieldset>
      `).join("");
    }}

    function selectedLabel(question, value) {{
      const opt = question.options.find((item) => item.value === value);
      return opt ? opt.label : value;
    }}

    document.getElementById("setup-form").addEventListener("submit", async (event) => {{
      event.preventDefault();
      const answers = {{}};
      for (const question of questions) {{
        const selected = document.querySelector(`input[name="${{question.id}}"]:checked`);
        if (!selected) {{
          document.getElementById("status").textContent = `${{question.title}}を選択してください。`;
          return;
        }}
        answers[question.id] = {{
          value: selected.value,
          label: selectedLabel(question, selected.value),
        }};
      }}
      const payload = {{
        theme: {theme_json},
        mode: {mode_json},
        answers,
        free_text: document.getElementById("free_text").value.trim(),
        safety_policy: {json_for_inline_script(SAFETY_POLICY)},
      }};
      document.getElementById("status").textContent = "保存中です...";
      const response = await fetch("/submit", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(payload),
      }});
      const result = await response.json();
      if (!response.ok) {{
        document.getElementById("status").textContent = result.error || "保存できませんでした。";
        return;
      }}
      document.getElementById("status").textContent = "保存しました。";
      const saved = document.getElementById("saved");
      saved.style.display = "block";
      saved.textContent = `保存先: ${{result.path}}`;
    }});

    render();
  </script>
</body>
</html>
"""
    return html.encode("utf-8")


class SetupHandler(BaseHTTPRequestHandler):
    server_version = "EbookSetupUI/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    @property
    def app(self) -> "SetupServer":
        return self.server  # type: ignore[return-value]

    def send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = render_page(theme=self.app.theme, mode=self.app.mode)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/latest":
            if self.app.latest_path and self.app.latest_path.exists():
                self.send_json(
                    HTTPStatus.OK,
                    {
                        "path": str(self.app.latest_path),
                        "data": json.loads(self.app.latest_path.read_text(encoding="utf-8")),
                    },
                )
                return
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "まだ保存済みの初回設定がありません。フォームで選択して保存してください。"})
            return
        self.send_json(HTTPStatus.NOT_FOUND, {"error": "指定されたページは見つかりません。"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/submit":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "指定されたページは見つかりません。"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "入力データの長さが正しくありません。"})
            return
        if length <= 0 or length > 1_000_000:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "入力データの長さが正しくありません。"})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "入力データの形式が正しくありません。画面を再読み込みしてから、もう一度保存してください。"})
            return

        try:
            payload = validate_submission(payload, self.app.theme, self.app.mode)
        except ValueError as exc:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        now = datetime.now(JST)
        theme = payload["theme"]
        payload["created_at"] = now.isoformat()
        payload["source"] = "local_ebook_setup_ui"

        out_dir = self.app.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{slugify(theme)}-setup.json"
        out_path = out_dir / filename
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        latest_path = out_dir / "latest.json"
        latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.app.latest_path = latest_path

        self.send_json(HTTPStatus.OK, {"ok": True, "path": str(out_path)})


class SetupServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], theme: str, mode: str, output_dir: Path):
        super().__init__(server_address, SetupHandler)
        self.theme = theme
        self.mode = mode
        self.output_dir = output_dir
        self.latest_path: Path | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="電子書籍制作の初回設定を選ぶローカル画面を起動します。")
    parser.add_argument("--theme", default="", help="初回設定画面に表示するテーマです。")
    parser.add_argument("--mode", default="theme-to-ebook", help="制作フローの表示名です。")
    parser.add_argument("--host", default="127.0.0.1", help="待受先ホスト（既定: 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8765, help="優先して使うポート番号（既定: 8765）")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="設定JSONの保存先ディレクトリです。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    port = pick_port(args.host, args.port)
    server = SetupServer((args.host, port), theme=args.theme, mode=args.mode, output_dir=args.output_dir)
    query = urlencode({"theme": args.theme, "mode": args.mode})
    url = f"http://{args.host}:{port}/?{query}"
    print(f"ebook_setup_ui_url={url}", flush=True)
    print(f"ebook_setup_output_dir={args.output_dir}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
