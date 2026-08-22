from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from .clients import CliModelRunner, DemoModelRunner
from .config import AppSettings, load_settings
from .domain import ModelTeam, RoutingDecision
from .project import (
    archive_legacy_source,
    copy_legacy_workflow,
    goal_path,
    initialize_project_files,
    inspect_project,
    model_selection_path,
    project_lock,
    requirements_path,
    sanitize_project_name,
    suggest_project_name,
    write_text,
)
from .router import decide_level
from .voice import WindowsVoiceIO, parse_yes_no
from .workflow import CollaborationWorkflow, classify_forks_document


APP_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ClaudeとCodexによる要件定義・実装プラン作成ツール")
    parser.add_argument("--check", action="store_true", help="インストール状況だけを確認")
    parser.add_argument("--demo", action="store_true", help="実際のAIを呼ばずに一連の動作を確認")
    parser.add_argument("--voice", action="store_true", help="Windowsの音声入力と読み上げを使用")
    parser.add_argument("--whisper-model", help="音声認識モデルを一時的に変更（例: medium）")
    parser.add_argument("--project", type=Path, help="YNFactory-cc等の作業ディレクトリを直接指定")
    parser.add_argument("--goal", help="依頼文。渡すと自動起動モードになる（人の入力を求めない）")
    parser.add_argument("--name", help="プロジェクト名。省略時は依頼文から自動提案")
    parser.add_argument(
        "--level",
        choices=["light", "standard", "complex", "critical"],
        help="作業レベル。省略時は依頼文のキーワードで判定",
    )
    parser.add_argument("--resume", type=Path, help="承認待ちで停止した実行記録から再開する")
    parser.add_argument("--json", action="store_true", help="結果をJSONで出力")
    parser.add_argument(
        "--print-project-path", action="store_true",
        help="プロジェクトの保存先を出力して終了する（AIを呼ばない）",
    )
    args = parser.parse_args(argv)
    if getattr(args, "json", False) and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    settings = load_settings(APP_ROOT / "config.toml")
    if args.check:
        return run_check(settings)

    if args.goal or args.resume:
        return run_headless(args, settings)

    voice = create_voice_io(settings, args.whisper_model) if args.voice else None
    if voice is not None and not voice.available():
        print(f"音声機能を開始できません: {voice.last_error}")
        print("今回はキーボード入力で続けます。")
        voice = None

    print_header(voice_enabled=voice is not None)
    if args.project:
        workspace_root = args.project.resolve()
    elif settings.default_workspace and Path(settings.default_workspace).is_dir():
        workspace_root = Path(settings.default_workspace).resolve()
        print(f"既定の親フォルダを使用します: {workspace_root}")
    else:
        workspace_root = choose_project_directory()
    if workspace_root is None:
        print("終了しました。")
        return 0

    try:
        state = inspect_project(workspace_root)
        show_project_state(state)
        if state.dirty_files:
            print("\n既存の変更は消しませんが、AIの変更と混ざる可能性があります。")
            if not ask_yes_no("現在の変更を維持したまま続けますか？", voice):
                print("先にGitHub Desktopなどで変更を保存してから、もう一度起動してください。")
                return 0

        goal = read_goal(voice)
        if not goal.strip():
            print("目的が入力されなかったため終了します。")
            return 1

        project_root = choose_named_project(workspace_root, settings.projects_directory, goal, voice)
        if project_root is None:
            print("終了しました。")
            return 0
        initialize_project_files(project_root)
        print(f"\n保存先: {project_root}")

        legacy = workspace_root / ".ai-workflow"
        if legacy.is_dir() and ask_yes_no("ルート直下にある旧実行記録を、このプロジェクトへ安全に移行しますか？", voice):
            try:
                migration = copy_legacy_workflow(workspace_root, project_root)
            except Exception as exc:
                print("\n旧実行記録の移行に失敗しました。元の記録は変更していません。")
                print(f"詳細: {exc}")
                if not ask_yes_no("旧記録の移行を飛ばして、今回の要件定義を続けますか？", voice):
                    print("安全のため停止しました。旧記録はそのまま残っています。")
                    return 1
                migration = None
            if migration:
                source, destination = migration
                print(f"旧実行記録をコピーし、内容を検証しました: {destination}")
                if ask_yes_no("元の .ai-workflow を削除せず、移行済みの名前へ変更しますか？", voice):
                    archived = archive_legacy_source(source)
                    print(f"元の記録は復元可能な名前で残しました: {archived}")

        decision = decide_level(goal, settings)
        team = select_team(decision, settings, voice)
        show_team(decision, team)

        if not ask_yes_no("このモデル構成で要件定義を開始しますか？", voice):
            print("開始しませんでした。")
            return 0

        write_text(model_selection_path(project_root), model_selection_markdown(decision, team))

        runner = DemoModelRunner() if args.demo else CliModelRunner(settings)
        if not args.demo:
            missing = sorted(
                {
                    role.provider
                    for role in _planning_roles(team)
                    if role.enabled and not runner.available(role.provider)
                }
            )
            if missing:
                print("\n必要なCLIが見つかりません: " + ", ".join(missing))
                print("先に『AIプランナー確認.bat』でセットアップ状況を確認してください。")
                return 2
            auth_failures: list[tuple[str, str]] = []
            for provider in sorted({role.provider for role in _planning_roles(team) if role.enabled}):
                ok, detail = runner.auth_status(provider)
                print(f"{provider}認証: {'OK' if ok else '未ログイン'} - {detail}")
                if not ok:
                    auth_failures.append((provider, detail))
            if auth_failures:
                print("\n認証が完了していないため、AIを呼び出す前に停止しました。")
                print("Codex: `codex login`    Claude: `claude auth login`")
                return 2

        progress = make_progress(voice)
        approve = make_approve(voice)
        with project_lock(project_root):
            workflow = CollaborationWorkflow(runner, progress=progress, approve=approve)
            outcome = workflow.execute(
                root=project_root,
                goal=goal,
                team=team,
            )

        if not outcome.completed:
            print("\n================================")
            print("承認されなかったため、要件定義を行わずに終了しました。")
            print(f"分岐点と立場の記録: {outcome.run_dir}")
            print("要件定義書は変更していません。")
            print("================================")
            if voice is not None:
                voice.speak("承認されなかったため、要件定義を行わずに終了しました。")
            return 0

        print("\n================================")
        print("処理が終了しました。")
        print(f"プロジェクト: {project_root}")
        print(f"記録: {outcome.run_dir}")
        if outcome.rounds_used:
            print(f"議論ラウンド: {outcome.rounds_used}回（終了理由: {outcome.stop_reason}）")
            print(f"争点: {len(outcome.issue_ids)}件")
            print("『要判断』として残った争点は要件定義書の12章と14章で確認してください。")
        else:
            print("議論: 行っていません（分岐点なし、または軽作業レベル）")
        print(f"要件定義書・実装プラン: {requirements_path(project_root)}")
        print("コード実装は行っていません。")
        print("================================")
        if voice is not None:
            voice.speak("要件定義書と実装プランの作成が終了しました。画面で結果を確認してください。")
        return 0
    except KeyboardInterrupt:
        print("\n中断しました。")
        return 130
    except Exception as exc:  # ユーザー向けCLIなので最上位で読みやすく表示する
        print(f"\nエラー: {exc}")
        if voice is not None:
            voice.speak("エラーで停止しました。画面の内容を確認してください。")
        return 1


def run_check(settings: AppSettings) -> int:
    print_header(voice_enabled=False)
    print("動作環境を確認します。\n")
    voice = create_voice_io(settings)
    voice_ok = voice.available()
    runner = CliModelRunner(settings)
    codex_found = shutil.which(settings.codex_command) is not None
    claude_found = shutil.which(settings.claude_command) is not None
    codex_auth, codex_detail = runner.auth_status("codex") if codex_found else (False, "CLI未検出")
    claude_auth, claude_detail = runner.auth_status("claude") if claude_found else (False, "CLI未検出")
    checks = [
        ("Python 3.11以上", sys.version_info >= (3, 11), sys.version.split()[0]),
        ("Git", shutil.which("git") is not None, shutil.which("git") or "未検出"),
        ("Codex CLI", codex_found, shutil.which(settings.codex_command) or "未検出"),
        ("Codexログイン", codex_auth, codex_detail),
        ("Claude Code CLI", claude_found, shutil.which(settings.claude_command) or "未検出"),
        ("Claudeログイン", claude_auth, claude_detail),
        ("日本語音声入力（任意）", voice_ok, voice.status_detail if voice_ok else voice.last_error),
    ]
    for name, ok, detail in checks:
        mark = "OK" if ok else "未設定"
        print(f"[{mark}] {name}: {detail}")

    required_ok = all(checks[index][1] for index in range(6))
    print("\n音声入力以外がすべてOKなら『AIプランナー起動.bat』を使用できます。")
    print("音声入力は任意です。未設定でもキーボード版は動作します。")
    print("CLIを使わず試す場合は `python main.py --demo` を実行してください。")
    return 0 if required_ok else 2


HEADLESS_NEEDS_APPROVAL = 10


class _HeadlessApprover:
    """自動起動モードの承認。原則True、例外のみFalse。

    議論そのものはAI同士で行われる。ここが判定するのは
    「その議論を始めてよい状態か」だけ。
    """

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.pending_reason: str | None = None

    def __call__(self, document: str) -> bool:
        if self.auto_approve:
            return True
        verdict = classify_forks_document(document)
        if verdict == "ok":
            return True
        self.pending_reason = verdict
        return False


def _team_summary(team: ModelTeam) -> dict:
    return {
        "fork_extractor": display_role(team.fork_extractor),
        "fork_auditor": display_role(team.fork_auditor),
        "primary_planner": display_role(team.primary_planner),
        "secondary_planner": display_role(team.secondary_planner),
        "plan_reviewer": display_role(team.plan_reviewer),
        "final_decider": display_role(team.final_decider),
        "requirements_final_checker": display_role(team.requirements_final_checker),
    }


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def run_headless(args: argparse.Namespace, settings: AppSettings) -> int:
    """人の入力を求めずに実行する。AI同士の議論工程は対話モードと同一。"""
    if args.project:
        workspace_root = args.project.resolve()
    elif settings.default_workspace and Path(settings.default_workspace).is_dir():
        workspace_root = Path(settings.default_workspace).resolve()
    else:
        _emit({"ok": False, "exit_reason": "no_workspace",
               "detail": "作業ディレクトリを解決できません。--project で指定してください。"},
              args.json)
        return 2

    forks_override: str | None = None
    run_dir_override: Path | None = None
    if args.resume:
        run_dir_override = args.resume.resolve()
        forks_file = run_dir_override / "01_forks_and_stances.md"
        if not forks_file.exists():
            _emit({"ok": False, "exit_reason": "resume_failed",
                   "detail": f"分岐点の記録が見つかりません: {forks_file}"}, args.json)
            return 1
        forks_override = forks_file.read_text(encoding="utf-8")
        project_root = run_dir_override.parent.parent
        goal_file = goal_path(project_root)
        goal = args.goal or (
            goal_file.read_text(encoding="utf-8").split("\n\n", 1)[-1].strip()
            if goal_file.exists() else ""
        )
    else:
        goal = args.goal or ""
        name = sanitize_project_name(args.name) if args.name else suggest_project_name(goal)
        project_root = (workspace_root / settings.projects_directory / name).resolve()
        project_root.mkdir(parents=True, exist_ok=True)

    if not goal.strip():
        _emit({"ok": False, "exit_reason": "empty_goal",
               "detail": "依頼文が空です。"}, args.json)
        return 1

    initialize_project_files(project_root)

    decision = decide_level(goal, settings)
    level = args.level or decision.level
    team = settings.teams[level]

    if args.print_project_path:
        _emit({"ok": True, "exit_reason": "path_only",
               "project_name": project_root.name,
               "project_root": str(project_root),
               "level": level,
               "level_label": team.label,
               "matched_keywords": list(decision.matched_keywords),
               "debate_enabled": team.debate_enabled,
               "team": _team_summary(team)}, args.json)
        return 0

    runner = DemoModelRunner() if args.demo else CliModelRunner(settings)
    if not args.demo:
        missing = sorted({
            role.provider for role in _planning_roles(team)
            if role.enabled and not runner.available(role.provider)
        })
        if missing:
            _emit({"ok": False, "exit_reason": "cli_missing",
                   "detail": "必要なCLIが見つかりません: " + ", ".join(missing)}, args.json)
            return 2
        failures = []
        for provider in sorted({r.provider for r in _planning_roles(team) if r.enabled}):
            ok, detail = runner.auth_status(provider)
            if not ok:
                failures.append(f"{provider}: {detail}")
        if failures:
            _emit({"ok": False, "exit_reason": "not_authenticated",
                   "detail": "; ".join(failures),
                   "hint": "Codex: `codex login`  Claude: `claude auth login`"}, args.json)
            return 2

    write_text(model_selection_path(project_root), model_selection_markdown(decision, team))

    approver = _HeadlessApprover(auto_approve=bool(args.resume))
    base = {
        "project_name": project_root.name,
        "project_root": str(project_root),
        "level": level,
        "level_label": team.label,
        "matched_keywords": list(decision.matched_keywords),
        "debate_enabled": team.debate_enabled,
        "team": _team_summary(team),
    }

    try:
        with project_lock(project_root):
            workflow = CollaborationWorkflow(
                runner,
                progress=lambda message: print(f"▶ {message}", file=sys.stderr),
                approve=approver,
                confirm_no_forks=True,
            )
            outcome = workflow.execute(
                root=project_root, goal=goal, team=team,
                forks_override=forks_override,
                run_dir_override=run_dir_override,
            )
    except Exception as exc:
        _emit({**base, "ok": False, "exit_reason": "error", "detail": str(exc)}, args.json)
        return 1

    if not outcome.completed:
        _emit({**base, "ok": False, "exit_reason": "needs_approval",
               "pending_reason": approver.pending_reason or "unknown",
               "run_dir": str(outcome.run_dir),
               "forks_path": str(outcome.run_dir / "01_forks_and_stances.md")}, args.json)
        return HEADLESS_NEEDS_APPROVAL

    _emit({**base, "ok": True, "exit_reason": "completed",
           "run_dir": str(outcome.run_dir),
           "requirements_path": str(requirements_path(project_root)),
           "requirements_created": outcome.requirements_created,
           "rounds_used": outcome.rounds_used,
           "stop_reason": outcome.stop_reason,
           "issue_ids": list(outcome.issue_ids)}, args.json)
    return 0


def choose_project_directory() -> Path | None:
    print("YNFactory-ccなど、名前付きプロジェクトを保存する親フォルダを選択してください。")
    print("フォルダ選択画面が開かない場合は、パスを直接入力できます。\n")
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(title="名前付きプロジェクトを保存する親フォルダを選択")
        root.destroy()
        if selected:
            return Path(selected)
    except Exception:
        pass

    raw = input("親フォルダのパス（終了は空欄）: ").strip().strip('"')
    return Path(raw) if raw else None


def read_goal(voice: WindowsVoiceIO | None) -> str:
    if voice is None:
        return read_multiline_goal()

    while True:
        prompt = "今回やりたいことを話してください。話し終わると自動で文字になります。"
        print(f"\n{prompt}")
        voice.speak(prompt)
        heard = voice.listen()
        if not heard:
            print(f"音声を認識できませんでした: {voice.last_error}")
            if not ask_yes_no("キーボードで入力しますか？", None):
                continue
            return read_multiline_goal()
        print(f"\n認識結果: {heard}")
        if ask_yes_no("この内容でよいですか？", voice):
            return heard


def read_multiline_goal() -> str:
    print("\n今回やりたいことを入力してください。")
    print("複数行入力できます。最後に END とだけ入力してください。\n")
    lines: list[str] = []
    while True:
        line = input("> ")
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def choose_named_project(
    workspace_root: Path,
    projects_directory: str,
    goal: str,
    voice: WindowsVoiceIO | None,
) -> Path | None:
    suggested = suggest_project_name(goal)
    print(f"\n提案するプロジェクト名: {suggested}")
    if ask_yes_no("このプロジェクト名を使いますか？", voice):
        name = suggested
    else:
        if voice is not None:
            voice.speak("希望するプロジェクト名を話してください。")
            heard = voice.listen()
            if heard:
                print(f"認識したプロジェクト名: {heard}")
                name = sanitize_project_name(heard)
            else:
                name = sanitize_project_name(input("プロジェクト名: "))
        else:
            name = sanitize_project_name(input("プロジェクト名: "))

    project_root = (workspace_root / projects_directory / name).resolve()
    projects_root = (workspace_root / projects_directory).resolve()
    if projects_root not in project_root.parents:
        raise ValueError("安全でないプロジェクト名です。")

    print(f"保存先: {project_root}")
    if project_root.exists():
        if not ask_yes_no("同名プロジェクトがあります。続きとして使用しますか？", voice):
            return None
    else:
        project_root.mkdir(parents=True)
    return project_root


def select_team(
    decision: RoutingDecision,
    settings: AppSettings,
    voice: WindowsVoiceIO | None,
) -> ModelTeam:
    recommended = settings.teams[decision.level]
    print(f"\n推奨レベル: {recommended.label}")
    if voice is not None:
        if ask_yes_no(f"推奨レベルの{recommended.label}を使いますか？", voice):
            return recommended
        prompt = "軽い、通常、複雑、長期のいずれかを話してください。"
        print(prompt)
        voice.speak(prompt)
        heard = voice.listen() or ""
        mappings = (("軽", "light"), ("通常", "standard"), ("複雑", "complex"), ("長期", "critical"), ("高リスク", "critical"))
        for keyword, level in mappings:
            if keyword in heard:
                return settings.teams[level]
        print("音声からレベルを判定できなかったため、番号で選択してください。")

    print("[1] 推奨構成を使う")
    print("[2] 軽い・定型")
    print("[3] 通常")
    print("[4] 複雑")
    print("[5] 長期・高リスク")
    choice = input("番号（Enterは1）: ").strip() or "1"
    mapping = {"1": decision.level, "2": "light", "3": "standard", "4": "complex", "5": "critical"}
    return settings.teams[mapping.get(choice, decision.level)]


def show_team(decision: RoutingDecision, team: ModelTeam) -> None:
    print("\n================================")
    print("今回のモデル構成")
    print("================================")
    print(f"作業レベル: {team.label}")
    if decision.matched_keywords:
        print("判定語: " + "、".join(decision.matched_keywords))
    print(f"分岐点抽出・立場設定: {display_role(team.fork_extractor)}")
    print(f"分岐点の補完: {display_role(team.fork_auditor)}")
    print(f"立場Aの案: {display_role(team.primary_planner)}")
    print(f"立場Bの案: {display_role(team.secondary_planner)}")
    print(f"争点整理・調停: {display_role(team.plan_reviewer)}")
    print(f"議論の上限ラウンド: {team.max_debate_rounds}回")
    print(f"最終要件定義: {display_role(team.final_decider)}")
    print(f"要件定義の最終チェック: {display_role(team.requirements_final_checker)}")
    print(f"推奨実装モデル（計画に記載）: {display_role(team.recommended_implementer)}")
    print(f"推奨コードレビューモデル（計画に記載）: {display_role(team.recommended_code_reviewer)}")
    print(f"推奨最終確認モデル（計画に記載）: {display_role(team.recommended_final_gate)}")
    print("※この実行では要件定義までとし、実装は行いません。")


def show_project_state(state) -> None:
    print("\n================================")
    print("作業対象の親フォルダ")
    print("================================")
    print(f"フォルダ: {state.root}")
    print(f"Git: {'設定済み' if state.is_git else '未設定'}")
    if state.git_root:
        print(f"Gitリポジトリ: {state.git_root}")
    print(f"ブランチ: {state.branch}")
    print(f"未保存の変更: {len(state.dirty_files)}件")
    for item in state.dirty_files[:10]:
        print(f"  {item}")
    if len(state.dirty_files) > 10:
        print("  …")


def ask_yes_no(message: str, voice: WindowsVoiceIO | None = None) -> bool:
    while True:
        if voice is not None:
            print(f"\n{message} [はい/いいえ]")
            voice.speak(message)
            heard = voice.listen()
            if heard:
                print(f"認識結果: {heard}")
                answer = parse_yes_no(heard)
                if answer is not None:
                    return answer
            print("音声で判断できなかったため、キーボードで入力してください。")

        answer_text = input(f"\n{message} [y/N]: ").strip().casefold()
        if answer_text in {"y", "yes", "はい", "1"}:
            return True
        if answer_text in {"", "n", "no", "いいえ", "2"}:
            return False
        print("y または n を入力してください。")


def make_progress(voice: WindowsVoiceIO | None):
    def progress(message: str) -> None:
        print(f"\n▶ {message}")
        if voice is not None:
            voice.speak(message)

    return progress


def make_approve(voice: WindowsVoiceIO | None):
    """分岐点と立場を人間へ提示し、議論を始めてよいか確認する。"""

    def approve(document: str) -> bool:
        print("\n================================")
        print("分岐点と、これから議論させる2つの立場")
        print("================================")
        print(document)
        print("================================")
        print("この2つの立場は、どちらかを選ぶためのものではありません。")
        print("両方の良いところを1つの要件定義へまとめるための材料です。")
        if voice is not None:
            voice.speak(
                "分岐点と2つの立場を画面に表示しました。"
                "内容を確認して、この内容で議論を始めてよいか答えてください。"
            )
        return ask_yes_no("この分岐点と立場で議論を始めますか？", voice)

    return approve


def display_role(role) -> str:
    return "省略" if not role.enabled else f"{role.provider} / {role.model}"


def model_selection_markdown(decision: RoutingDecision, team: ModelTeam) -> str:
    roles = [
        ("分岐点抽出・立場設定", team.fork_extractor),
        ("分岐点の補完", team.fork_auditor),
        ("立場Aの案", team.primary_planner),
        ("立場Bの案", team.secondary_planner),
        ("争点整理・調停", team.plan_reviewer),
        ("最終要件定義", team.final_decider),
        ("要件定義の最終チェック", team.requirements_final_checker),
        ("推奨実装モデル（実行しない）", team.recommended_implementer),
        ("推奨コードレビュー（実行しない）", team.recommended_code_reviewer),
        ("推奨最終確認（実行しない）", team.recommended_final_gate),
    ]
    lines = [
        "# 今回のモデル構成",
        "",
        f"作業レベル: {team.label}",
        f"議論の上限ラウンド: {team.max_debate_rounds}回",
        "",
        "## 選定理由",
        "",
    ]
    lines.extend(f"- {reason}" for reason in decision.reasons)
    if decision.matched_keywords:
        lines.append(f"- 判定語: {'、'.join(decision.matched_keywords)}")
    lines.extend(["", "## 役割", "", "| 工程 | 担当 |", "|---|---|"])
    lines.extend(f"| {name} | {display_role(role)} |" for name, role in roles)
    return "\n".join(lines)


def _planning_roles(team: ModelTeam):
    return (
        team.fork_extractor,
        team.fork_auditor,
        team.primary_planner,
        team.secondary_planner,
        team.plan_reviewer,
        team.final_decider,
        team.requirements_final_checker,
    )


def print_header(voice_enabled: bool) -> None:
    print("================================")
    print(" AI共同開発プランナー 0.14 要件定義専用")
    print(" Claude Code + Codex CLI")
    print(f" 音声操作: {'有効' if voice_enabled else '無効'}")
    print("================================\n")


def create_voice_io(settings: AppSettings, model_override: str | None = None) -> WindowsVoiceIO:
    voice = settings.voice
    return WindowsVoiceIO(
        backend=voice.backend,
        whisper_model=model_override or voice.whisper_model,
        device=voice.device,
        compute_type=voice.compute_type,
        max_recording_seconds=voice.max_recording_seconds,
        start_timeout_seconds=voice.start_timeout_seconds,
        silence_seconds=voice.silence_seconds,
        silence_threshold=voice.silence_threshold,
        initial_prompt=voice.initial_prompt,
        corrections=dict(voice.corrections),
        input_device=voice.input_device,
    )
