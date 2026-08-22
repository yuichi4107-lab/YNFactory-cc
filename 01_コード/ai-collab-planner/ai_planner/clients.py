from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import AppSettings
from .domain import Role, RunResult


class ModelRunner(Protocol):
    def run(self, role: Role, prompt: str, cwd: Path, writable: bool = False) -> RunResult:
        ...


@dataclass
class CliModelRunner:
    settings: AppSettings

    def available(self, provider: str) -> bool:
        if provider == "none":
            return True
        command = self.settings.codex_command if provider == "codex" else self.settings.claude_command
        return shutil.which(command) is not None

    def auth_status(self, provider: str) -> tuple[bool, str]:
        if provider == "none":
            return True, "認証不要"
        command_name = self.settings.codex_command if provider == "codex" else self.settings.claude_command
        resolved = shutil.which(command_name)
        if resolved is None:
            return False, f"{command_name} が見つかりません。"
        args = [resolved, "login", "status"] if provider == "codex" else [resolved, "auth", "status", "--text"]
        try:
            completed = subprocess.run(
                args,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            return False, f"認証状態を確認できませんでした: {exc}"
        detail = (completed.stdout.strip() or completed.stderr.strip() or "詳細なし").splitlines()[0]
        return completed.returncode == 0, detail

    def run(self, role: Role, prompt: str, cwd: Path, writable: bool = False) -> RunResult:
        if not role.enabled:
            return RunResult("none", "none", "（この工程は省略されました）", 0, "none")

        if role.provider == "codex":
            command = self._codex_command(role, prompt, writable)
            stdin_text = prompt
        elif role.provider == "claude":
            command = self._claude_command(role, prompt, writable)
            stdin_text = prompt
        else:
            raise ValueError(f"未対応のプロバイダーです: {role.provider}")

        resolved_command = shutil.which(command[0])
        if resolved_command is not None:
            command[0] = resolved_command

        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                text=True,
                encoding="utf-8",
                errors="replace",
                input=stdin_text,
                capture_output=True,
                timeout=self.settings.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"{command[0]} が見つかりません。インストールとログインを確認してください。") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{role.model} の処理が制限時間を超えました。") from exc

        output = completed.stdout.strip()
        if completed.returncode != 0:
            detail = completed.stderr.strip() or output or "詳細不明"
            raise RuntimeError(f"{role.provider} ({role.model}) の実行に失敗しました。\n{detail}")

        return RunResult(
            provider=role.provider,
            model=role.model,
            output=output,
            return_code=completed.returncode,
            command_summary=" ".join(command[:5]) + " …",
        )

    def _codex_command(self, role: Role, prompt: str, writable: bool) -> list[str]:
        sandbox = "workspace-write" if writable else "read-only"
        return [
            self.settings.codex_command,
            "exec",
            "-m",
            role.model,
            "--sandbox",
            sandbox,
            "--skip-git-repo-check",
            "--ephemeral",
            "-",
        ]

    def _claude_command(self, role: Role, prompt: str, writable: bool) -> list[str]:
        permission_mode = "acceptEdits" if writable else "plan"
        command = [
            self.settings.claude_command,
            "-p",
            "標準入力に渡された依頼本文に従ってください。",
            "--model",
            role.model,
            "--output-format",
            "text",
            "--permission-mode",
            permission_mode,
        ]
        if not writable:
            command.extend(["--tools", "Read,Glob,Grep", "--strict-mcp-config"])
        return command


DEMO_FORKS = """# 分岐点と立場

## 確認した事実

デモ実行のため、実際のフォルダ調査は行っていません。

## 分岐点

1. 保存先をローカル内に閉じるか、外部サービスへ預けるか（不可逆性：高）
2. 最初から複数人で使う前提にするか、1人用で始めるか（不可逆性：中）

## 立場A

### 優先するもの

早く形にして試せること。

### 捨てるもの

将来の拡張余地。あとから作り直す前提を受け入れます。

## 立場B

### 優先するもの

作り直しが要らない構造。

### 捨てるもの

初期の速さ。最初の一歩が重くなることを受け入れます。
"""

DEMO_ISSUES = """# 争点表

| 争点ID | 論点 | 立場Aの案 | 立場Bの案 | 違いが生まれた理由 | 統合を判断するのに必要な情報 |
|---|---|---|---|---|---|
| A-1 | 保存先 | ローカルに閉じる | 外部サービスへ預ける | 速さと拡張性の重心の違い | 利用人数の見込み |
| A-2 | 利用人数 | 1人用で始める | 最初から複数人 | 同上 | 共有の必要性 |

## 補足

デモ用の固定データです。
"""

DEMO_RESPONSE = """# 応答

## 争点ごとの応答

### A-1

両立させる。保存の入口を1か所にまとめれば、後から預け先を差し替えられます。

### A-2

取り込む。1人用で始めても、識別子を最初から持たせておけば複数人へ広げられます。

## 争点の立て方への異議

なし
"""

DEMO_MEDIATION = """# 調停

## ここまでの経緯

両者とも、保存の入口を1か所にまとめる案で一致しました。

## 争点ごとの統合案

| 争点ID | 状態 | 統合案 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合に人間が決めること |
|---|---|---|---|---|---|
| A-1 | 統合済み | 保存処理を1か所に集約し、当面はローカルへ保存する | すぐ動く実装 | 差し替え可能な構造 | - |
| A-2 | 統合済み | 1人用で始め、識別子だけ先に持たせる | 小さく始める判断 | 将来の複数人対応 | - |

## 未整理件数

未整理: 0件

## 継続判定

終了：統合完了
"""

DEMO_REQUIREMENTS = """# 要件定義書・実装プラン

## 1. 背景と目的

デモ目的を安全に確認します。

## 2. 想定利用者と利用場面

依頼者が利用します。

## 3. 現状と解決する課題

動作確認が必要です。

## 4. 対象範囲

要件定義資料を対象にします。

## 5. 対象外

コード実装、公開、課金は行いません。

## 6. 機能要件

依頼内容を整理します。

## 7. 非機能要件

初心者にも読みやすくします。

## 8. 画面・操作・業務の流れ

入力から要件定義書を作成します。

## 9. データ・外部連携

デモでは外部連携しません。

## 10. 完了条件・受入基準

必要な見出しが揃うこと。

## 11. 制約・リスク・依存関係

実AIは呼び出しません。

## 12. 未決事項・確認質問

実装開始前に人間が確認します。

## 13. 実装プラン

### 13.1 実装工程

設計、実装、検証に分けます。

### 13.2 テスト方針

受入基準に沿って確認します。

### 13.3 AIモデルの役割分担

| 工程 | 推奨系統 | 具体的モデル | 選定理由 | 代替候補 |
|---|---|---|---|---|
| 実装 | GPT系 | 設定済みモデル | コード作業向け | Claude系モデル |

### 13.4 人間の承認ポイント

実装開始前に承認します。

## 14. 争点と統合結果

| 争点ID | 状態 | 統合後の結論 | 立場Aから採った要素 | 立場Bから採った要素 | 要判断の場合の人間への質問 |
|---|---|---|---|---|---|
| A-1 | 統合済み | 保存処理を1か所に集約する | すぐ動く実装 | 差し替え可能な構造 | - |
| A-2 | 統合済み | 1人用で始め、識別子を先に持たせる | 小さく始める判断 | 将来の複数人対応 | - |
"""


@dataclass
class DemoModelRunner:
    """CLIや利用枠を消費せず、画面とファイル生成だけを確認する。"""

    counter: int = 0

    def available(self, provider: str) -> bool:
        return True

    def run(self, role: Role, prompt: str, cwd: Path, writable: bool = False) -> RunResult:
        self.counter += 1
        action = "書き込み" if writable else "読み取り専用の検討"
        # 工程タグは各プロンプトの指示部分にだけ現れる。埋め込まれた過去の出力には含まれない。
        if "【工程】分岐点抽出と立場設定" in prompt:
            output = DEMO_FORKS
        elif "【工程】分岐点の補完" in prompt:
            output = DEMO_FORKS
        elif "【工程】争点表の作成" in prompt:
            output = DEMO_ISSUES
        elif "【工程】相互検討への応答" in prompt:
            output = DEMO_RESPONSE
        elif "【工程】調停" in prompt:
            output = DEMO_MEDIATION
        elif "【工程】要件定義書の最終チェック" in prompt:
            output = DEMO_REQUIREMENTS
        elif "【工程】要件定義書・実装プランの統合" in prompt:
            output = DEMO_REQUIREMENTS
        else:
            output = (
                f"# デモ出力 {self.counter}\n\n"
                f"- 担当: {role.provider} / {role.model}\n"
                f"- 種類: {action}\n"
                "- この出力は動作確認用で、実際のAIは呼び出していません。\n\n"
                "## 結果\n\n依頼内容を段階分けし、各段階に確認方法を設けます。"
            )
        return RunResult(role.provider, role.model, output, 0, "demo")
