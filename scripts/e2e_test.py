#!/usr/bin/env python3
"""End-to-end test of the yt-dlp extension in an isolated Floorp profile.
- Installs the freshly built XPI from dist/
- Opens a real YouTube video
- Verifies the extension connects to the native host (health check)
- Triggers a real download via the native host and confirms a file lands
"""
import os, sys, time, json, struct, glob, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
TEST_VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"  # Big Buck Bunny (short-ish, public)
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")

# Fresh isolated profile each run
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-test"

def log(*a):
    print("[TEST]", *a)

def main():
    if os.path.exists(PROFILE):
        shutil.rmtree(PROFILE)
    os.makedirs(PROFILE, exist_ok=True)

    opts = Options()
    opts.binary_location = FLOORP
    opts.add_argument("-profile")
    opts.add_argument(PROFILE)
    opts.add_argument("--headless")
    opts.set_preference("xpinstall.signatures.required", False)
    opts.set_preference("extensions.autoDisableScopes", 0)

    driver = webdriver.Firefox(service=Service(GECKO), options=opts)
    try:
        log("driver started")
        driver.install_addon(XPI, temporary=True)
        log("XPI installed")
        time.sleep(3)

        # Confirm extension is present
        driver.get("about:addons")
        time.sleep(3)
        assert "yt-dlp" in driver.page_source.lower(), "extension not visible in about:addons"
        log("extension visible in about:addons")

        # Find the addon's internal UUID from the profile so we can open its
        # extension page (where `browser` is available)
        import json as _json
        ext_json = os.path.join(PROFILE, "extensions.json")
        uuid = None
        with open(ext_json, encoding="utf-8") as f:
            data = _json.load(f)
        for addon in data.get("addons", []):
            if addon.get("id") == "yt-dlp-downloader@kajusmar.com":
                uuid = addon.get("instanceId") or addon.get("id")
                break
        log("extension instanceId:", uuid)

        # Open the popup page as a tab -> `browser` is available there
        popup_url = f"moz-extension://{uuid}/popup/popup.html"
        driver.get(popup_url)
        time.sleep(4)

        # 1) Health check through the extension -> native host
        result = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            browser.runtime.sendMessage({type:'CHECK_HEALTH'}).then(r => cb(r)).catch(e => cb({error:String(e)}));
        """)
        log("CHECK_HEALTH result:", result)
        assert result.get("success") and result["data"]["status"] == "ok", result
        log("NATIVE HOST CONNECTED via extension -> " + result["data"]["yt_dlp_version"])

        # 2) Open a real YouTube video tab, then download via the popup page context
        driver.execute_script("window.open(arguments[0], '_blank');", TEST_VIDEO)
        time.sleep(6)

        # 3) Trigger a real download (audio-only mp3 = small + fast) using the video URL
        result = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            const url = arguments[0];
            browser.runtime.sendMessage({
              type:'DOWNLOAD_VIDEO',
              payload:{ url: url, options:{ format:'bestaudio', extractAudio:true, audioFormat:'mp3' } }
            }).then(r => cb(r)).catch(e => cb({error:String(e)}));
        """, TEST_VIDEO)
        log("DOWNLOAD_VIDEO ack:", result)
        assert result.get("success"), result
        req_id = result["data"].get("requestId")
        log("download requestId:", req_id)

        # 3) Wait for the file to appear on disk
        log("waiting for file in", DOWNLOAD_DIR)
        found = None
        for _ in range(60):  # up to 60s
            files = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
            mp3s = [f for f in files if f.lower().endswith(".mp3")]
            if mp3s:
                found = mp3s[0]
                break
            time.sleep(1)
        assert found, "no mp3 downloaded within timeout"
        size = os.path.getsize(found)
        log("DOWNLOADED:", found, f"({size} bytes)")
        assert size > 1000, "file too small, likely incomplete"
        log("E2E PASS: real YouTube download succeeded")

    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
    print("DONE")
