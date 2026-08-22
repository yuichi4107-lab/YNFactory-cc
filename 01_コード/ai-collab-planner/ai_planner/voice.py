from __future__ import annotations

import base64
import os
import shutil
import subprocess
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WindowsVoiceIO:
    """ローカルWhisperを優先し、Windows標準認識へ安全に戻せる音声入出力。"""

    backend: str = "auto"
    whisper_model: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    max_recording_seconds: int = 60
    start_timeout_seconds: int = 10
    silence_seconds: float = 1.2
    silence_threshold: float = 0.012
    initial_prompt: str = ""
    corrections: dict[str, str] = field(default_factory=dict)
    input_device: str = ""
    recognition_seconds: int = 30
    last_error: str = ""
    status_detail: str = ""
    _model: Any = field(default=None, init=False, repr=False)

    def available(self) -> bool:
        whisper_ok, whisper_detail = self._whisper_available()
        windows_ok, windows_detail = self._windows_recognition_available()

        if self.backend in {"auto", "whisper"} and whisper_ok:
            self.status_detail = f"高精度ローカルWhisper（{self.whisper_model}）"
            self.last_error = ""
            return True
        if windows_ok:
            self.status_detail = "Windows標準音声認識（予備）"
            self.last_error = ""
            return True

        details = [detail for detail in (whisper_detail, windows_detail) if detail]
        self.last_error = " / ".join(details) or "利用できる音声認識がありません。"
        self.status_detail = self.last_error
        return False

    def listen(self) -> str | None:
        errors: list[str] = []
        if self.backend in {"auto", "whisper"}:
            text = self._listen_whisper()
            if text:
                self.status_detail = f"高精度ローカルWhisper（{self.whisper_model}）"
                self.last_error = ""
                return self._apply_corrections(text)
            if self.last_error:
                errors.append(f"Whisper: {self.last_error}")

        if errors:
            print("高精度音声認識を使用できなかったため、Windows標準認識へ切り替えます。もう一度話してください。")
        text = self._listen_windows()
        if text:
            self.status_detail = "Windows標準音声認識（予備）"
            self.last_error = ""
            return self._apply_corrections(text)
        if self.last_error:
            errors.append(f"Windows: {self.last_error}")
        self.last_error = " / ".join(errors) or "音声を認識できませんでした。"
        return None

    def speak(self, text: str) -> bool:
        if not text.strip() or _powershell_command() is None:
            return False
        script = r"""
try {
  Add-Type -AssemblyName System.Speech
  $speaker = [System.Speech.Synthesis.SpeechSynthesizer]::new()
  $culture = [System.Globalization.CultureInfo]::GetCultureInfo('ja-JP')
  $voice = $speaker.GetInstalledVoices($culture) | Select-Object -First 1
  if ($null -ne $voice) { $speaker.SelectVoice($voice.VoiceInfo.Name) }
  $speaker.Speak($env:AI_PLANNER_SPEAK_TEXT)
  $speaker.Dispose()
} catch { exit 4 }
"""
        environment = os.environ.copy()
        environment["AI_PLANNER_SPEAK_TEXT"] = text[:1000]
        result = _run_powershell(script, timeout=60, env=environment)
        return result.returncode == 0

    def preload_whisper_model(self) -> bool:
        try:
            self._load_whisper_model()
            self.status_detail = f"Whisperモデル準備済み（{self.whisper_model}）"
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def _listen_whisper(self) -> str | None:
        ok, detail = self._whisper_available()
        if not ok:
            self.last_error = detail
            return None
        try:
            audio = self._record_until_silence()
            if audio is None:
                return None
            model = self._load_whisper_model()
            segments, _ = model.transcribe(
                audio,
                language="ja",
                beam_size=5,
                temperature=0.0,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 300},
                initial_prompt=self.initial_prompt or None,
                condition_on_previous_text=False,
            )
            text = "".join(segment.text for segment in segments).strip()
            if not text:
                self.last_error = "音声から文字を取得できませんでした。"
                return None
            return text
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def _record_until_silence(self):
        import numpy as np
        import sounddevice as sd

        sample_rate = 16000
        block_seconds = 0.1
        block_frames = int(sample_rate * block_seconds)
        pre_roll = deque(maxlen=4)
        recorded: list[Any] = []
        speech_started = False
        silent_blocks = 0
        required_silent_blocks = max(3, int(self.silence_seconds / block_seconds))
        started_at = time.monotonic()

        print("音声を待っています。自然に話してください。話し終わると自動で停止します。")
        with sd.InputStream(
            device=self.input_device or None,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_frames,
        ) as stream:
            while time.monotonic() - started_at < self.max_recording_seconds:
                data, overflowed = stream.read(block_frames)
                if overflowed:
                    self.last_error = "録音データの一部が欠けました。マイク設定を確認してください。"
                mono = data[:, 0].copy()
                rms = float(np.sqrt(np.mean(np.square(mono))))

                if not speech_started:
                    pre_roll.append(mono)
                    if rms >= self.silence_threshold:
                        speech_started = True
                        recorded.extend(pre_roll)
                        pre_roll.clear()
                    elif time.monotonic() - started_at >= self.start_timeout_seconds:
                        self.last_error = "話し始めを検出できませんでした。マイクへ少し近づいて話してください。"
                        return None
                    continue

                recorded.append(mono)
                if rms < self.silence_threshold:
                    silent_blocks += 1
                    if silent_blocks >= required_silent_blocks:
                        break
                else:
                    silent_blocks = 0

        if not recorded:
            self.last_error = "音声が録音されませんでした。"
            return None
        return np.concatenate(recorded).astype(np.float32, copy=False)

    def _load_whisper_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            print(f"Whisperモデルを準備しています: {self.whisper_model}")
            self._model = WhisperModel(
                self.whisper_model,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def _whisper_available(self) -> tuple[bool, str]:
        try:
            import faster_whisper  # noqa: F401
            import numpy  # noqa: F401
            import sounddevice as sd

            sd.query_devices(kind="input")
            return True, f"ローカルWhisper（{self.whisper_model}）"
        except Exception as exc:
            return False, f"高精度音声認識が未設定です: {exc}"

    def _windows_recognition_available(self) -> tuple[bool, str]:
        if _powershell_command() is None:
            return False, "PowerShellが見つかりません。"
        script = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
try {
  Add-Type -AssemblyName System.Speech
  $items = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
  $ja = $items | Where-Object { $_.Culture.Name -eq 'ja-JP' } | Select-Object -First 1
  if ($null -eq $ja) { exit 3 }
  [Console]::Write('OK')
} catch { exit 4 }
"""
        result = _run_powershell(script, timeout=15)
        if result.returncode == 0 and result.stdout.strip() == "OK":
            return True, "Windows標準音声認識"
        return False, "Windowsの日本語音声認識が利用できません。"

    def _listen_windows(self) -> str | None:
        seconds = max(5, min(self.recognition_seconds, 120))
        script = rf"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
try {{
  Add-Type -AssemblyName System.Speech
  $culture = [System.Globalization.CultureInfo]::GetCultureInfo('ja-JP')
  $recognizer = [System.Speech.Recognition.SpeechRecognitionEngine]::new($culture)
  $grammar = [System.Speech.Recognition.DictationGrammar]::new()
  $recognizer.LoadGrammar($grammar)
  $recognizer.SetInputToDefaultAudioDevice()
  $result = $recognizer.Recognize([TimeSpan]::FromSeconds({seconds}))
  $recognizer.Dispose()
  if ($null -eq $result) {{ exit 3 }}
  [Console]::Write($result.Text)
}} catch {{
  [Console]::Error.Write($_.Exception.Message)
  exit 4
}}
"""
        result = _run_powershell(script, timeout=seconds + 15)
        text = result.stdout.strip()
        if result.returncode == 0 and text:
            return text
        self.last_error = result.stderr.strip() or "音声を認識できませんでした。"
        return None

    def _apply_corrections(self, text: str) -> str:
        corrected = text.strip()
        for before, after in self.corrections.items():
            corrected = corrected.replace(before, after)
        return corrected


def parse_yes_no(text: str) -> bool | None:
    normalized = text.strip().casefold().replace(" ", "")
    yes_words = ("はい", "うん", "ええ", "進めて", "お願いします", "問題ない", "オーケー", "ok", "yes", "イエス")
    no_words = ("いいえ", "いや", "やめて", "中止", "キャンセル", "修正", "no", "ノー")
    if any(word in normalized for word in yes_words):
        return True
    if any(word in normalized for word in no_words):
        return False
    return None


def _powershell_command() -> str | None:
    return shutil.which("powershell.exe") or shutil.which("powershell")


def _run_powershell(
    script: str,
    timeout: int,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = _powershell_command()
    if command is None:
        return subprocess.CompletedProcess(["powershell"], 127, "", "PowerShellが見つかりません。")
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    try:
        return subprocess.run(
            [command, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess([command], 124, "", "音声処理がタイムアウトしました。")
