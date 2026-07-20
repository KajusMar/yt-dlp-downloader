import os, re, json, time, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users/Kay/yt-dlp-downloader/dist/yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-realerr"

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
    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(4)
    # Directly attempt connectNative from the extension page and read lastError
    res = driver.execute_async_script("""
        const cb = arguments[arguments.length-1];
        try {
            const port = browser.runtime.connectNative('com.kajusmar.ytdlp_downloader');
            port.onDisconnect.addListener(() => {
                cb({connected:false, lastError: browser.runtime.lastError ? browser.runtime.lastError.message : 'no lastError'});
            });
            port.onMessage.addListener(() => {});
            // give it a moment; if connect succeeded, lastError stays null
            setTimeout(() => {
                const le = browser.runtime.lastError ? browser.runtime.lastError.message : null;
                cb({connected: true, lastError: le});
            }, 1500);
        } catch (e) {
            cb({threw: String(e), lastError: browser.runtime.lastError ? browser.runtime.lastError.message : null});
        }
    """)
    print("connectNative result:", json.dumps(res, indent=2))
finally:
    driver.quit()
print("DONE")
