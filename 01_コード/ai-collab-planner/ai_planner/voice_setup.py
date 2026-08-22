from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_settings
from .voice import WindowsVoiceIO


APP_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="高精度ローカルWhisperモデルを準備します")
    parser.add_argument("--model", help="準備するモデル名（small / medium等）")
    parser.add_argument("--list-devices", action="store_true", help="利用可能なマイクを一覧表示")
    args = parser.parse_args(argv)

    if args.list_devices:
        try:
            import sounddevice as sd

            print("利用可能な音声機器:")
            print(sd.query_devices())
            print("\n先頭の番号または機器名を config.toml の input_device に設定できます。")
            return 0
        except Exception as exc:
            print(f"音声機器を取得できませんでした: {exc}")
            return 1

    settings = load_settings(APP_ROOT / "config.toml")
    voice = settings.voice
    recognizer = WindowsVoiceIO(
        backend="whisper",
        whisper_model=args.model or voice.whisper_model,
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

    print(f"Whisperモデルを準備します: {recognizer.whisper_model}")
    print("初回はモデルをダウンロードするため、時間がかかります。")
    if recognizer.preload_whisper_model():
        print("\n準備が完了しました。")
        return 0
    print(f"\n準備に失敗しました: {recognizer.last_error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
