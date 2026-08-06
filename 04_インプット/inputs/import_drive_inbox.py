#!/usr/bin/env python3
from __future__ import annotations

"""
Import files dropped into the Google Drive input box.

Default input box:
    <workspace>/04_インプット/inputs/00_INPUT_BOX

Outputs:
    04_インプット/inputs/intake/raw/YYYY-MM-DD/<input-id>/
    04_インプット/inputs/organized/external/YYYY-MM-DD-<input-id>.md
    04_インプット/inputs/indexes/external-*.md
"""
import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
COMPANY_DIR = BASE_DIR.parent
ROOT_DIR = COMPANY_DIR.parent
DEFAULT_INBOX_DIR = Path(os.getenv("YN_INPUT_BOX", BASE_DIR / "00_INPUT_BOX"))
RAW_BASE_DIR = BASE_DIR / "intake" / "raw"
STATE_FILE = BASE_DIR / "intake" / "state" / "drive_inbox_imported.json"
ORGANIZED_DIR = BASE_DIR / "organized" / "external"
INDEX_DIR = BASE_DIR / "indexes"

IGNORE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
    "README.md",
    "README.txt",
    "metadata.json",
    "import_now_mac.sh",
    "import_now_windows.bat",
}
IGNORE_DIRS = {"_archive", "_ignore", "_processed", "_samples", "_templates", "__pycache__"}
TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".tsv",
    ".json",
    ".yaml",
    ".yml",
    ".html",
    ".htm",
    ".url",
    ".webloc",
    ".rtf",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif", ".tiff", ".bmp"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".pages", ".numbers", ".key"}
GOOGLE_DRIVE_NATIVE_EXTENSIONS = {".gdoc", ".gsheet", ".gslides", ".gdraw", ".gform", ".gsite"}
MAX_TEXT_BYTES = 300_000
MAX_NORMALIZED_CHARS = 120_000
URL_FETCH_BYTES = 500_000
URL_RE = re.compile(r"https?://[^\s<>'\")]+", re.IGNORECASE)


@dataclass
class SourceFile:
    source_path: Path
    relative_path: str
    size: int
    sha256: str
    mime_type: str
    kind: str
    text_excerpt: str = ""
    normalized_text: str = ""
    extraction_method: str = ""
    extraction_status: str = "not_attempted"
    extraction_notes: str = ""
    urls: list[str] = field(default_factory=list)


@dataclass
class ImportItem:
    source_path: Path
    relative_path: str
    is_directory: bool
    files: list[SourceFile]
    metadata: dict[str, Any]
    signature: str


@dataclass
class ImportedItem:
    input_id: str
    item: ImportItem
    raw_dir: Path
    organized_path: Path
    imported_at: str
    title: str
    tags: list[str]
    priority: str
    related_project: str
    todo_candidate: bool
    todo_candidates: list[str]
    notes: str


def now_jst() -> dt.datetime:
    return dt.datetime.now().astimezone()


def today_string() -> str:
    return now_jst().strftime("%Y-%m-%d")


def workspace_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT_DIR.resolve()))
    except ValueError:
        return str(path)


def slugify(value: str, fallback: str = "input") -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:48] or fallback


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_excerpt(path: Path) -> str:
    try:
        data = path.read_bytes()[:MAX_TEXT_BYTES]
        return data.decode("utf-8-sig", errors="replace").strip()
    except OSError:
        return ""


class PlainTextHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
        if tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        text = unescape(" ".join(self.parts))
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r"\n\s+", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def truncate_normalized(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_NORMALIZED_CHARS:
        return text
    return text[:MAX_NORMALIZED_CHARS].rstrip() + "\n\n...[truncated]"


def run_command(args: list[str], timeout: int = 20) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def textutil_extract(path: Path) -> str:
    return run_command(["textutil", "-convert", "txt", "-stdout", str(path)], timeout=30)


def zip_member_text(path: Path, member_patterns: list[str]) -> str:
    if not zipfile.is_zipfile(path):
        return ""
    parts = []
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not any(re.match(pattern, name) for pattern in member_patterns):
                continue
            try:
                raw = archive.read(name).decode("utf-8", errors="replace")
            except (KeyError, RuntimeError):
                continue
            values = re.findall(r">([^<>]+)<", raw)
            text = " ".join(unescape(value).strip() for value in values if value.strip())
            if text:
                parts.append(f"## {name}\n{text}")
    return "\n\n".join(parts).strip()


def extract_docx_text(path: Path) -> str:
    return zip_member_text(
        path,
        [
            r"word/document\.xml$",
            r"word/header\d*\.xml$",
            r"word/footer\d*\.xml$",
            r"word/footnotes\.xml$",
            r"word/endnotes\.xml$",
        ],
    )


def extract_xlsx_text(path: Path) -> str:
    return zip_member_text(path, [r"xl/sharedStrings\.xml$", r"xl/worksheets/sheet\d+\.xml$"])


def extract_pptx_text(path: Path) -> str:
    return zip_member_text(path, [r"ppt/slides/slide\d+\.xml$", r"ppt/notesSlides/notesSlide\d+\.xml$"])


def extract_pdf_text(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        parts = []
        for index, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if text.strip():
                parts.append(f"## Page {index}\n{text.strip()}")
        if parts:
            return "\n\n".join(parts), "pypdf"
    except Exception:
        pass

    text = run_command(["pdftotext", str(path), "-"], timeout=30)
    if text:
        return text, "pdftotext"
    return "", ""


def extract_image_text(path: Path) -> tuple[str, str]:
    text = run_command(["tesseract", str(path), "stdout", "-l", "jpn+eng"], timeout=45)
    if text:
        return text, "tesseract"
    return "", ""


def fetch_url_text(url: str) -> tuple[str, str]:
    try:
        request = Request(url, headers={"User-Agent": "YNFactoryInputImporter/1.0"})
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(URL_FETCH_BYTES)
    except (OSError, URLError, ValueError):
        return "", ""
    encoding_match = re.search(r"charset=([\w.-]+)", content_type, re.IGNORECASE)
    encoding = encoding_match.group(1) if encoding_match else "utf-8"
    text = raw.decode(encoding, errors="replace")
    if "html" in content_type.lower() or re.search(r"<html|<body", text, re.IGNORECASE):
        parser = PlainTextHTMLParser()
        parser.feed(text)
        return parser.text(), "url-html"
    return text.strip(), "url-text"


def normalize_file_text(path: Path, kind: str, text_excerpt: str, urls: list[str]) -> tuple[str, str, str, str]:
    suffix = path.suffix.lower()
    if kind == "drive-native":
        lines = [
            "Google Drive native file shortcut.",
            "",
            f"- local_file: `{path.name}`",
            "- body_status: not_in_local_shortcut",
            "",
            "## URLs",
            "",
            *(f"- {url}" for url in urls),
            "" if urls else "_URLなし_",
            "",
            "## Local Shortcut Content",
            "",
            text_excerpt or "_ローカルショートカット本文なし_",
        ]
        return (
            truncate_normalized("\n".join(lines)),
            "google-drive-shortcut",
            "needs_export",
            "Google Docs/Sheets/Slides ネイティブ本文はローカルショートカット内にないため、.docx / .txt / .pdf 等へのエクスポートが必要です。",
        )
    if kind in {"text", "url"}:
        parts = [text_excerpt] if text_excerpt else []
        for url in urls[:3]:
            fetched, method = fetch_url_text(url)
            if fetched:
                parts.append(f"\n\n# URL Snapshot: {url}\n\n{fetched}")
                return truncate_normalized("\n".join(parts)), f"text+{method}", "ok", ""
        if parts:
            return truncate_normalized("\n".join(parts)), "text", "ok", ""
        return "", "text", "empty", "テキスト本文を抽出できませんでした。"

    if suffix == ".docx":
        text = extract_docx_text(path)
        if text:
            return truncate_normalized(text), "docx-zip", "ok", ""
        text = textutil_extract(path)
        return (
            truncate_normalized(text),
            "textutil" if text else "",
            "ok" if text else "unavailable",
            "" if text else "DOCX本文を抽出できませんでした。",
        )
    if suffix == ".xlsx":
        text = extract_xlsx_text(path)
        return (
            truncate_normalized(text),
            "xlsx-zip" if text else "",
            "ok" if text else "unavailable",
            "" if text else "XLSX本文を抽出できませんでした。",
        )
    if suffix == ".pptx":
        text = extract_pptx_text(path)
        return (
            truncate_normalized(text),
            "pptx-zip" if text else "",
            "ok" if text else "unavailable",
            "" if text else "PPTX本文を抽出できませんでした。",
        )
    if suffix == ".pdf":
        text, method = extract_pdf_text(path)
        return (
            truncate_normalized(text),
            method,
            "ok" if text else "needs_ocr_or_dependency",
            "" if text else "PDF本文を抽出できませんでした。スキャンPDFの場合はOCRが必要です。",
        )
    if suffix in IMAGE_EXTENSIONS:
        text, method = extract_image_text(path)
        return (
            truncate_normalized(text),
            method,
            "ok" if text else "needs_ocr_dependency",
            "" if text else "画像OCRには tesseract が必要です。原本は保存済みです。",
        )

    text = textutil_extract(path)
    if text:
        return truncate_normalized(text), "textutil", "ok", ""
    return "", "", "unsupported", "この拡張子は原本保存のみ実施しました。必要なら追加の抽出器を実装します。"


def detect_kind(path: Path, mime_type: str) -> str:
    suffix = path.suffix.lower()
    if suffix in GOOGLE_DRIVE_NATIVE_EXTENSIONS:
        return "drive-native"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in DOCUMENT_EXTENSIONS:
        return "document"
    if suffix in TEXT_EXTENSIONS or mime_type.startswith("text/"):
        return "text"
    return "file"


def extract_urls(path: Path, text: str) -> list[str]:
    urls = URL_RE.findall(text or "")
    if path.suffix.lower() == ".url":
        for line in text.splitlines():
            if line.lower().startswith("url="):
                urls.append(line.split("=", 1)[1].strip())
    if path.suffix.lower() == ".webloc":
        urls.extend(re.findall(r"<string>(https?://.*?)</string>", text, re.IGNORECASE))
    seen = set()
    result = []
    for url in urls:
        url = url.strip()
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


def load_source_file(path: Path, root: Path) -> SourceFile:
    stat = path.stat()
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    kind = detect_kind(path, mime_type)
    text_excerpt = read_text_excerpt(path) if kind in {"text", "drive-native"} else ""
    urls = extract_urls(path, text_excerpt)
    if urls and kind == "text":
        kind = "url"
    normalized_text, extraction_method, extraction_status, extraction_notes = normalize_file_text(
        path, kind, text_excerpt, urls
    )
    return SourceFile(
        source_path=path,
        relative_path=workspace_path(path),
        size=stat.st_size,
        sha256=sha256_file(path),
        mime_type=mime_type,
        kind=kind,
        text_excerpt=text_excerpt,
        normalized_text=normalized_text,
        extraction_method=extraction_method,
        extraction_status=extraction_status,
        extraction_notes=extraction_notes,
        urls=urls,
    )


def should_ignore(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if path.name in IGNORE_NAMES:
        return True
    if path.is_dir() and path.name in IGNORE_DIRS:
        return True
    if path.name.endswith(".meta.json"):
        return True
    return False


def iter_top_level_items(inbox_dir: Path) -> list[Path]:
    if not inbox_dir.exists():
        return []
    return sorted(path for path in inbox_dir.iterdir() if not should_ignore(path))


def iter_files_for_item(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    files = []
    for child in sorted(path.rglob("*")):
        if child.is_file() and not should_ignore(child):
            files.append(child)
    return files


def file_sidecar_paths(path: Path) -> list[Path]:
    return [
        path.with_name(path.name + ".meta.json"),
        path.with_suffix(".meta.json"),
    ]


def load_metadata(path: Path) -> dict[str, Any]:
    candidates = []
    if path.is_dir():
        candidates.append(path / "metadata.json")
    else:
        candidates.extend(file_sidecar_paths(path))
    for candidate in candidates:
        if candidate.exists():
            data = read_json(candidate, {})
            return data if isinstance(data, dict) else {}
    return {}


def normalize_tags(value: Any) -> list[str]:
    if isinstance(value, str):
        parts = re.split(r"[,#\s]+", value)
    elif isinstance(value, list):
        parts = [str(item) for item in value]
    else:
        parts = []
    tags = []
    seen = set()
    for part in parts:
        tag = part.strip().strip("#")
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def normalize_todos(metadata: dict[str, Any]) -> list[str]:
    candidates = metadata.get("todo_candidates", metadata.get("todos", []))
    if isinstance(candidates, str):
        values = [line.strip("-* \t") for line in candidates.splitlines()]
    elif isinstance(candidates, list):
        values = [str(item).strip() for item in candidates]
    else:
        values = []
    return [item for item in values if item]


def build_signature(relative_path: str, files: list[SourceFile], metadata: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(relative_path.encode("utf-8"))
    for file in files:
        digest.update(file.relative_path.encode("utf-8"))
        digest.update(str(file.size).encode("ascii"))
        digest.update(file.sha256.encode("ascii"))
    digest.update(json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def build_import_item(path: Path, inbox_dir: Path) -> ImportItem | None:
    if not path.exists() or should_ignore(path):
        return None
    files = [load_source_file(file, inbox_dir) for file in iter_files_for_item(path)]
    if not files:
        return None
    metadata = load_metadata(path)
    relative_path = workspace_path(path)
    return ImportItem(
        source_path=path,
        relative_path=relative_path,
        is_directory=path.is_dir(),
        files=files,
        metadata=metadata,
        signature=build_signature(relative_path, files, metadata),
    )


def title_for(item: ImportItem) -> str:
    title = str(item.metadata.get("title", "")).strip()
    if title:
        return title
    if item.is_directory:
        return item.source_path.name
    if len(item.files) == 1:
        return item.files[0].source_path.stem
    return item.source_path.name


def choose_input_type(item: ImportItem) -> str:
    kinds = {file.kind for file in item.files}
    if item.is_directory:
        return "folder"
    if "url" in kinds:
        return "url"
    if len(kinds) == 1:
        return next(iter(kinds))
    return "mixed"


def copy_raw_files(item: ImportItem, raw_dir: Path) -> list[dict[str, Any]]:
    files_dir = raw_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for source in item.files:
        destination = files_dir / source.source_path.name
        if destination.exists():
            stem = destination.stem
            suffix = destination.suffix
            destination = files_dir / f"{stem}-{source.sha256[:8]}{suffix}"
        shutil.copy2(source.source_path, destination)
        copied.append(
            {
                "original_path": source.relative_path,
                "raw_copy": workspace_path(destination),
                "size": source.size,
                "sha256": source.sha256,
                "mime_type": source.mime_type,
                "kind": source.kind,
                "extraction_status": source.extraction_status,
                "extraction_method": source.extraction_method,
                "extraction_notes": source.extraction_notes,
                "urls": source.urls,
            }
        )
    return copied


def normalized_filename(source: SourceFile) -> str:
    stem = slugify(source.source_path.stem, "file")
    return f"{stem}-{source.sha256[:8]}.md"


def write_normalized_files(item: ImportItem, raw_dir: Path) -> list[dict[str, Any]]:
    normalized_dir = raw_dir / "normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    combined_lines = [
        f"# Normalized Input Content",
        "",
        f"- source: `{item.relative_path}`",
        f"- file_count: {len(item.files)}",
        "",
    ]
    for source in item.files:
        path = normalized_dir / normalized_filename(source)
        lines = [
            f"# {source.source_path.name}",
            "",
            f"- original: `{source.relative_path}`",
            f"- kind: {source.kind}",
            f"- mime_type: {source.mime_type}",
            f"- sha256: {source.sha256}",
            f"- extraction_status: {source.extraction_status}",
            f"- extraction_method: {source.extraction_method or '-'}",
            f"- extraction_notes: {source.extraction_notes or '-'}",
            "",
            "## URLs",
            "",
            *(f"- {url}" for url in source.urls),
            "" if source.urls else "_URLなし_",
            "",
            "## Text",
            "",
            source.normalized_text or "_抽出テキストなし。原本を参照してください。_",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        outputs.append(
            {
                "original_path": source.relative_path,
                "normalized_path": workspace_path(path),
                "extraction_status": source.extraction_status,
                "extraction_method": source.extraction_method,
                "extraction_notes": source.extraction_notes,
            }
        )
        combined_lines.extend(
            [
                f"## {source.source_path.name}",
                "",
                f"- original: `{source.relative_path}`",
                f"- normalized_file: `{workspace_path(path)}`",
                f"- extraction_status: {source.extraction_status}",
                f"- extraction_method: {source.extraction_method or '-'}",
                "",
                source.normalized_text or "_抽出テキストなし。原本を参照してください。_",
                "",
            ]
        )
    combined_path = normalized_dir / "all-normalized-content.md"
    combined_path.write_text("\n".join(combined_lines), encoding="utf-8")
    outputs.append(
        {
            "original_path": item.relative_path,
            "normalized_path": workspace_path(combined_path),
            "extraction_status": "combined",
            "extraction_method": "import_drive_inbox.py",
            "extraction_notes": "全ファイルの正規化テキストを結合した入口です。",
        }
    )
    return outputs


def render_file_list(files: list[SourceFile], raw_dir: Path) -> list[str]:
    lines = []
    for file in files:
        lines.append(
            f"- `{file.relative_path}` | kind:{file.kind} | size:{file.size} | sha256:{file.sha256[:12]}"
        )
    if lines:
        lines.append(f"- raw copy directory: `{workspace_path(raw_dir / 'files')}`")
    return lines or ["_添付ファイルなし_"]


def render_urls(files: list[SourceFile]) -> list[str]:
    urls = []
    for file in files:
        for url in file.urls:
            urls.append((url, file.relative_path))
    if not urls:
        return ["_URLなし_"]
    return [f"- {url} | source:`{source}`" for url, source in urls]


def render_text_excerpt(files: list[SourceFile]) -> list[str]:
    blocks = []
    for file in files:
        if not file.normalized_text:
            continue
        excerpt = file.normalized_text
        if len(excerpt) > 4000:
            excerpt = excerpt[:4000].rstrip() + "\n..."
        blocks.extend([f"### {file.source_path.name}", "", "```text", excerpt, "```", ""])
    return blocks or ["_抽出テキストなし。raw 原本または normalized レポートを参照してください。_"]


def render_extraction_status(files: list[SourceFile], raw_dir: Path) -> list[str]:
    lines = [f"- normalized入口: `{workspace_path(raw_dir / 'normalized' / 'all-normalized-content.md')}`"]
    for file in files:
        lines.append(
            f"- `{file.relative_path}` | status:{file.extraction_status} | method:{file.extraction_method or '-'}"
        )
        if file.extraction_notes:
            lines.append(f"  - note: {file.extraction_notes}")
    return lines


def render_todo_candidates(imported: ImportedItem) -> list[str]:
    if imported.todo_candidates:
        return [f"- [ ] {todo}" for todo in imported.todo_candidates]
    if imported.todo_candidate:
        return ["- [ ] 内容を確認して、必要なら日別TODOへ昇格する"]
    return ["_明示されたTODO候補なし_"]


def render_organized(imported: ImportedItem) -> str:
    item = imported.item
    input_type = choose_input_type(item)
    tags = ["external", "drive-inbox", input_type, *imported.tags]
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    raw_meta_path = imported.raw_dir / "metadata.json"

    lines = [
        "---",
        f"date: {today_string()}",
        "source: drive-inbox",
        "type: organized-input",
        f"input_type: {input_type}",
        f"input_id: {imported.input_id}",
        f"imported_at: {imported.imported_at}",
        f"title: {json.dumps(imported.title, ensure_ascii=False)}",
        f"priority: {imported.priority}",
        f"related_project: {json.dumps(imported.related_project, ensure_ascii=False)}",
        f"todo_candidate: {str(imported.todo_candidate).lower()}",
        f"raw_source: {workspace_path(imported.raw_dir)}",
        "tags:",
        tag_lines,
        "---",
        "",
        f"# 外部インプット - {imported.title}",
        "",
        "## 出典",
        "",
        f"- 投入口: `{item.relative_path}`",
        f"- raw保存先: `{workspace_path(imported.raw_dir)}`",
        f"- raw metadata: `{workspace_path(raw_meta_path)}`",
        f"- ファイル数: {len(item.files)}",
        "",
        "## 登録メタデータ",
        "",
        f"- 優先度: {imported.priority}",
        f"- 関連プロジェクト: {imported.related_project or '-'}",
        f"- タグ: {', '.join(tags) if tags else '-'}",
        f"- 補足: {imported.notes or '-'}",
        "",
        "## URL",
        "",
        *render_urls(item.files),
        "",
        "## テキスト抜粋",
        "",
        *render_text_excerpt(item.files),
        "",
        "## 読み取り正規化",
        "",
        *render_extraction_status(item.files, imported.raw_dir),
        "",
        "## 添付ファイル",
        "",
        *render_file_list(item.files, imported.raw_dir),
        "",
        "## TODO候補",
        "",
        *render_todo_candidates(imported),
        "",
        "## 活用メモ",
        "",
        "- 原本は `04_インプット/inputs/00_INPUT_BOX/` 側と raw 保存先の両方から確認できる。",
        "- AIが原本拡張子を読めない場合は、raw保存先の `normalized/all-normalized-content.md` を参照する。",
        "- TODO候補は日別TODOへ直接入れず、案件状態と優先度を確認してから昇格する。",
        "- 顧客資料・案件資料として継続利用する場合は、案件別ファイルや顧客別メモへ昇格する。",
        "",
    ]
    return "\n".join(lines)


def import_item(
    item: ImportItem,
    raw_base_dir: Path,
    organized_dir: Path,
    dry_run: bool = False,
) -> ImportedItem:
    imported_at = now_jst().isoformat(timespec="seconds")
    title = title_for(item)
    input_id = f"{now_jst().strftime('%Y%m%d-%H%M%S')}-{slugify(title)}-{item.signature[:8]}"
    raw_dir = raw_base_dir / today_string() / input_id
    organized_path = organized_dir / f"{today_string()}-{input_id}.md"
    tags = normalize_tags(item.metadata.get("tags", []))
    priority = str(item.metadata.get("priority", "normal")).strip() or "normal"
    related_project = str(item.metadata.get("related_project", "")).strip()
    todo_candidate = bool(item.metadata.get("todo_candidate", False))
    todo_candidates = normalize_todos(item.metadata)
    notes = str(item.metadata.get("notes", "")).strip()
    imported = ImportedItem(
        input_id=input_id,
        item=item,
        raw_dir=raw_dir,
        organized_path=organized_path,
        imported_at=imported_at,
        title=title,
        tags=tags,
        priority=priority,
        related_project=related_project,
        todo_candidate=todo_candidate,
        todo_candidates=todo_candidates,
        notes=notes,
    )

    if dry_run:
        return imported

    raw_dir.mkdir(parents=True, exist_ok=True)
    copied_files = copy_raw_files(item, raw_dir)
    normalized_files = write_normalized_files(item, raw_dir)
    raw_metadata = {
        "input_id": input_id,
        "imported_at": imported_at,
        "source_path": item.relative_path,
        "source_is_directory": item.is_directory,
        "signature": item.signature,
        "title": title,
        "input_type": choose_input_type(item),
        "metadata": item.metadata,
        "files": copied_files,
        "normalized_files": normalized_files,
    }
    write_json(raw_dir / "metadata.json", raw_metadata)

    organized_dir.mkdir(parents=True, exist_ok=True)
    organized_path.write_text(render_organized(imported), encoding="utf-8")
    return imported


def collect_imported_items(organized_dir: Path) -> list[dict[str, str]]:
    items = []
    if not organized_dir.exists():
        return items
    for path in sorted(organized_dir.glob("*.md"), reverse=True):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "source: drive-inbox" not in text:
            continue
        title_match = re.search(r"^# 外部インプット - (.+)$", text, re.MULTILINE)
        type_match = re.search(r"^input_type:\s*(.+)$", text, re.MULTILINE)
        project_match = re.search(r"^related_project:\s*(.+)$", text, re.MULTILINE)
        todo_match = re.search(r"^todo_candidate:\s*(.+)$", text, re.MULTILINE)
        url_matches = URL_RE.findall(text)
        items.append(
            {
                "path": workspace_path(path),
                "title": title_match.group(1).strip() if title_match else path.stem,
                "input_type": type_match.group(1).strip() if type_match else "-",
                "related_project": project_match.group(1).strip().strip('"') if project_match else "",
                "todo_candidate": todo_match.group(1).strip() if todo_match else "false",
                "urls": "\n".join(dict.fromkeys(url_matches)),
            }
        )
    return items


def index_header(title: str, description: str) -> list[str]:
    return [
        "---",
        "source: import_drive_inbox.py",
        "type: input-index",
        "scope: external-drive-inbox",
        f"generated_at: {now_jst().isoformat(timespec='seconds')}",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
        "> 自動生成ファイル。必要な修正は元の organized input または importer に反映する。",
        "",
    ]


def rebuild_indexes(organized_dir: Path, index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    items = collect_imported_items(organized_dir)

    inputs_lines = index_header("External Inputs", "Google Drive 投入口から登録された外部インプット一覧。")
    for item in items:
        project = item["related_project"] or "-"
        inputs_lines.append(
            f"- {item['title']} | type:{item['input_type']} | project:{project} | source:`{item['path']}`"
        )
    (index_dir / "external-inputs.md").write_text("\n".join(inputs_lines) + "\n", encoding="utf-8")

    urls_lines = index_header("External URLs", "外部インプットに含まれるURL一覧。")
    for item in items:
        for url in item["urls"].splitlines():
            if url:
                urls_lines.append(f"- {url} | title:{item['title']} | source:`{item['path']}`")
    (index_dir / "external-urls.md").write_text("\n".join(urls_lines) + "\n", encoding="utf-8")

    files_lines = index_header("External Files", "外部インプットに含まれるファイル・資料の入口。")
    for item in items:
        files_lines.append(f"- {item['title']} | type:{item['input_type']} | source:`{item['path']}`")
    (index_dir / "external-files.md").write_text("\n".join(files_lines) + "\n", encoding="utf-8")

    todo_lines = index_header("External TODO Candidates", "外部インプット由来のTODO候補。日別TODOへ反映する前に確認する。")
    for item in items:
        if item["todo_candidate"].lower() == "true":
            todo_lines.append(f"- [ ] {item['title']} を確認する | source:`{item['path']}`")
    (index_dir / "external-todo-candidates.md").write_text("\n".join(todo_lines) + "\n", encoding="utf-8")


def run_import(args: argparse.Namespace) -> int:
    inbox_dir = args.inbox.resolve()
    raw_base_dir = args.raw_base.resolve()
    organized_dir = args.organized_dir.resolve()
    index_dir = args.index_dir.resolve()
    state_file = args.state_file.resolve()

    inbox_dir.mkdir(parents=True, exist_ok=True)
    state = read_json(state_file, {"imported": {}})
    imported_state = state.setdefault("imported", {})

    targets = iter_top_level_items(inbox_dir)
    imported_count = 0
    skipped_count = 0
    print(f"=== Importing Google Drive input box: {inbox_dir} ===")
    print(f"Found {len(targets)} top-level item(s)")

    for target in targets:
        item = build_import_item(target, inbox_dir)
        if not item:
            skipped_count += 1
            print(f"  Skipped empty or unsupported item: {target}")
            continue
        key = f"{item.relative_path}:{item.signature}"
        if key in imported_state and not args.force:
            skipped_count += 1
            print(f"  Already imported, skipping: {item.relative_path}")
            continue

        imported = import_item(item, raw_base_dir, organized_dir, dry_run=args.dry_run)
        imported_count += 1
        print(f"  Imported: {item.relative_path} -> {workspace_path(imported.organized_path)}")
        if not args.dry_run:
            imported_state[key] = {
                "input_id": imported.input_id,
                "organized_path": workspace_path(imported.organized_path),
                "imported_at": imported.imported_at,
                "source_path": item.relative_path,
                "signature": item.signature,
            }

    if not args.no_index and not args.dry_run:
        rebuild_indexes(organized_dir, index_dir)
        print(f"  Rebuilt external indexes in {index_dir}")

    if not args.dry_run:
        state["updated_at"] = now_jst().isoformat(timespec="seconds")
        write_json(state_file, state)

    print(f"=== Done! imported={imported_count} skipped={skipped_count} ===")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Google Drive input box files into 04_インプット/inputs")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX_DIR, help="Input box directory")
    parser.add_argument("--raw-base", type=Path, default=RAW_BASE_DIR, help="Raw intake output directory")
    parser.add_argument("--organized-dir", type=Path, default=ORGANIZED_DIR, help="Organized external output directory")
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR, help="Index output directory")
    parser.add_argument("--state-file", type=Path, default=STATE_FILE, help="Imported-state JSON path")
    parser.add_argument("--force", action="store_true", help="Import even if the same source signature was imported")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be imported without writing outputs")
    parser.add_argument("--no-index", action="store_true", help="Do not rebuild external indexes")
    args = parser.parse_args()
    try:
        raise SystemExit(run_import(args))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)


if __name__ == "__main__":
    main()
