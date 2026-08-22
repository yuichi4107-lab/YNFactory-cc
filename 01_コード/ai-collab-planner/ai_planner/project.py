from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .domain import ProjectState


WORKFLOW_DIR = ".ai-workflow"
REQUEST_DIR = "00_依頼"
PLAN_DIR = "01_計画"
RESEARCH_DIR = "02_調査"
OUTPUT_DIR = "03_成果物"
TEST_DIR = "04_テスト"
REVIEW_DIR = "05_レビュー"
RUNS_DIR = "90_実行履歴"
LEGACY_IGNORED_NAMES = {"desktop.ini", "thumbs.db", ".ds_store", "active.lock"}


def inspect_project(root: Path) -> ProjectState:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"フォルダが存在しません: {root}")

    git_root = find_git_root(root)
    is_git = git_root is not None
    branch = "Git未設定"
    dirty: tuple[str, ...] = ()
    if is_git:
        branch_result = _git(root, "branch", "--show-current")
        branch = branch_result.stdout.strip() or "detached HEAD"
        status_result = _git(root, "status", "--porcelain", "--", ".")
        dirty = tuple(line for line in status_result.stdout.splitlines() if line.strip())

    return ProjectState(
        root=root,
        is_git=is_git,
        git_root=git_root,
        branch=branch,
        dirty_files=dirty,
    )


def find_git_root(root: Path) -> Path | None:
    result = _git(root, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    return Path(raw).resolve() if raw else None


def capture_git_snapshot(root: Path) -> str:
    """対象サブプロジェクトに限定したGit差分資料を作る。"""
    if find_git_root(root) is None:
        return "Git未設定のため差分情報はありません。"

    status = _git(root, "status", "--short", "--", ".").stdout
    unstaged = _git(
        root,
        "diff",
        "--no-ext-diff",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        "--",
        ".",
    ).stdout
    staged = _git(
        root,
        "diff",
        "--cached",
        "--no-ext-diff",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        "--",
        ".",
    ).stdout
    return (
        "# Git作業状態\n\n"
        "対象は、この名前付きプロジェクト内の変更だけです。\n\n"
        "## 変更ファイル\n\n```text\n"
        f"{status.rstrip()}\n```\n\n"
        "## 未ステージ差分\n\n```diff\n"
        f"{unstaged.rstrip()}\n```\n\n"
        "## ステージ済み差分\n\n```diff\n"
        f"{staged.rstrip()}\n```"
    )


def initialize_project_files(root: Path) -> None:
    workflow = root / WORKFLOW_DIR
    for directory in (
        root / REQUEST_DIR,
        root / PLAN_DIR,
        root / RUNS_DIR,
        workflow,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    _write_if_missing(
        root / "AGENTS.md",
        """# Codexへのプロジェクト指示

作業前に `.ai-workflow/AI_WORKFLOW.md`、`00_依頼/GOAL.md`、`01_計画/REQUIREMENTS.md`、`.ai-workflow/STATUS.md` を読むこと。

- AI共同開発プランナーからは実装を行わず、要件定義と実装プランの作成だけを行う。
- 将来、別途実装を依頼された場合も、承認済みの `01_計画/REQUIREMENTS.md` の範囲外を勝手に変更しない。
- この名前付きプロジェクトの外側を変更しない。
- 実装後は利用可能なテスト、型チェック、ビルドを行う。
- Git push、デプロイ、課金操作、秘密情報の変更は行わない。
- データ削除、依存パッケージ追加、大規模な仕様変更は人間の確認を求める。
- レビュー時は重大な問題から報告し、根拠となるファイルを示す。
""",
    )
    _write_if_missing(
        root / "CLAUDE.md",
        """# Claudeへのプロジェクト指示

作業前に `.ai-workflow/AI_WORKFLOW.md`、`00_依頼/GOAL.md`、`01_計画/REQUIREMENTS.md`、`.ai-workflow/STATUS.md` を読むこと。

- 要件定義とレビューでは既存ファイルを変更しない。
- レビューは重大・中程度・軽微に分類し、誤検知の可能性も明示する。
- この名前付きプロジェクトの外側を変更しない。
- Git push、デプロイ、課金操作、秘密情報の変更は行わない。
- コード変更は、オーケストレーターから実装担当として明示された場合に限る。
""",
    )
    _write_if_missing(
        workflow / "AI_WORKFLOW.md",
        """# AI共同開発ルール

1. 作業開始時に、要件定義に使うモデルを決め、人間が変更できる状態にする。
2. このツールは要件定義書と実装プランの作成までとし、コード実装は行わない。
3. 要件定義とレビューは読み取り専用で行う。
4. 統合した要件定義書は、別のAIによる最終チェック後に完成版として保存する。
4.1 複数案を作る目的は優劣を決めることではなく、両案の良いところを1つへ統合することとする。
4.2 見かけ上の対立は統合し、本当に両立しないトレードオフだけを人間の判断へ回す。
5. 実装プランには、工程別にClaude系かGPT系か、具体的モデル、理由、代替候補を記載する。
6. 実装担当と第三者レビュー担当は、原則として異なる会社のモデルを提案する。
7. テスト結果をAIの意見より優先する方針を実装プランへ含める。
8. 公開、Git push、デプロイ、課金、秘密情報、重大な削除は人間の承認事項とする。
9. 合意できない内容や情報不足は未決事項として残し、推測で決めない。
10. 要件定義書が空、エラー文、必要見出し不足の場合は成果物として確定しない。
""",
    )
    _write_if_missing(root / REQUEST_DIR / "GOAL.md", "# 目的\n\n未設定\n")
    _write_if_missing(root / PLAN_DIR / "REQUIREMENTS.md", "# 要件定義書・実装プラン\n\n未作成\n")
    _write_if_missing(root / PLAN_DIR / "PLAN.md", "# 要件定義書・実装プラン\n\n未作成\n")
    _write_if_missing(workflow / "DECISIONS.md", "# 判断記録\n")
    _write_if_missing(workflow / "STATUS.md", "# 現在の状態\n\n未着手\n")


def suggest_project_name(goal: str) -> str:
    first_line = next((line.strip() for line in goal.splitlines() if line.strip()), "新規プロジェクト")
    name = re.sub(r"^(今回|新しく|えっと)[、,\s]*", "", first_line, flags=re.IGNORECASE)
    endings = (
        "をお願いします",
        "してください",
        "してほしいです",
        "してほしい",
        "を作りたいです",
        "を作りたい",
        "したいです",
        "したい",
    )
    for ending in endings:
        if name.endswith(ending):
            name = name[: -len(ending)]
            break
    name = re.sub(r"(?<=[A-Za-z0-9])(?:と|で)(?=[A-Za-z0-9])", "-", name)
    name = name.replace("を収益化", "収益化").replace("で収益化", "収益化")
    name = name.replace("×", "-").replace("／", "-").replace("/", "-")
    suggested = sanitize_project_name(name)
    if len(suggested) > 36:
        compact = _compact_project_name(goal)
        if compact:
            return sanitize_project_name(compact)
    return suggested


def sanitize_project_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name.strip())
    cleaned = re.sub(r"[\s_-]+", "-", cleaned).strip(" .-")
    if not cleaned:
        cleaned = "新規プロジェクト"
    if len(cleaned) > 60:
        cleaned = cleaned[:60].rstrip(" .-")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if cleaned.upper() in reserved:
        cleaned = f"{cleaned}-プロジェクト"
    return cleaned


def create_run_directory(root: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = root / RUNS_DIR / stamp
    suffix = 1
    while candidate.exists():
        candidate = root / RUNS_DIR / f"{stamp}-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def copy_legacy_workflow(workspace_root: Path, project_root: Path) -> tuple[Path, Path] | None:
    """旧ルート直下の記録を検証付きで新プロジェクトへコピーする。"""
    source = workspace_root / WORKFLOW_DIR
    if not source.is_dir() or source.resolve() == (project_root / WORKFLOW_DIR).resolve():
        return None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = project_root / RUNS_DIR / f"旧形式-{stamp}"
    shutil.copytree(
        source,
        destination,
        ignore=_ignore_legacy_system_files,
        copy_function=_copy_file_resilient,
    )
    if _directory_digest(source) != _directory_digest(destination):
        raise RuntimeError("旧実行記録のコピー検証に失敗しました。元ファイルは変更していません。")
    return source, destination


def archive_legacy_source(source: Path) -> Path:
    """コピー済みの旧フォルダを削除せず、復元できる名前へ変更する。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = source.with_name(f"{source.name}.migrated-{stamp}")
    suffix = 1
    while candidate.exists():
        candidate = source.with_name(f"{source.name}.migrated-{stamp}-{suffix}")
        suffix += 1
    source.rename(candidate)
    return candidate


def goal_path(root: Path) -> Path:
    return root / REQUEST_DIR / "GOAL.md"


def plan_path(root: Path) -> Path:
    return root / PLAN_DIR / "PLAN.md"


def requirements_path(root: Path) -> Path:
    return root / PLAN_DIR / "REQUIREMENTS.md"


def status_path(root: Path) -> Path:
    return root / WORKFLOW_DIR / "STATUS.md"


def model_selection_path(root: Path) -> Path:
    return root / PLAN_DIR / "MODEL_SELECTION.md"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def append_decision(root: Path, title: str, content: str) -> None:
    path = root / WORKFLOW_DIR / "DECISIONS.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as file:
        file.write(f"\n## {timestamp} {title}\n\n{content.rstrip()}\n")


@contextmanager
def project_lock(root: Path):
    lock_path = root / WORKFLOW_DIR / "active.lock"
    if lock_path.exists():
        raise RuntimeError(
            "このプロジェクトでは別のAIプランナーが動作中です。"
            "実際に動いていない場合だけ .ai-workflow/active.lock を削除してください。"
        )
    payload = {"pid": os.getpid(), "started_at": datetime.now().isoformat(timespec="seconds")}
    lock_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(["git", *args], 127, "", "Gitが見つかりません。")


def _directory_digest(root: Path) -> str:
    digest = hashlib.sha256()
    paths: list[Path] = []
    for item in root.rglob("*"):
        if item.name.casefold() in LEGACY_IGNORED_NAMES:
            continue
        try:
            if item.is_file():
                paths.append(item)
        except OSError:
            continue
    for path in sorted(paths):
        try:
            content = path.read_bytes()
        except FileNotFoundError:
            # Google Drive等では、一覧取得と読み込みの間にプレースホルダーが
            # 消えることがある。元データは触らず、この一時項目だけ除外する。
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(content)
    return digest.hexdigest()


def _ignore_legacy_system_files(_directory: str, names: list[str]) -> set[str]:
    """移行対象に不要なOS管理ファイルと実行中ロックを除外する。"""
    return {name for name in names if name.casefold() in LEGACY_IGNORED_NAMES}


def _copy_file_resilient(source: str, destination: str) -> str:
    """クラウド同期中に消えた一時ファイルだけを安全に読み飛ばす。"""
    try:
        return shutil.copy2(source, destination)
    except FileNotFoundError:
        return destination


def _compact_project_name(goal: str) -> str:
    """長い依頼文から、フォルダー向けの短い名前を組み立てる。"""
    labels: list[str] = []
    if re.search(r"AIを使ったことがない|AI初心者|AI未経験", goal, re.IGNORECASE):
        labels.append("AI初心者向け")
    elif re.search(r"AI", goal, re.IGNORECASE):
        labels.append("AI")

    patterns = (
        (r"業務効率(?:化)?", "業務効率化"),
        (r"提案", "提案"),
        (r"アンケート", "アンケート"),
        (r"(?:web|ウェブ)\s*アプリ", "Webアプリ"),
        (r"LINE\s*スタンプ", "LINEスタンプ"),
        (r"収益化", "収益化"),
        (r"ホームページ|(?:web|ウェブ)\s*サイト", "Webサイト"),
        (r"ダッシュボード", "ダッシュボード"),
        (r"自動化", "自動化"),
    )
    for pattern, label in patterns:
        if re.search(pattern, goal, re.IGNORECASE) and label not in labels:
            labels.append(label)
    return "".join(labels)


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)
