"""TikTok アップロード（常駐Chrome + Playwright CDP接続）。【実験的】

公式 Content Posting API は審査必須のため、TikTok Studio のアップロード画面を
ブラウザ操作する。TikTokはUI変更が頻繁なので、失敗時はスクリーンショットを
保存して blocked にし、人間へ通知する運用とする。

前提: shorts-chrome の常駐Chromeプロファイルに TikTok ログイン済み。
config.yaml の queue.platforms に "tiktok" を加えると有効化される。
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from ..config import CONFIG

CDP_URL = f"http://127.0.0.1:{CONFIG.get('youtube', 'cdp_port', default=9223)}"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"


def _shot(page, tag: str) -> Path:
    p = CONFIG.logs_dir / f"tt_{tag}_{datetime.now().strftime('%m%d_%H%M%S')}.png"
    try:
        page.screenshot(path=str(p))
    except Exception:
        pass
    return p


def upload(video_path: Path, caption: str, timeout_sec: int = 420) -> str:
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
            time.sleep(5)
            if "login" in page.url:
                raise RuntimeError("TikTokセッション失効。常駐Chromeで tiktok.com に再ログインしてください")

            page.wait_for_selector("input[type=file]", state="attached", timeout=60000)
            page.set_input_files("input[type=file]", str(video_path))

            # アップロード完了（キャプション編集領域の出現）を待つ
            page.wait_for_selector("div[contenteditable='true']", timeout=180000)
            time.sleep(3)

            editor = page.locator("div[contenteditable='true']").first
            editor.click()
            page.keyboard.press("Meta+A")
            page.keyboard.press("Delete")
            page.keyboard.type(caption[:2000], delay=10)
            time.sleep(2)

            # 投稿ボタン（data-e2e属性は比較的安定）
            deadline = time.time() + timeout_sec
            posted = False
            while time.time() < deadline:
                btn = page.locator("button[data-e2e='post_video_button']")
                if not btn.count():
                    btn = page.locator("button:has-text('投稿')")
                if btn.count() and btn.first.is_enabled():
                    btn.first.click()
                    posted = True
                    break
                time.sleep(3)
            if not posted:
                raise RuntimeError("投稿ボタンが有効になりませんでした")
            time.sleep(8)
            return "https://www.tiktok.com/tiktokstudio/content"
        except Exception as e:
            shot = _shot(page, "fail")
            raise RuntimeError(f"TikTokアップロード失敗: {e}（スクショ: {shot}）") from e
        finally:
            page.close()
