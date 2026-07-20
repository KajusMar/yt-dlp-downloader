#!/usr/bin/env python3
"""
In-browser end-to-end test for the yt-dlp extension.

Strategy: content scripts do NOT inject in headless Floorp (proven with a
trivial test extension), but the EXTENSION PAGE (popup.html) is a real WebExtension
context where `browser` is a global. So we:
  1. Permanently install the built XPI into an isolated profile.
  2. Launch Floorp headless, let it assign a moz-extension UUID.
  3. Read the UUID from prefs.js (extensions.webextensions.uuids).
  4. Open moz-extension://<uuid>/popup/popup.html in a tab.
  5. From that extension page, call browser.runtime.sendMessage for
     CHECK_HEALTH, GET_VIDEO_INFO and DOWNLOAD_VIDEO (the exact API the
     popup UI uses) -> exercises background.js -> connectNative -> host.py -> yt-dlp.
  6. Confirm a real .mp3 lands in ~/Videos/yt-dlp.

This verifies the full browser integration (extension <-> native host) without
depending on content-script injection.
"""
import os, re, time, glob, shutil, json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
TEST_VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-browser"
STATE_FILE = r"C:\Users\Kay\yt-dlp-downloader\E2E_STATE.json"


def log(*a):
    print("[E2E]", *a)


def load_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {}


def save_state(s):
    json.dump(s, open(STATE_FILE, "w"))


def get_uuid(profile):
    """Extract the moz-extension UUID for our addon from prefs.js."""
    prefs = os.path.join(profile, "prefs.js")
    if not os.path.exists(prefs):
        return None
    txt = open(prefs, encoding="utf-8", errors="ignore").read()
    m = re.search(r'extensions\.webextensions\.uuids",\s*"(.*)"\);', txt)
    if not m:
        return None
    try:
        val = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
        mapping = json.loads(val)
        return mapping.get(ADDON_ID)
    except Exception:
        return None


def main():
    state = load_state()
    if os.path.exists(PROFILE):
        shutil.rmtree(PROFILE)
    os.makedirs(PROFILE, exist_ok=True)
    ext_dir = os.path.join(PROFILE, "extensions")
    os.makedirs(ext_dir, exist_ok=True)
    shutil.copy(XPI, os.path.join(ext_dir, ADDON_ID + ".xpi"))

    opts = Options()
    opts.binary_location = FLOORP
    opts.add_argument("-profile"); opts.add_argument(PROFILE)
    opts.add_argument("--headless")
    opts.set_preference("xpinstall.signatures.required", False)

    driver = webdriver.Firefox(service=Service(GECKO), options=opts)
    try:
        time.sleep(12)  # let addon manager assign UUID + write prefs.js

        uuid = get_uuid(PROFILE)
        log("moz-extension UUID:", uuid)
        assert uuid, "could not determine extension UUID from prefs.js"
        save_state({"uuid": uuid})

        popup_url = f"moz-extension://{uuid}/popup/popup.html"
        driver.get(popup_url)
        time.sleep(5)
        assert "yt-dlp" in driver.page_source.lower() or "YouTube" in driver.page_source, "popup page did not load"
        log("popup page loaded:", popup_url)

        def ext_call(message, timeout=90000):
            return driver.execute_async_script("""
                const cb = arguments[arguments.length-1];
                const message = arguments[0];
                const t = arguments[1] || 90000;
                const done = (res) => { clearTimeout(to); cb(res); };
                const to = setTimeout(() => done({error:'TIMEOUT'}), t);
                browser.runtime.sendMessage(message).then(done).catch(e => done({error:String(e)}));
            """, message, timeout)

        # 1) Health (background -> connectNative -> host health_check)
        res = ext_call({"type": "CHECK_HEALTH"})
        log("CHECK_HEALTH:", res)
        assert res.get("success") and res["data"]["status"] == "ok", res
        log(">>> NATIVE HOST CONNECTED inside real browser:", res["data"]["yt_dlp_version"])

        # 2) Info
        res = ext_call({"type": "GET_VIDEO_INFO", "payload": {"url": TEST_VIDEO}})
        log("GET_VIDEO_INFO:", (res.get("data") or {}).get("title"), "| err:", res.get("error"))
        # info is best-effort; don't hard-fail

        # 3) Real download
        res = ext_call({
            "type": "DOWNLOAD_VIDEO",
            "payload": {"url": TEST_VIDEO, "options": {"format": "bestaudio", "extractAudio": True, "audioFormat": "mp3"}}
        }, timeout=120000)
        log("DOWNLOAD_VIDEO ack:", res)
        assert res.get("success"), res
        log("requestId:", res["data"].get("requestId"))

        # 4) Wait for file on disk
        found = None
        for _ in range(120):
            mp3s = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3"))
            if mp3s:
                found = max(mp3s, key=os.path.getmtime); break
            time.sleep(1)
        assert found, "no mp3 downloaded within timeout"
        size = os.path.getsize(found)
        log(">>> DOWNLOADED IN-BROWSER:", found, f"({size} bytes)")
        assert size > 1000, "file too small"
        save_state({"uuid": uuid, "in_browser_download": "PASS", "file": found})
        log("=== E2E BROWSER PASS ===")
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    main()
    print("DONE")
