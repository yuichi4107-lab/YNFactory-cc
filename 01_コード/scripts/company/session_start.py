#!/usr/bin/env python3
"""セッション開始時の同期。GitHub最新をDriveへ安全に取り込む。

`sync_drive_git.py pull-sync` は、pullで取得したパスのDrive側ファイルを**上書き**する。
Driveは全PCで即時共有されるため、別PCがDrive上で編集して未pushのままだと、
その作業がGitHubの古い内容で消える。このスクリプトは上書きの前に衝突を検出する。

やること:
  1. origin/main を fetch し、取り込むコミットがあるか調べる
  2. 無ければ何もしない（最新）
  3. あれば「pullで書き換わるパス」だけを Drive と照合する
     - Drive側が現在のHEADと同じ  -> 安全に上書きできる
     - Drive側が現在のHEADと違う  -> 未pushの編集がある = 衝突。pullせず一覧を出す
  4. 衝突が無ければ pull-sync を実行する

終了コード: 0=完了/最新, 2=衝突あり(pullしていない), 1=エラー
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_drive_git import detect_drive_root  # noqa: E402

HERE = Path(__file__).resolve().parent


def git(args: list[str], cwd: Path, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{(r.stderr or '').strip()}")
    return (r.stdout or "").strip()


def detect_local_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
    else:
        root = Path(git(["rev-parse", "--show-toplevel"], HERE)).resolve()
    if not (root / ".git").exists():
        raise SystemExit(f"ローカルGit作業ディレクトリが見つかりません: {root}")
    return root


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def blob_md5(root: Path, rev: str, rel: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return None
    return hashlib.md5(r.stdout).hexdigest()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--drive-root")
    ap.add_argument("--local-root")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--force", action="store_true",
                    help="衝突を検出してもpullする（Drive側の未push分は失われる）")
    args = ap.parse_args(argv)

    local = detect_local_root(args.local_root)
    drive = detect_drive_root(args.drive_root)
    print(f"local: {local}")
    print(f"drive: {drive}")

    git(["fetch", args.remote, args.branch], local)
    incoming = git(["rev-list", "--count", f"HEAD..{args.remote}/{args.branch}"], local)
    if incoming == "0":
        print("取り込むコミットなし。Driveは最新です。")
        return 0

    print(f"取り込むコミット: {incoming} 件")
    for line in git(["log", "--oneline", f"HEAD..{args.remote}/{args.branch}"], local).split("\n"):
        if line:
            print(f"  {line}")

    paths = [p for p in git(["diff", "--name-only", "HEAD",
                             f"{args.remote}/{args.branch}"], local).split("\n") if p]
    print(f"pullで書き換わるパス: {len(paths)} 件")

    conflicts = []
    for rel in paths:
        dp = drive / rel
        head = blob_md5(local, "HEAD", rel)
        if not dp.exists():
            continue                      # Driveに無い -> 新規取得。衝突しない
        if head is None:
            continue                      # HEADに無い -> 新規追加。衝突しない
        if md5(dp) != head:
            conflicts.append(rel)         # Drive側だけ変わっている = 未pushの編集

    if conflicts and not args.force:
        print("")
        print(f"!! 衝突 {len(conflicts)} 件。pullすると Drive側の未push分が失われます。")
        for rel in conflicts[:20]:
            print(f"   {rel}")
        if len(conflicts) > 20:
            print(f"   ... 他 {len(conflicts) - 20} 件")
        print("")
        print("対処: 先に該当パスを commit-push してから、もう一度実行する。")
        print("      内容を捨ててよい場合のみ --force を付ける。")
        return 2

    if conflicts:
        print(f"--force 指定のため、衝突 {len(conflicts)} 件を上書きします。")

    r = subprocess.run([sys.executable, str(HERE / "sync_drive_git.py"), "pull-sync",
                        "--remote", args.remote, "--branch", args.branch],
                       cwd=local, text=True, encoding="utf-8", errors="replace")
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
