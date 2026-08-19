"""Topviewで書き出した実写クリップのローカル在庫管理。

TopviewへのAPIアクセスや新規生成は行わない。手動で書き出した動画だけを
``~/shorts-factory/topview_assets`` に登録し、生成時には検証済み在庫から選ぶ。
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from .state_io import atomic_write_json, file_lock


class TopviewInventoryError(RuntimeError):
    """実写在庫が不正・不足で、混在動画を安全に停止する状態。"""


def _assets_dir(config) -> Path:
    return Path(config.get("topview", "assets_dir", default="~/shorts-factory/topview_assets")).expanduser()


def _manifest_path(config) -> Path:
    return Path(
        config.get("topview", "manifest", default=str(_assets_dir(config) / "manifest.json"))
    ).expanduser()


def _probe_clip(path: Path, ffprobe: str) -> dict:
    proc = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode:
        raise TopviewInventoryError(f"Topview素材を解析できません: {path.name}")
    try:
        data = json.loads(proc.stdout)
        video = next(s for s in data.get("streams", []) if s.get("codec_type") == "video")
        duration = float(data["format"]["duration"])
        width, height = int(video["width"]), int(video["height"])
    except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TopviewInventoryError(f"Topview素材のメタデータが不正です: {path.name}") from exc
    return {"duration_sec": round(duration, 3), "width": width, "height": height}


def _validate_split_meta(meta: dict, config) -> None:
    """1本を前後に分割する運用に必要な尺・縦型を検証する。"""
    min_duration = float(config.get("topview", "min_clip_duration_sec", default=11.5))
    max_duration = float(config.get("topview", "max_clip_duration_sec", default=12.5))
    duration = float(meta["duration_sec"])
    if duration < min_duration or duration > max_duration:
        raise TopviewInventoryError(
            f"Topview分割素材の尺が対象外です: {duration:.3f}秒（{min_duration:.1f}〜{max_duration:.1f}秒）"
        )
    if int(meta["width"]) * 16 != int(meta["height"]) * 9:
        raise TopviewInventoryError("Topview分割素材が9:16ではありません")


def _load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise TopviewInventoryError(f"Topview在庫マニフェストがありません: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TopviewInventoryError(f"Topview在庫マニフェストを読めません: {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("clips"), list):
        raise TopviewInventoryError("Topview在庫マニフェストの clips が不正です")
    return data


def validate_inventory(config) -> tuple[dict, list[dict], Path]:
    """在庫を再プローブしてから返す。異常時は一切フォールバックしない。"""
    assets_dir = _assets_dir(config).resolve()
    manifest_path = _manifest_path(config)
    manifest = _load_manifest(manifest_path)
    min_count = max(1, int(config.get("topview", "min_enabled_clips", default=4)))
    required_format = str(config.get("topview", "required_format", default="split_12s_v1"))
    ffprobe = str(config.get("ffprobe", default="ffprobe"))
    enabled: list[dict] = []
    ids: set[str] = set()
    for raw in manifest["clips"]:
        if not isinstance(raw, dict) or not raw.get("enabled", True):
            continue
        # 旧形式は履歴として残すが、現行の1本分割在庫には混在させない。
        if raw.get("format") != required_format:
            continue
        clip = dict(raw)
        clip_id, filename = clip.get("id"), clip.get("file")
        if not isinstance(clip_id, str) or not clip_id or clip_id in ids:
            raise TopviewInventoryError("Topview在庫の id が重複または不正です")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise TopviewInventoryError(f"Topview在庫のファイル名が不正です: {clip_id}")
        path = (assets_dir / filename).resolve()
        if assets_dir not in path.parents or not path.is_file():
            raise TopviewInventoryError(f"Topview素材が見つかりません: {filename}")
        actual = _probe_clip(path, ffprobe)
        _validate_split_meta(actual, config)
        for key in ("duration_sec", "width", "height"):
            if key not in clip:
                raise TopviewInventoryError(f"Topview在庫の {key} がありません: {clip_id}")
        if abs(float(clip["duration_sec"]) - actual["duration_sec"]) > 0.75 or int(clip["width"]) != actual["width"] or int(clip["height"]) != actual["height"]:
            raise TopviewInventoryError(f"Topview在庫のメタデータが実ファイルと一致しません: {filename}")
        if clip.get("ratio") != "9:16":
            raise TopviewInventoryError(f"Topview在庫の比率表記が不正です: {clip_id}")
        clip["path"] = path
        enabled.append(clip)
        ids.add(clip_id)
    if len(enabled) < min_count:
        raise TopviewInventoryError(
            f"Topview実写在庫が不足しています: 有効 {len(enabled)} 本 / 必要 {min_count} 本。旧カード版は作成しません。"
        )
    return manifest, enabled, manifest_path


def select_live_clips(config, count: int = 2) -> tuple[list[dict], Path]:
    manifest, clips, manifest_path = validate_inventory(config)
    # 同じ素材を別の最終ショートへ再利用しない。使い切った場合は旧素材を
    # 循環させず、新規の書き出し素材が補充されるまで安全停止する。
    unused = [clip for clip in clips if int(clip.get("use_count", 0)) == 0]
    if len(unused) < count:
        raise TopviewInventoryError(
            f"未使用のTopview実写在庫が不足しています: 有効未使用 {len(unused)} 本 / 必要 {count} 本。"
            "使用済み素材は再利用しません。"
        )
    # 朝4時に作る当日分4本を、9/14/19時の3本で先に消費する。
    # 残る1本と前日以前の未使用素材は、当日の補充が失敗・不足した時だけ使う
    # 予備として残す。registered_at のない旧マニフェスト項目は後方互換のためID順にする。
    current_batch = [clip for clip in unused if clip.get("registered_at")]
    reserve = [clip for clip in unused if not clip.get("registered_at")]
    current_batch.sort(key=lambda c: (str(c["registered_at"]), c["id"]), reverse=True)
    reserve.sort(key=lambda c: c["id"])
    return (current_batch + reserve)[:count], manifest_path


def record_usage(config, selected_ids: list[str]) -> None:
    """完成成果物に使った素材だけを、ロック付きで使用済みにする。"""
    path = _manifest_path(config)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with file_lock(lock_path):
        manifest = _load_manifest(path)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        seen = set(selected_ids)
        for clip in manifest["clips"]:
            if clip.get("id") in seen:
                clip["use_count"] = int(clip.get("use_count", 0)) + 1
                clip["last_used_at"] = now
        manifest["updated_at"] = now
        atomic_write_json(path, manifest, mode=0o600)


def register_files(config, filenames: list[str]) -> Path:
    """assets_dir内の手動書き出し済みクリップをマニフェストへ追加登録する。

    既存マニフェストへ追記し、既に登録済みのクリップの ``use_count`` /
    ``last_used_at`` は保持する。補充のたびに全体を置き換えると使用履歴が
    消え、公開済みの実写が別動画で再利用されてしまうため。
    """
    assets_dir = _assets_dir(config).expanduser().resolve()
    ffprobe = str(config.get("ffprobe", default="ffprobe"))
    path = _manifest_path(config)
    lock_path = path.with_suffix(path.suffix + ".lock")
    with file_lock(lock_path):
        existing: list[dict] = _load_manifest(path)["clips"] if path.is_file() else []
        by_id = {c["id"]: c for c in existing if isinstance(c, dict) and isinstance(c.get("id"), str)}
        added: list[dict] = []
        registered_at = datetime.now().astimezone().isoformat(timespec="seconds")
        for filename in filenames:
            name = Path(filename).name
            if name != filename:
                raise TopviewInventoryError("登録できるのは assets_dir 直下のファイルだけです")
            file_path = (assets_dir / name).resolve()
            if not file_path.is_file():
                raise TopviewInventoryError(f"登録対象がありません: {name}")
            meta = _probe_clip(file_path, ffprobe)
            _validate_split_meta(meta, config)
            clip_id = "topview-" + Path(name).stem.lower().replace(" ", "-")
            prior = by_id.get(clip_id, {})
            by_id[clip_id] = {
                "id": clip_id,
                "file": name,
                "enabled": True,
                "ratio": "9:16",
                "format": str(config.get("topview", "required_format", default="split_12s_v1")),
                **meta,
                "use_count": int(prior.get("use_count", 0) or 0),
                "last_used_at": prior.get("last_used_at"),
                # 再登録で既存素材を当日分として扱い直さない。新規書き出しだけに
                # 登録時刻を付け、当日分を優先して消費できるようにする。
                "registered_at": prior.get("registered_at") or registered_at,
            }
            added.append(by_id[clip_id])
        if len({c["id"] for c in added}) != len(added):
            raise TopviewInventoryError("登録対象のファイル名から作るIDが重複しています")
        atomic_write_json(path, {
            "schema_version": 1,
            "source": "topview_manual_export",
            "updated_at": registered_at,
            "clips": list(by_id.values()),
        }, mode=0o600)
    return path
