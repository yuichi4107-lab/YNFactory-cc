#!/usr/bin/env python3
"""
Gemini image generator script.
Generates images using Gemini's image generation capabilities via browser automation.

Usage:
    # Basic usage
    python scripts/run.py image_generator.py --prompt "your prompt here" --output output.png
    python scripts/run.py image_generator.py --prompt "sunset" --output images/sunset.png --show-browser

    # With reference image (NEW!)
    python scripts/run.py image_generator.py --prompt "犬を描いて" --reference-image ref.png --output output.png
"""

import sys
import json
import argparse
import time
from pathlib import Path
from patchright.sync_api import sync_playwright
import base64

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_DIR,
    AUTH_INFO_FILE,
    STATE_FILE,
    OUTPUT_DIR,
    DEFAULT_TIMEOUT,
    GEMINI_URL
)
from browser_utils import BrowserFactory, StealthUtils

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)

def check_authenticated():
    """
    Check if user is authenticated with Google auth cookies.

    Uses STATE_FILE (state.json) as the primary check since it contains
    actual browser cookies. Verifies Google auth cookies exist, not just
    analytics cookies.

    This matches the NotebookLM skill pattern where state.json is the
    source of truth for authentication status.
    """
    # Primary check: state.json with cookies
    if not STATE_FILE.exists():
        return False

    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)

        # Verify we have cookies
        if 'cookies' not in state or len(state['cookies']) == 0:
            return False

        # Check for Google auth cookies specifically
        google_auth_cookie_names = [
            'SID', 'HSID', 'SSID', 'APISID', 'SAPISID',
            '__Secure-1PSID', '__Secure-3PSID',
            '__Secure-1PAPISID', '__Secure-3PAPISID'
        ]
        google_auth_cookies = [c for c in state['cookies']
                               if c['name'] in google_auth_cookie_names]

        if len(google_auth_cookies) < 3:
            print(f"⚠️  Missing Google auth cookies (found {len(google_auth_cookies)}, need 3+)")
            return False

        # Check if state file is not too old (7 days)
        import time
        age_days = (time.time() - STATE_FILE.stat().st_mtime) / 86400
        if age_days > 7:
            print(f"⚠️  Browser state is {age_days:.1f} days old, may need re-authentication")

        return True

    except Exception:
        return False

def generate_image(prompt: str, output_path: str, show_browser: bool = False, timeout: int = 180):
    """
    Generate image using Gemini with persistent browser context.

    Args:
        prompt: Image generation prompt
        output_path: Path to save generated image
        show_browser: Whether to show browser window
        timeout: Maximum wait time in seconds (default: 180)

    Returns:
        bool: True if successful
    """
    ensure_output_dir()

    print(f"🎨 Generating image with prompt: '{prompt}'")
    print(f"   Output: {output_path}")
    print(f"   Max wait time: {timeout}s")

    playwright = None
    context = None

    try:
        playwright = sync_playwright().start()

        # Use persistent context (key improvement!)
        context = BrowserFactory.launch_persistent_context(
            playwright,
            headless=not show_browser
        )

        # Get or create page
        page = context.pages[0] if context.pages else context.new_page()

        # Navigate to Gemini
        print(f"   → Opening Gemini ({GEMINI_URL})...")
        page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait for page to be ready
        page.wait_for_timeout(3000)

        # Check if redirected to sign-in
        if "accounts.google.com" in page.url or "signin" in page.url.lower():
            print("❌ Not authenticated. Run: python scripts/run.py auth_manager.py setup")
            context.close()
            playwright.stop()
            return False

        # Step 1: Find and click "🍌 画像の作成" button (New UI - 2026+)
        # The button is now a suggestion chip below the input field
        print("   → Looking for '画像の作成' button...")

        # First, ensure we're on a fresh chat page (not a conversation)
        if '/app/c' in page.url or '/app/' not in page.url:
            print("   → Navigating to fresh chat...")
            page.goto("https://gemini.google.com/app", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

        image_gen_selectors = [
            # New UI (2026): Suggestion chip below input - full aria-label match
            'button:has-text("🍌 画像の作成")',
            'button:has-text("画像の作成、ボタン")',
            # Partial text match
            'button:has-text("画像の作成")',
            # Role-based selector
            'button[role="button"]:has-text("画像")',
            # Generic text match
            '*:has-text("画像の作成"):visible',
        ]

        image_gen_button = None
        for selector in image_gen_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    for i in range(locator.count()):
                        btn = locator.nth(i)
                        if btn.is_visible():
                            # Check if it's clickable (not just text)
                            bbox = btn.bounding_box()
                            if bbox and bbox['width'] > 50:
                                image_gen_button = btn
                                print(f"   ✓ Found image generation button: {selector}")
                                break
                if image_gen_button:
                    break
            except:
                continue

        if not image_gen_button:
            print("❌ Could not find '画像の作成' button. UI may have changed.")
            print("   Try running with --show-browser to debug")
            context.close()
            playwright.stop()
            return False

        # Click to activate NanoBanana (image generation mode)
        image_gen_button.click()
        page.wait_for_timeout(2000)

        print("   → NanoBanana (画像の作成) activated")

        # Step 3: Find input field (now in NanoBanana mode)
        print("   → Finding input field...")
        input_selectors = [
            'div[contenteditable="true"]',
            'textarea[placeholder*="プロンプト"]',
            'textarea[placeholder*="画像"]',
            'textarea',
            'rich-textarea textarea',
        ]

        input_element = None
        for selector in input_selectors:
            try:
                if page.locator(selector).count() > 0:
                    input_element = page.locator(selector).first
                    if input_element.is_visible():
                        print(f"   ✓ Found input: {selector}")
                        break
            except:
                continue

        if not input_element:
            print("❌ Could not find input field. UI may have changed.")
            print("   Try running with --show-browser to debug")
            context.close()
            playwright.stop()
            return False

        # Type prompt
        print("   → Typing prompt...")
        input_element.click()
        StealthUtils.random_delay(200, 500)
        input_element.fill(prompt)
        page.wait_for_timeout(500)

        # Step 4: Find and click send button
        print("   → Sending request...")
        send_selectors = [
            'button[aria-label*="送信"]',
            'button[aria-label*="Send"]',
            'button:has-text("生成")',
            'button:has-text("Generate")',
            'button[mattooltip*="Send"]',
            'button.send-button',
        ]

        send_button = None
        for selector in send_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    for i in range(locator.count()):
                        btn = locator.nth(i)
                        if btn.is_visible():
                            send_button = btn
                            print(f"   ✓ Found send button: {selector}")
                            break
                if send_button:
                    break
            except:
                continue

        if not send_button:
            # Try Enter key as fallback
            print("   → Send button not found, trying Enter key...")
            input_element.press("Enter")
        else:
            send_button.click()

        # Wait for image generation
        print(f"   → Waiting for image generation (max {timeout}s)...")
        print("      This may take 30-180 seconds...")

        # Try to find generated image (updated selectors for Nano Banana 2)
        image_selectors = [
            'img[src*="lh3.googleusercontent"]',
            'img[src*="googleusercontent"]',
            'img[src*="blob:"]',
            'div[class*="response"] img',
            'model-response img',
            'message-content img',
            'div[data-testid*="image"] img',
            'div[class*="image"] img',
            'div[class*="generated"] img',
            'response-container img',
            'img[alt*="generated"]',
            'img[alt*="image"]',
        ]

        image_found = False
        image_element = None
        start_time = time.time()

        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0 and elapsed > 0:
                print(f"      ... {elapsed}s elapsed")

            # Try JS-based detection for any large image in response area
            try:
                js_result = page.evaluate("""() => {
                    const imgs = [...document.querySelectorAll('img')];
                    for (const img of imgs) {
                        const src = img.src || '';
                        const rect = img.getBoundingClientRect();
                        const isLarge = rect.width > 200 && rect.height > 200;
                        const isVisible = rect.width > 0 && rect.height > 0;
                        const isGenerated = src.includes('googleusercontent') ||
                                           src.includes('blob:') ||
                                           src.startsWith('data:image');
                        if (isLarge && isVisible && isGenerated) {
                            return { found: true, src: src };
                        }
                    }
                    return { found: false };
                }""")
                if js_result and js_result.get('found'):
                    print("   ✓ Image detected via JS scan!")
                    image_found = True
                    # Find the element via Playwright
                    for sel in ['img[src*="googleusercontent"]', 'img[src*="blob:"]']:
                        try:
                            loc = page.locator(sel).first
                            if loc.is_visible():
                                bbox = loc.bounding_box()
                                if bbox and bbox['width'] > 200:
                                    image_element = loc
                                    break
                        except:
                            continue
                    if image_found:
                        break
            except:
                pass

            for selector in image_selectors:
                try:
                    locator = page.locator(selector)
                    count = locator.count()
                    if count > 0:
                        for i in range(count):
                            img = locator.nth(i)
                            if img.is_visible():
                                src = img.get_attribute('src') or ''
                                # Accept googleusercontent, blob, or data URLs
                                if ('googleusercontent' in src or
                                    src.startswith('blob:') or
                                    src.startswith('data:image')):
                                    # Check image size to ensure it's the generated image
                                    bbox = img.bounding_box()
                                    if bbox and bbox['width'] > 200 and bbox['height'] > 200:
                                        print("   ✓ Image generated!")
                                        image_found = True
                                        image_element = img
                                        break
                        if image_found:
                            break
                except:
                    continue

            if image_found:
                break

            # Check for error messages (Japanese and English)
            error_texts = [
                "画像を生成できません",
                "生成できませんでした",
                "申し訳",
                "I cannot help",
                "Unable to generate",
                "Sorry"
            ]
            for error_text in error_texts:
                try:
                    if page.locator(f'text="{error_text}"').count() > 0:
                        print("❌ Gemini declined to generate the image")
                        context.close()
                        playwright.stop()
                        return False
                except:
                    pass

            page.wait_for_timeout(2000)

        if not image_found:
            print(f"❌ Timeout after {timeout}s - image not generated")
            context.close()
            playwright.stop()
            return False

        # Download image
        print("   → Downloading image...")

        try:
            # image_element が None の場合は JS で大きな画像を探す
            if image_element is None:
                print("   → Element not found via locator, trying screenshot fallback...")
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(output_path), full_page=False)
                print(f"\n✓ Image saved via page screenshot: {output_path}")
                context.close()
                playwright.stop()
                return True

            # Get image source
            img_src = image_element.get_attribute("src") or ""

            if img_src.startswith("blob:"):
                # Blob URL: JS経由でbase64に変換して取得
                print("   → Downloading blob URL via JS...")
                b64 = page.evaluate("""async (src) => {
                    const resp = await fetch(src);
                    const buf = await resp.arrayBuffer();
                    const bytes = new Uint8Array(buf);
                    let binary = '';
                    for (const b of bytes) binary += String.fromCharCode(b);
                    return btoa(binary);
                }""", img_src)
                img_bytes = base64.b64decode(b64)
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(img_bytes)

            elif img_src.startswith("data:"):
                # Base64 encoded image
                print("   → Saving base64 image...")
                img_data = img_src.split(",")[1]
                img_bytes = base64.b64decode(img_data)

                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(img_bytes)

            elif img_src.startswith("http"):
                # URL image
                print("   → Downloading from URL...")
                response = page.request.get(img_src)
                img_bytes = response.body()

                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(img_bytes)

            else:
                # Try screenshot as fallback
                print("   → Using screenshot fallback...")
                image_element.screenshot(path=output_path)

            print(f"\n✓ Image saved to: {output_path}")
            context.close()
            playwright.stop()
            return True

        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            print("   → Trying screenshot fallback...")
            try:
                image_element.screenshot(path=output_path)
                print(f"✓ Image saved via screenshot: {output_path}")
                context.close()
                playwright.stop()
                return True
            except Exception as e2:
                print(f"❌ Screenshot also failed: {e2}")
                context.close()
                playwright.stop()
                return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Try running with --show-browser to see what went wrong")
        if context:
            context.close()
        if playwright:
            playwright.stop()
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate images with Gemini")
    parser.add_argument(
        "--prompt",
        required=True,
        help="Image generation prompt"
    )
    parser.add_argument(
        "--output",
        default="output/generated_image.png",
        help="Output file path (default: output/generated_image.png)"
    )
    parser.add_argument(
        "--reference-image",
        help="Reference image path for style extraction (optional)"
    )
    parser.add_argument(
        "--yaml-output",
        help="Save extracted YAML analysis to this path (optional)"
    )
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="Show browser window (useful for debugging)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Maximum wait time in seconds (default: 180)"
    )

    args = parser.parse_args()

    # Check authentication
    if not check_authenticated():
        print("❌ Not authenticated")
        print("   Run: python scripts/run.py auth_manager.py setup")
        return 1

    # Determine final prompt
    final_prompt = args.prompt

    # If reference image is provided, extract style and create optimized prompt
    if args.reference_image:
        print("\n" + "="*60)
        print("📷 Reference image mode enabled")
        print("="*60)

        # Step 1: Extract visual elements from reference image
        from prompt_extractor import extract_visual_prompt
        print("\n[Step 1/3] Extracting visual elements...")

        extract_result = extract_visual_prompt(
            image_path=args.reference_image,
            output_path=args.yaml_output,
            show_browser=args.show_browser,
            timeout=120
        )

        if not extract_result["success"]:
            print(f"❌ Failed to extract from reference image: {extract_result['error']}")
            return 1

        yaml_content = extract_result["yaml"]
        print("   ✓ Visual analysis complete")

        # Step 2: Generate optimized meta-prompt
        from meta_prompt import load_yaml, generate_meta_prompt
        print("\n[Step 2/3] Generating optimized prompt...")

        try:
            yaml_data = load_yaml(yaml_text=yaml_content)
            final_prompt = generate_meta_prompt(yaml_data, args.prompt)
            print(f"   ✓ Optimized prompt: {final_prompt[:100]}...")
        except Exception as e:
            print(f"⚠️  Warning: Could not parse YAML, using original prompt")
            print(f"   Error: {e}")

        print(f"\n[Step 3/3] Generating image...")
        print("="*60 + "\n")

    # Generate image
    success = generate_image(
        prompt=final_prompt,
        output_path=args.output,
        show_browser=args.show_browser,
        timeout=args.timeout
    )

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
