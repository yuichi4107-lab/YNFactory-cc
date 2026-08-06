#!/usr/bin/env python3
"""Detect, block, and repair Google Drive related Git breakage for YNFactory-cc.

Google Drive syncs `.git` byte by byte, which leaves stale `*.lock` files,
zero-byte loose objects, and conflict copies inside the repository metadata.
This tool finds those states before Git reports them as fatal errors.

Usage:
    python3 git_drive_guard.py check           # 点検する
    python3 git_drive_guard.py check --deep    # git fsck --full まで実行する
    python3 git_drive_guard.py fix             # 安全に直せるものだけ隔離・修復する
    python3 git_drive_guard.py install-hooks   # pre-commit / pre-push ガードを入れる
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")

CRITICAL = "critical"
WARN = "warn"

SEVERITY_LABEL = {CRITICAL: "危険", WARN: "注意"}
SEVERITY_ORDER = {CRITICAL: 0, WARN: 1}

# Google Drive がマウントされる典型パス。ここに .git があると Git は必ず壊れる。
DRIVE_PATH_MARKERS = (
    "CloudStorage/GoogleDrive",
    "GoogleDrive-",
    "GoogleDriveFS",
    "マイドライブ",
    "My Drive",
    "Google Drive",
    "Dropbox",
    "OneDrive",
    "iCloud Drive",
    "Mobile Documents/com~apple~CloudDocs",
)

DRIVE_ROOT_CANDIDATES = [
    Path.home()
    / "Library"
    / "CloudStorage"
    / "GoogleDrive-yuichi4107@gmail.com"
    / "マイドライブ"
    / "YNFactory-cc",
    Path("G:/マイドライブ/YNFactory-cc"),
    Path("G:/My Drive/YNFactory-cc"),
]

# Drive / Dropbox が作る競合コピーと同期途中ファイル。
CONFLICT_NAME_PATTERNS = (
    re.compile(r"競合コピー"),
    re.compile(r"conflicted copy", re.IGNORECASE),
    re.compile(r"conflicted-copy", re.IGNORECASE),
    re.compile(r"\.tmp\.drive(download|upload)$", re.IGNORECASE),
    re.compile(r"\.driveupload$", re.IGNORECASE),
    re.compile(r"\.drivedownload$", re.IGNORECASE),
)

# `.git` 配下でだけ意味を持つ重複名（HEAD (1) / config (2) など）。
GIT_DIR_DUPLICATE_PATTERN = re.compile(r" \(\d+\)$")

# Drive が撒き散らすメタデータ。追跡されているとPC間で毎回差分になる。
DRIVE_NOISE_NAMES = frozenset(
    {"desktop.ini", "Thumbs.db", "ehthumbs.db", ".DS_Store", "Icon\r", "Icon\r\r"}
)
DRIVE_NOISE_SUFFIXES = (
    ".gdoc",
    ".gsheet",
    ".gslides",
    ".gdraw",
    ".gform",
    ".gjam",
    ".glink",
    ".gmap",
    ".gnote",
    ".gsite",
    ".gtable",
)

# `.git/*.lock` に見えるが Git のロックではないもの。
NON_GIT_LOCK_NAMES = frozenset({"daily-git-sync.lock"})

# 走査を打ち切るディレクトリ名。
PRUNED_DIR_NAMES = frozenset(
    {
        ".git",
        ".git_drivebackup",
        "_archive",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".venvs",
        ".next",
        ".turbo",
        ".cache",
        "dist",
        "build",
    }
)

MAX_REPORTED_PATHS = 40

REQUIRED_IGNORE_PATTERNS = (
    "*競合コピー*",
    "*conflicted copy*",
    "*.tmp.drivedownload",
    "*.tmp.driveupload",
    "desktop.ini",
    ".DS_Store",
)

HOOK_MARKER = "git_drive_guard"
HOOK_NAMES = ("pre-commit", "pre-push")
HOOK_TEMPLATE = """#!/bin/sh
# YNFactory {marker} hook - Google Drive 由来の Git 破損をコミット前に止める。
# 再インストール: python3 01_コード/scripts/company/git_drive_guard.py install-hooks
if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "git-drive-guard: python が見つからないためガードを実行できません" >&2
    exit 0
fi

ROOT=$(git rev-parse --show-toplevel) || exit 0
GUARD="$ROOT/01_コード/scripts/company/git_drive_guard.py"
[ -f "$GUARD" ] || exit 0

exec "$PY" "$GUARD" check --hook
"""


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    action: str
    paths: list[Path] = field(default_factory=list)
    details: list[str] = field(default_factory=list)
    fixable: bool = False


@dataclass
class Context:
    root: Path
    git_dir: Path
    lock_age: int
    deep: bool


class GuardError(RuntimeError):
    pass


def run_git(cwd: Path, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )


def detect_context(start: Path, lock_age: int, deep: bool) -> Context:
    result = run_git(start, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        raise GuardError(f"Gitリポジトリの外で実行されています: {start}")
    root = Path(result.stdout.strip()).resolve()

    result = run_git(root, ["rev-parse", "--git-dir"])
    if result.returncode != 0:
        raise GuardError("`git rev-parse --git-dir` が失敗しました。リポジトリが壊れている可能性があります。")
    git_dir = Path(result.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = (root / git_dir).resolve()

    return Context(root=root, git_dir=git_dir, lock_age=lock_age, deep=deep)


def matched_drive_marker(path: Path) -> str | None:
    text = str(path).replace("\\", "/")
    for marker in DRIVE_PATH_MARKERS:
        if marker in text:
            return marker
    return None


def is_conflict_name(name: str) -> bool:
    return any(pattern.search(name) for pattern in CONFLICT_NAME_PATTERNS)


def is_drive_noise_name(name: str) -> bool:
    if name in DRIVE_NOISE_NAMES:
        return True
    return name.endswith(DRIVE_NOISE_SUFFIXES)


def walk_repo_files(root: Path):
    """Yield repo files, pruning heavy and irrelevant directories."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in PRUNED_DIR_NAMES]
        current = Path(dirpath)
        for name in dirnames:
            yield current / name
        for name in filenames:
            yield current / name


def walk_git_dir_entries(git_dir: Path):
    for dirpath, dirnames, filenames in os.walk(git_dir):
        current = Path(dirpath)
        for name in dirnames:
            yield current / name
        for name in filenames:
            yield current / name


def file_age_seconds(path: Path) -> float:
    try:
        return max(0.0, dt.datetime.now().timestamp() - path.stat().st_mtime)
    except OSError:
        return 0.0


# ─── 個別チェック ──────────────────────────────────────────────


def check_worktree_location(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    for label, path in (("作業ツリー", ctx.root), (".git", ctx.git_dir)):
        marker = matched_drive_marker(path)
        if marker:
            findings.append(
                Finding(
                    check="worktree-location",
                    severity=CRITICAL,
                    message=f"{label} がクラウド同期フォルダ内にあります（一致: {marker}）",
                    action=(
                        "ここでは git を実行しない。ローカルGit側"
                        "（Mac: ~/YNFactory-cc / Windows: C:\\YNFactory-cc）へ移動してから操作する。"
                    ),
                    paths=[path],
                )
            )
    return findings


def check_drive_root_stray_git(ctx: Context) -> list[Finding]:
    env_value = os.environ.get("YNFACTORY_DRIVE_ROOT")
    candidates = [Path(env_value).expanduser()] if env_value else list(DRIVE_ROOT_CANDIDATES)

    findings: list[Finding] = []
    for candidate in candidates:
        try:
            if not candidate.exists():
                continue
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved == ctx.root:
            continue
        if (resolved / ".git").exists():
            findings.append(
                Finding(
                    check="drive-root-stray-git",
                    severity=CRITICAL,
                    message="Drive側 YNFactory-cc に .git があります（マルチPCルール §9 違反）",
                    action=(
                        "Drive側の .git は同期で必ず壊れる。中身を確認のうえ退避し、"
                        "Git操作はローカルGit側だけで行う。削除は実行直前に承認を取る。"
                    ),
                    paths=[resolved / ".git"],
                )
            )
    return findings


def check_stale_locks(ctx: Context) -> list[Finding]:
    stale: list[Path] = []
    fresh: list[Path] = []
    for path in ctx.git_dir.rglob("*.lock"):
        if path.name in NON_GIT_LOCK_NAMES or not path.is_file():
            continue
        if file_age_seconds(path) >= ctx.lock_age:
            stale.append(path)
        else:
            fresh.append(path)

    findings: list[Finding] = []
    if stale:
        findings.append(
            Finding(
                check="stale-locks",
                severity=CRITICAL,
                message=f"{ctx.lock_age}秒以上放置された Git ロックが {len(stale)} 件あります",
                action=(
                    "`fatal: Unable to create '...index.lock': File exists` の直接原因。"
                    "他PC・他プロセスで git が動いていないことを確認して `fix` を実行する。"
                ),
                paths=stale,
                fixable=True,
            )
        )
    if fresh:
        findings.append(
            Finding(
                check="active-locks",
                severity=WARN,
                message=f"作成直後の Git ロックが {len(fresh)} 件あります",
                action="別の git プロセスが実行中の可能性がある。終了を待ってから操作する。",
                paths=fresh,
            )
        )
    return findings


def check_git_dir_conflict_copies(ctx: Context) -> list[Finding]:
    hits = [
        path
        for path in walk_git_dir_entries(ctx.git_dir)
        if is_conflict_name(path.name)
        or GIT_DIR_DUPLICATE_PATTERN.search(path.stem)
        or is_drive_noise_name(path.name)
    ]
    if not hits:
        return []
    return [
        Finding(
            check="gitdir-conflict-copies",
            severity=CRITICAL,
            message=f".git の中に同期ゴミ・競合コピーが {len(hits)} 件あります",
            action="Git が参照を誤読して `bad object` や `broken link` を出す。`fix` で隔離する。",
            paths=hits,
            fixable=True,
        )
    ]


def check_worktree_conflict_copies(ctx: Context) -> list[Finding]:
    hits = [path for path in walk_repo_files(ctx.root) if is_conflict_name(path.name)]
    if not hits:
        return []
    return [
        Finding(
            check="worktree-conflict-copies",
            severity=WARN,
            message=f"作業ツリーに Drive 競合コピーが {len(hits)} 件あります",
            action=(
                "中身が本体と違う場合があるため自動削除しない。"
                "本体へ内容を統合してから、承認のうえ削除する（マルチPCルール §6）。"
            ),
            paths=hits,
        )
    ]


def check_empty_git_files(ctx: Context) -> list[Finding]:
    """Zero-byte metadata is the classic signature of a Drive-truncated .git."""
    targets: list[Path] = []

    objects_dir = ctx.git_dir / "objects"
    if objects_dir.is_dir():
        for dirpath, dirnames, filenames in os.walk(objects_dir):
            dirnames[:] = [name for name in dirnames if name != "info"]
            current = Path(dirpath)
            targets.extend(current / name for name in filenames)

    refs_dir = ctx.git_dir / "refs"
    if refs_dir.is_dir():
        targets.extend(path for path in refs_dir.rglob("*") if path.is_file())

    for name in ("HEAD", "index", "packed-refs", "config"):
        candidate = ctx.git_dir / name
        if candidate.is_file():
            targets.append(candidate)

    empty: list[Path] = []
    for path in targets:
        try:
            if path.stat().st_size == 0:
                empty.append(path)
        except OSError:
            continue

    if not empty:
        return []
    return [
        Finding(
            check="empty-git-files",
            severity=CRITICAL,
            message=f".git 内に0バイトのファイルが {len(empty)} 件あります",
            action=(
                "Drive がファイル実体を同期しきれていない典型症状"
                "（`object file ... is empty` / `index file corrupt`）。"
                "自動修復せず docs/git-drive-safety.md の復旧手順に従う。"
            ),
            paths=empty,
        )
    ]


def check_fsck(ctx: Context) -> list[Finding]:
    args = ["fsck", "--no-progress"]
    args.append("--full" if ctx.deep else "--connectivity-only")
    try:
        result = run_git(ctx.root, args, timeout=900)
    except subprocess.TimeoutExpired:
        return [
            Finding(
                check="fsck",
                severity=WARN,
                message="git fsck がタイムアウトしました",
                action="リポジトリが大きい可能性がある。時間のあるときに `git fsck --full` を手動実行する。",
            )
        ]

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    broken = [
        line
        for line in lines
        if re.search(r"\b(error|fatal|missing|corrupt|broken link)\b", line, re.IGNORECASE)
    ]
    if result.returncode != 0 or broken:
        return [
            Finding(
                check="fsck",
                severity=CRITICAL,
                message="git fsck がリポジトリ破損を報告しました",
                action="docs/git-drive-safety.md の復旧手順（クローンし直し / .git_drivebackup から復元）を実行する。",
                details=(broken or lines)[:MAX_REPORTED_PATHS],
            )
        ]
    return []


def check_tracked_drive_noise(ctx: Context) -> list[Finding]:
    result = run_git(ctx.root, ["ls-files", "-z"])
    if result.returncode != 0:
        return []
    hits = [
        Path(item)
        for item in result.stdout.split("\0")
        if item and (is_drive_noise_name(Path(item).name) or is_conflict_name(Path(item).name))
    ]
    if not hits:
        return []
    return [
        Finding(
            check="tracked-drive-noise",
            severity=WARN,
            message=f"Drive のゴミファイルが {len(hits)} 件 Git 管理下にあります",
            action="`git rm --cached <path>` で外す。大規模な削除は実行直前に承認を取る（マルチPCルール §8）。",
            paths=hits,
        )
    ]


def check_gitignore(ctx: Context) -> list[Finding]:
    ignore_path = ctx.root / ".gitignore"
    if not ignore_path.is_file():
        return [
            Finding(
                check="gitignore",
                severity=WARN,
                message=".gitignore がありません",
                action="Drive のゴミが取り込まれる。.gitignore を作成する。",
            )
        ]
    lines = {line.strip() for line in ignore_path.read_text(encoding="utf-8").splitlines()}
    missing = [pattern for pattern in REQUIRED_IGNORE_PATTERNS if pattern not in lines]
    if not missing:
        return []
    return [
        Finding(
            check="gitignore",
            severity=WARN,
            message=f"Drive 対策の .gitignore パターンが {len(missing)} 件不足しています",
            action="不足パターンを .gitignore に追記する。",
            details=missing,
        )
    ]


def check_hooks(ctx: Context) -> list[Finding]:
    missing: list[Path] = []
    for name in HOOK_NAMES:
        hook = ctx.git_dir / "hooks" / name
        if not hook.is_file():
            missing.append(hook)
            continue
        try:
            if HOOK_MARKER not in hook.read_text(encoding="utf-8", errors="replace"):
                missing.append(hook)
        except OSError:
            missing.append(hook)
    if not missing:
        return []
    return [
        Finding(
            check="hooks",
            severity=WARN,
            message="このPCにガードフックが入っていません",
            action="`python3 01_コード/scripts/company/git_drive_guard.py install-hooks` を1回実行する。",
            paths=missing,
        )
    ]


BLOCKING_CHECKS = (
    check_worktree_location,
    check_stale_locks,
    check_git_dir_conflict_copies,
    check_empty_git_files,
)

FULL_CHECKS = (
    check_worktree_location,
    check_drive_root_stray_git,
    check_stale_locks,
    check_git_dir_conflict_copies,
    check_worktree_conflict_copies,
    check_empty_git_files,
    check_tracked_drive_noise,
    check_gitignore,
    check_hooks,
    check_fsck,
)


def collect(ctx: Context, checks) -> list[Finding]:
    findings: list[Finding] = []
    for check in checks:
        findings.extend(check(ctx))
    findings.sort(key=lambda finding: SEVERITY_ORDER[finding.severity])
    return findings


# ─── 出力 ────────────────────────────────────────────────────


def print_findings(ctx: Context, findings: list[Finding], *, quiet_when_clean: bool) -> None:
    if not findings:
        if not quiet_when_clean:
            print("git-drive-guard: 問題は見つかりませんでした。")
            print(f"  作業ツリー: {ctx.root}")
            print(f"  .git:       {ctx.git_dir}")
        return

    print("git-drive-guard: 点検結果")
    print(f"  作業ツリー: {ctx.root}")
    print(f"  .git:       {ctx.git_dir}")
    print()
    for finding in findings:
        print(f"[{SEVERITY_LABEL[finding.severity]}] {finding.check}: {finding.message}")
        print(f"  対処: {finding.action}")
        for path in finding.paths[:MAX_REPORTED_PATHS]:
            print(f"    - {path}")
        if len(finding.paths) > MAX_REPORTED_PATHS:
            print(f"    ... 他 {len(finding.paths) - MAX_REPORTED_PATHS} 件")
        for line in finding.details:
            print(f"    | {line}")
        print()


def worst_severity(findings: list[Finding]) -> str | None:
    if any(finding.severity == CRITICAL for finding in findings):
        return CRITICAL
    if findings:
        return WARN
    return None


# ─── 修復 ────────────────────────────────────────────────────


def quarantine_root(ctx: Context) -> Path:
    stamp = dt.datetime.now(JST).strftime("%Y%m%d-%H%M%S")
    return ctx.root / "_archive" / "git-drive-quarantine" / stamp


def quarantine(ctx: Context, paths: list[Path], destination: Path, dry_run: bool) -> list[Path]:
    moved: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        try:
            relative = path.relative_to(ctx.root)
        except ValueError:
            relative = Path(path.name)
        target = destination / relative
        print(f"隔離: {path} -> {target}")
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(target))
        moved.append(path)
    return moved


def command_fix(ctx: Context, dry_run: bool) -> int:
    findings = collect(ctx, FULL_CHECKS)
    fixable = [finding for finding in findings if finding.fixable]

    if not fixable:
        print_findings(ctx, findings, quiet_when_clean=False)
        print("自動修復できる項目はありません。")
        return 1 if worst_severity(findings) == CRITICAL else 0

    location_blocked = [f for f in findings if f.check == "worktree-location"]
    if location_blocked:
        print_findings(ctx, findings, quiet_when_clean=False)
        print("クラウド同期フォルダ内では修復しません。ローカルGit側で実行してください。")
        return 1

    print("修復前に、他のPC・ターミナル・エディタで git が動いていないことを確認してください。")
    print()
    destination = quarantine_root(ctx)
    for finding in fixable:
        print(f"対象: {finding.check} ({len(finding.paths)} 件)")
        quarantine(ctx, finding.paths, destination, dry_run)
        print()

    if dry_run:
        print("dry-run: 実際には移動していません。")
        return 0

    print(f"隔離先: {destination}")
    print("（削除はしていません。問題が解決したことを確認してから、承認のうえ削除してください）")
    print()
    print("再点検:")
    remaining = collect(ctx, FULL_CHECKS)
    print_findings(ctx, remaining, quiet_when_clean=False)
    return 1 if worst_severity(remaining) == CRITICAL else 0


def command_install_hooks(ctx: Context) -> int:
    hooks_dir = ctx.git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    body = HOOK_TEMPLATE.format(marker=HOOK_MARKER)

    for name in HOOK_NAMES:
        hook = hooks_dir / name
        if hook.exists():
            existing = hook.read_text(encoding="utf-8", errors="replace")
            if HOOK_MARKER in existing:
                print(f"更新: {hook}")
            else:
                backup = hook.with_suffix(hook.suffix + ".bak")
                shutil.copy2(hook, backup)
                print(f"既存フックを退避: {backup}")
        else:
            print(f"作成: {hook}")
        hook.write_text(body, encoding="utf-8")
        hook.chmod(0o755)

    print()
    print("インストール完了。フックは .git/hooks 配下のためPCごとに1回実行が必要です。")
    return 0


def command_check(ctx: Context, hook_mode: bool) -> int:
    checks = BLOCKING_CHECKS if hook_mode else FULL_CHECKS
    findings = collect(ctx, checks)
    print_findings(ctx, findings, quiet_when_clean=hook_mode)

    if worst_severity(findings) != CRITICAL:
        return 0

    if hook_mode:
        print("git-drive-guard: Google Drive 由来の破損を検出したため操作を中止しました。")
        print("  復旧: python3 01_コード/scripts/company/git_drive_guard.py fix")
        print("  詳細: 02_設定/docs/git-drive-safety.md")
        print("  どうしても続行する場合のみ --no-verify を付けてください。")
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Drive 由来の Git 破損を検出・防止・修復する。"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="check",
        choices=["check", "fix", "install-hooks"],
        help="check: 点検 / fix: 安全に直せるものを隔離 / install-hooks: ガードフック導入",
    )
    parser.add_argument("--root", help="対象リポジトリ。既定はカレントの Git ルート。")
    parser.add_argument(
        "--lock-age",
        type=int,
        default=600,
        help="この秒数以上古い *.lock を残留ロックとみなす（既定: 600）。",
    )
    parser.add_argument("--deep", action="store_true", help="git fsck --full まで実行する。")
    parser.add_argument("--hook", action="store_true", help="フック用。ブロック対象のみ点検する。")
    parser.add_argument("--dry-run", action="store_true", help="fix で実際には移動しない。")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    start = Path(args.root).expanduser().resolve() if args.root else Path.cwd()

    try:
        ctx = detect_context(start, lock_age=args.lock_age, deep=args.deep)
    except GuardError as exc:
        print(f"git-drive-guard: {exc}", file=sys.stderr)
        return 1

    if args.command == "install-hooks":
        return command_install_hooks(ctx)
    if args.command == "fix":
        return command_fix(ctx, dry_run=args.dry_run)
    return command_check(ctx, hook_mode=args.hook)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
