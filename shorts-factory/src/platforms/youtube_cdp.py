"""YouTube Shorts アップロード（常駐Chrome + Playwright CDP接続）。

Data API v3 は未審査プロジェクトの動画が強制非公開になるため、
notebooklm-sync と同じ「常駐Chrome(専用プロファイル) + CDP」方式で
YouTube Studio をブラウザ操作してアップロードする。

前提:
- launchd com.ynfactory.shorts-chrome が port 9223 でChromeを常駐
- 初回のみ scripts/login_youtube.sh でそのプロファイルにGoogleログイン済み

セレクタは言語非依存の id / name のみ使用（UI文言変更に強い）。
失敗時は logs/ にスクリーンショットを保存して例外を投げる。
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from ..config import CONFIG

CDP_URL = f"http://127.0.0.1:{CONFIG.get('youtube', 'cdp_port', default=9223)}"
UPLOAD_URL = "https://www.youtube.com/upload"


class SessionExpired(RuntimeError):
    """Googleセッション失効。login_youtube.sh での再ログインが必要。"""


def _shot(page, tag: str) -> Path:
    p = CONFIG.logs_dir / f"yt_{tag}_{datetime.now().strftime('%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(p))
    except Exception:
        pass
    return p


def check_session() -> bool:
    """Studioに到達できるか（ログイン生存確認）。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        try:
            page.goto("https://studio.youtube.com", timeout=45000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)
            return "accounts.google.com" not in page.url
        finally:
            page.close()


def upload(video_path: Path, title: str, description: str, timeout_sec: int = 420) -> str:
    """動画をアップロードして公開し、URLを返す。"""
    from playwright.sync_api import sync_playwright

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        ctx.set_default_timeout(45000)
        page = ctx.new_page()
        try:
            page.goto(UPLOAD_URL, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(4)
            if "accounts.google.com" in page.url:
                raise SessionExpired(
                    "YouTubeセッション失効。scripts/login_youtube.sh で再ログインしてください"
                )

            # ファイル選択（アップロードダイアログの input[type=file]）
            page.wait_for_selector("input[type=file]", state="attached", timeout=60000)
            page.set_input_files("input[type=file]", str(video_path))

            # メタデータダイアログ
            page.wait_for_selector("ytcp-uploads-dialog", timeout=90000)
            time.sleep(3)
            boxes = page.locator("ytcp-uploads-dialog #textbox")
            boxes.nth(0).click()
            page.keyboard.press("Meta+A")
            page.keyboard.type(title, delay=10)
            boxes.nth(1).click()
            page.keyboard.press("Meta+A")
            page.keyboard.type(description[:4500], delay=5)

            # 「子ども向けではない」
            page.click("tp-yt-paper-radio-button[name='VIDEO_MADE_FOR_KIDS_NOT_MFK']")

            # 動画URLを先に取得（ダイアログ内の youtu.be リンク）
            url = ""
            try:
                page.wait_for_selector("a[href^='https://youtu.be/']", timeout=60000)
                url = page.locator("a[href^='https://youtu.be/']").first.get_attribute("href") or ""
            except Exception:
                pass

            # 次へ ×3（詳細 → 動画の要素 → チェック）
            for _ in range(3):
                page.click("#next-button")
                time.sleep(2)

            # 公開設定
            page.click("tp-yt-paper-radio-button[name='PUBLIC']")
            time.sleep(1)

            # アップロード完了を待ってから保存（done が有効になるまで）
            deadline = time.time() + timeout_sec
            ready = False
            while time.time() < deadline:
                btn = page.locator("#done-button")
                if btn.count() and btn.first.is_enabled():
                    ready = True
                    break
                time.sleep(3)
            if not ready:
                raise RuntimeError(f"アップロードが{timeout_sec}秒以内に完了しませんでした")
            page.click("#done-button")
            time.sleep(3)

            # 「処理中」ダイアログが出たら閉じる
            try:
                dialog_close = page.locator(
                    "ytcp-uploads-still-processing-dialog #close-button, "
                    "ytcp-uploads-still-processing-dialog ytcp-button"
                )
                if dialog_close.count():
                    dialog_close.first.click()
            except Exception:
                pass

            if not url:
                raise RuntimeError("動画URLが取得できませんでした（アップロードは完了している可能性あり）")
            return url
        except SessionExpired:
            raise
        except Exception as e:
            shot = _shot(page, "fail")
            raise RuntimeError(f"YouTubeアップロード失敗: {e}（スクショ: {shot}）") from e
        finally:
            page.close()
