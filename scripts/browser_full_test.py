import os, re, json, time, glob, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
TEST_VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-full"

for mp3 in glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3")):
    os.remove(mp3)
if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE)
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

opts = Options()
opts.binary_location = FLOORP
opts.add_argument("-profile"); opts.add_argument(PROFILE)
opts.add_argument("--headless")
opts.set_preference("xpinstall.signatures.required", False)

driver = webdriver.Firefox(service=Service(GECKO), options=opts)
try:
    time.sleep(12)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    m = re.search(r'webextensions\.uuids",\s*"(.*)"\);', line)
    uuid = json.loads(m.group(1).replace('\\"', '"').replace("\\\\", "\\")).get(ADDON_ID)
    print("UUID:", uuid)

    # Open the popup page (a real extension context with `browser` available)
    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(4)
    assert "yt-dlp" in driver.page_source.lower(), "popup did not render"

    def ext_call(message, timeout=120000):
        return driver.execute_async_script("""
            const cb = arguments[arguments.length-1];
            const message = arguments[0];
            const t = arguments[1] || 120000;
            const to = setTimeout(() => cb({error:'TIMEOUT'}), t);
            browser.runtime.sendMessage(message).then(r => { clearTimeout(to); cb(r); })
                .catch(e => { clearTimeout(to); cb({error:String(e)}); });
        """, message, timeout)

    res = ext_call({"type": "CHECK_HEALTH"})
    print("CHECK_HEALTH:", res)

    res = ext_call({"type": "DOWNLOAD_VIDEO", "payload": {
        "url": TEST_VIDEO,
        "options": {"format": "bestaudio", "extractAudio": True, "audioFormat": "mp3"}
    }}, timeout=150000)
    print("DOWNLOAD ack:", res)
    rid = (res.get("data") or {}).get("requestId")
    print("requestId:", rid)

    found = None
    for _ in range(150):
        mp3s = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3"))
        if mp3s:
            found = max(mp3s, key=os.path.getmtime)
            break
        time.sleep(1)
    if found:
        print("IN-BROWSER DOWNLOAD OK:", found, os.path.getsize(found), "bytes")
    else:
        print("IN-BROWSER DOWNLOAD FAILED: no file")
    print("CHECK_HEALTH again:", ext_call({"type": "CHECK_HEALTH"}))
    time.sleep(2)
    try:
        logs = driver.get_log("browser")
        print("=== CONSOLE LOGS ===")
        for l in logs[-30:]:
            print(l.get("level"), l.get("message")[:200])
    except Exception as e:
        print("no console:", e)
finally:
    driver.quit()
print("DONE")
