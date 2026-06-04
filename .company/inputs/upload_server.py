#!/usr/bin/env python3
"""
One-shot uploader for external inputs.

Usage:
    python upload_server.py --host 0.0.0.0 --port 8787

Uploaded items are saved into .company/inputs/00_INPUT_BOX/ and immediately
imported by import_drive_inbox.py.
"""
import argparse
import cgi
import datetime as dt
import html
import json
import os
import re
import socket
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
INPUT_BOX_DIR = Path(os.getenv("YN_INPUT_BOX", BASE_DIR / "00_INPUT_BOX"))
PYTHON = sys.executable


def now_jst() -> dt.datetime:
    return dt.datetime.now().astimezone()


def slugify(value: str, fallback: str = "input") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:48] or fallback


def safe_filename(value: str, fallback: str = "upload.bin") -> str:
    value = Path(value or fallback).name
    value = re.sub(r'[\\/:*?"<>|]+', "-", value).strip()
    return value or fallback


def get_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def import_command() -> list[str]:
    command = [PYTHON, str(BASE_DIR / "import_drive_inbox.py"), "--inbox", str(INPUT_BOX_DIR)]
    env_to_arg = {
        "YN_INPUT_RAW_BASE": "--raw-base",
        "YN_INPUT_ORGANIZED_DIR": "--organized-dir",
        "YN_INPUT_INDEX_DIR": "--index-dir",
        "YN_INPUT_STATE_FILE": "--state-file",
    }
    for env_name, arg_name in env_to_arg.items():
        value = os.getenv(env_name, "").strip()
        if value:
            command.extend([arg_name, value])
    return command


def read_field(form: cgi.FieldStorage, name: str, default: str = "") -> str:
    field = form.getfirst(name, default)
    return str(field).strip()


def read_files(form: cgi.FieldStorage, name: str) -> list[cgi.FieldStorage]:
    value = form[name] if name in form else []
    if isinstance(value, list):
        return [item for item in value if item.filename]
    if getattr(value, "filename", None):
        return [value]
    return []


def render_page(message: str = "", error: str = "") -> bytes:
    escaped_message = html.escape(message)
    escaped_error = html.escape(error)
    body = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YNFactory Input Upload</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    body {{
      margin: 0;
      background: Canvas;
      color: CanvasText;
    }}
    main {{
      width: min(720px, calc(100vw - 32px));
      margin: 24px auto;
    }}
    h1 {{
      font-size: 24px;
      margin: 0 0 16px;
    }}
    form {{
      display: grid;
      gap: 14px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-weight: 600;
    }}
    input, textarea, select, button {{
      font: inherit;
      box-sizing: border-box;
      width: 100%;
      border: 1px solid color-mix(in srgb, CanvasText 24%, transparent);
      border-radius: 8px;
      padding: 10px 12px;
      background: Canvas;
      color: CanvasText;
    }}
    textarea {{
      min-height: 140px;
      resize: vertical;
    }}
    button {{
      cursor: pointer;
      font-weight: 700;
      background: #155eef;
      border-color: #155eef;
      color: white;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .message {{
      border: 1px solid #15803d;
      background: color-mix(in srgb, #15803d 12%, transparent);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 14px;
    }}
    .error {{
      border: 1px solid #b42318;
      background: color-mix(in srgb, #b42318 12%, transparent);
      border-radius: 8px;
      padding: 10px 12px;
      margin-bottom: 14px;
    }}
    .hint {{
      font-size: 13px;
      opacity: .75;
      font-weight: 400;
    }}
    @media (max-width: 640px) {{
      .row {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>インプット登録</h1>
    {f'<div class="message">{escaped_message}</div>' if message else ''}
    {f'<div class="error">{escaped_error}</div>' if error else ''}
    <form method="post" action="/upload" enctype="multipart/form-data">
      <label>タイトル
        <input name="title" autocomplete="off" placeholder="未入力ならファイル名から自動設定">
      </label>
      <label>テキスト・メモ
        <textarea name="text" placeholder="保存したいメモ、URL、引用など"></textarea>
      </label>
      <label>URL
        <input name="url" inputmode="url" placeholder="https://example.com">
      </label>
      <label>ファイル
        <input name="files" type="file" multiple>
        <span class="hint">画像、PDF、Office、テキストなど。スマホでは写真/カメラ/Filesから選べます。</span>
      </label>
      <div class="row">
        <label>タグ
          <input name="tags" placeholder="client proposal idea">
        </label>
        <label>関連プロジェクト
          <input name="related_project" placeholder="project-name">
        </label>
      </div>
      <div class="row">
        <label>優先度
          <select name="priority">
            <option value="normal">normal</option>
            <option value="high">high</option>
            <option value="low">low</option>
          </select>
        </label>
        <label>TODO候補
          <select name="todo_candidate">
            <option value="false">しない</option>
            <option value="true">する</option>
          </select>
        </label>
      </div>
      <label>TODO候補メモ
        <textarea name="todo_candidates" placeholder="1行に1件ずつ"></textarea>
      </label>
      <label>アップロードトークン
        <input name="token" autocomplete="off" placeholder="設定している場合のみ入力">
      </label>
      <button type="submit">登録する</button>
    </form>
  </main>
</body>
</html>"""
    return body.encode("utf-8")


class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        self.respond(render_page())

    def do_POST(self) -> None:
        if self.path != "/upload":
            self.send_error(404)
            return
        try:
            self.handle_upload()
        except Exception as exc:
            self.respond(render_page(error=f"登録に失敗しました: {exc}"), status=500)

    def respond(self, content: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_upload(self) -> None:
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
        required_token = os.getenv("YN_INPUT_UPLOAD_TOKEN", "").strip()
        provided_token = read_field(form, "token")
        if required_token and provided_token != required_token:
            self.respond(render_page(error="アップロードトークンが違います。"), status=403)
            return

        title = read_field(form, "title")
        text = read_field(form, "text")
        url = read_field(form, "url")
        tags = read_field(form, "tags")
        related_project = read_field(form, "related_project")
        priority = read_field(form, "priority", "normal")
        todo_candidate = read_field(form, "todo_candidate", "false").lower() == "true"
        todo_candidates = read_field(form, "todo_candidates")
        files = read_files(form, "files")

        if not any([title, text, url, files]):
            self.respond(render_page(error="テキスト、URL、ファイルのどれかを入力してください。"), status=400)
            return

        now = now_jst()
        inferred_title = title or (safe_filename(files[0].filename).rsplit(".", 1)[0] if files else "input")
        input_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{slugify(inferred_title)}"
        target_dir = INPUT_BOX_DIR / input_id
        files_dir = target_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        if text or url:
            note_parts = []
            if text:
                note_parts.append(text)
            if url:
                note_parts.append(url)
            (target_dir / "note.md").write_text("\n\n".join(note_parts).strip() + "\n", encoding="utf-8")

        saved_files = []
        for field in files:
            filename = safe_filename(field.filename)
            destination = files_dir / filename
            counter = 2
            while destination.exists():
                stem = destination.stem
                suffix = destination.suffix
                destination = files_dir / f"{stem}-{counter}{suffix}"
                counter += 1
            with destination.open("wb") as fh:
                shutil_buffer = field.file.read()
                fh.write(shutil_buffer)
            saved_files.append(str(destination.relative_to(INPUT_BOX_DIR)))

        metadata = {
            "title": inferred_title,
            "tags": tags.split() if tags else [],
            "priority": priority,
            "related_project": related_project,
            "todo_candidate": todo_candidate,
            "todo_candidates": [line.strip() for line in todo_candidates.splitlines() if line.strip()],
            "notes": "upload_server.py",
            "uploaded_at": now.isoformat(timespec="seconds"),
            "saved_files": saved_files,
        }
        (target_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = subprocess.run(
            import_command(),
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            self.respond(render_page(error=f"アップロードは保存済みですが、取り込みに失敗しました: {result.stderr[-500:]}"), status=500)
            return
        self.respond(render_page(message=f"登録しました: {input_id}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start one-shot input upload server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    INPUT_BOX_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), UploadHandler)
    lan_ip = get_lan_ip()
    print(f"Upload server: http://127.0.0.1:{args.port}")
    print(f"LAN URL:       http://{lan_ip}:{args.port}")
    print("Stop with Ctrl+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
