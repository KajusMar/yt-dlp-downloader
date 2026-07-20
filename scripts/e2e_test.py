#!/usr/bin/env python3
"""End-to-end test of the yt-dlp extension in an isolated Floorp profile.
Uses a PERMANENT install (XPI placed in <profile>/extensions/<id>.xpi) so
content scripts actually activate, then drives the extension from the
content-script scope via postMessage and verifies a real download lands.
"""
import os, time, glob, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
TEST_VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-test"

def log(*a):
    print("[TEST]", *a)

def launch(opts):
    return webdriver.Firefox(service=Service(GECKO), options=opts)

def main():
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

    driver = launch(opts)
    try:
        # Permanent install activates on startup; give it a moment.
        time.sleep(4)
        driver.get("about:addons")
        time.sleep(3)
        assert "yt-dlp" in driver.page_source.lower(), "extension not visible"
        log("extension visible in about:addons")

        # Open a real YouTube video; content script should inject.
        driver.get(TEST_VIDEO)
        time.sleep(10)

        marker = driver.execute_script("return document.documentElement.dataset.ytdlpCs || 'NONE';")
        log("content-script marker:", marker)
        assert marker == "loaded", "content script did not inject"

        def ext_call(message, timeout=30000):
            return driver.execute_async_script("""
                const cb = arguments[arguments.length-1];
                const message = arguments[0];
                const token='tok'+Math.random().toString(36).slice(2);
                const h=(ev)=>{const d=ev.data; if(d&&d.__yt_dlp_e2e_result===true&&d.token===token){window.removeEventListener('message',h);cb(d.result);}};
                window.addEventListener('message',h);
                window.postMessage({__yt_dlp_e2e:true,token,message},'*');
                setTimeout(()=>{window.removeEventListener('message',h);cb({error:'NO_REPLY'});}, arguments[1] || 30000);
            """, message, timeout)

        # 1) Health check -> native host
        result = ext_call({ "type": "CHECK_HEALTH" })
        log("CHECK_HEALTH:", result)
        assert result.get("success") and result["data"]["status"] == "ok", result
        log("NATIVE HOST CONNECTED -> " + result["data"]["yt_dlp_version"])

        # 2) Real download (audio-only mp3)
        result = ext_call({ "type": "DOWNLOAD_VIDEO", "payload": {
            "url": TEST_VIDEO,
            "options": { "format": "bestaudio", "extractAudio": True, "audioFormat": "mp3" }
        }}, timeout=30000)
        log("DOWNLOAD_VIDEO ack:", result)
        assert result.get("success"), result
        log("requestId:", result["data"].get("requestId"))

        # 3) Wait for file on disk
        found = None
        for _ in range(120):  # up to 120s
            mp3s = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3"))
            if mp3s:
                found = mp3s[0]; break
            time.sleep(1)
        assert found, "no mp3 downloaded within timeout"
        size = os.path.getsize(found)
        log("DOWNLOADED:", found, f"({size} bytes)")
        assert size > 1000, "file too small"
        log("E2E PASS: real YouTube download succeeded")
    finally:
        try: driver.quit()
        except Exception: pass

if __name__ == "__main__":
    main()
    print("DONE")
