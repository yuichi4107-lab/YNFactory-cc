"""AIの出力に混ざった秘密情報と、指示の上書きを狙う文を検出する。

このツールは「フォルダを読む → AIへ渡す → ファイルへ書く → 別のAIへ渡す」構造のため、
外部から入った文字列が多くの工程を経由する。ここはその通り道に置く検査。

方針:
- 秘密情報は検出したら停止する。外部へ出た秘密は取り消せないため。
- 指示の上書きを狙う文は停止せず警告する。誤検知でツールが使えなくなるため。
  ただし最終文書だけは例外で、将来のAIセッションへの永続指示になるため停止する。
- 検出結果に秘密の値そのものを含めない。表示やログ自体が漏洩経路になるため。
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    name: str
    line: int

    def describe(self) -> str:
        return f"{self.name}（{self.line}行目）"


# 明らかに鍵・トークンの形式のものだけを対象にする。
# 汎用語（password等）は、十分な長さの値が続く場合だけ拾う。
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("秘密鍵ファイルの内容", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("OpenAI APIキー", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}")),
    ("Anthropic APIキー", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("GitHubトークン", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}")),
    ("GitHub Personal Access Token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("AWSアクセスキーID", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google APIキー", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Slackトークン", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Stripeキー", re.compile(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{20,}")),
    (
        "認証情報の代入",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret|password|passwd)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9!@#$%^&*_+=/-]{16,}"
        ),
    ),
)

# 指示の上書きを狙う語だけに絞る。通常の日本語の要件記述では出ない表現を選ぶ。
INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("これまでの指示を無効化する文", re.compile(r"(?:これまで|以前|上記|前)の(?:指示|命令|ルール)[^。\n]{0,10}(?:無視|無効|忘れ)")),
    ("英語の指示上書き", re.compile(r"(?i)ignore\s+(?:all\s+)?(?:the\s+)?(?:previous|prior|above)\s+instructions?")),
    ("役割の乗っ取り", re.compile(r"(?i)(?:you\s+are\s+now|あなたは今から|あなたの新しい役割)")),
    ("システムプロンプトの詐称", re.compile(r"(?i)(?:system\s*prompt|<\s*/?\s*system\s*>|\[system\])")),
    ("読み取り専用の解除要求", re.compile(r"(?:読み取り専用|read[- ]?only)[^。\n]{0,15}(?:解除|無視|外し)")),
    ("実装・実行の指示", re.compile(r"(?:実際に|必ず)[^。\n]{0,10}(?:コードを実装|コマンドを実行|デプロイ)")),
    ("将来のセッションへの指示", re.compile(r"(?:このファイルを読んだ|次のセッション|今後のAI)[^。\n]{0,20}(?:は|に)[^。\n]{0,20}(?:すること|してください|せよ)")),
    ("危険なコマンド", re.compile(r"(?:rm\s+-rf\s+/|curl[^\n]{0,40}\|\s*(?:sh|bash)|Invoke-Expression)")),
)


def _scan(text: str, patterns: tuple[tuple[str, re.Pattern[str]], ...]) -> tuple[Finding, ...]:
    findings: list[Finding] = []
    seen: set[str] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in patterns:
            if name in seen:
                continue
            if pattern.search(line):
                findings.append(Finding(name, number))
                seen.add(name)
    return tuple(findings)


def scan_secrets(text: str) -> tuple[Finding, ...]:
    """秘密情報らしき記述を探す。値そのものは返さない。"""
    return _scan(text, SECRET_PATTERNS)


def scan_injection(text: str) -> tuple[Finding, ...]:
    """指示の上書きを狙う文を探す。"""
    return _scan(text, INJECTION_PATTERNS)


def assert_no_secrets(stage: str, text: str) -> None:
    """秘密情報を検出したら停止する。エラー文に値そのものを含めない。"""
    findings = scan_secrets(text)
    if findings:
        detail = "、".join(finding.describe() for finding in findings)
        raise RuntimeError(
            f"{stage}の出力に認証情報らしき記述が含まれていたため、成果物を保存せず停止しました。"
            f"検出: {detail}。"
            "対象フォルダから認証情報ファイルを外すか、AIが読まない場所へ移してから実行してください。"
            "（安全のため、検出した値そのものは表示していません）"
        )


def assert_no_injection(stage: str, text: str) -> None:
    """最終文書のみに適用する。将来のAIセッションへの永続指示になるため停止する。"""
    findings = scan_injection(text)
    if findings:
        detail = "、".join(finding.describe() for finding in findings)
        raise RuntimeError(
            f"{stage}に、AIへの指示と解釈されうる文が含まれていたため、保存せず停止しました。"
            f"検出: {detail}。"
            "この文書は今後のAIセッションが毎回読むため、指示文が残ると影響が続きます。"
        )


def injection_warning(findings: tuple[Finding, ...]) -> str:
    """人間の承認画面の先頭に付ける警告文を作る。"""
    if not findings:
        return ""
    detail = "\n".join(f"  - {finding.describe()}" for finding in findings)
    return (
        "!!! 注意 !!!\n"
        "この内容に、AIへの指示と解釈されうる文が含まれています。\n"
        "対象フォルダのファイルに、AIを誘導する文が仕込まれている可能性があります。\n"
        f"{detail}\n"
        "心当たりがなければ、承認せず中止して、対象フォルダの中身を確認してください。\n"
        "----------------------------------------\n\n"
    )
