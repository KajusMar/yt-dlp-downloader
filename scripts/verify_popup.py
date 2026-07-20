import os, re, json, time, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-popup"

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
    val = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    uuid = json.loads(val).get(ADDON_ID)
    print("UUID:", uuid)
    for path in ["manifest.json", "popup/popup.html", "popup/popup.js", "background/background.js"]:
        url = f"moz-extension://{uuid}/{path}"
        try:
            driver.get(url)
            src = driver.page_source
            ok = "not found" not in src.lower() and "error" not in src.lower()[:40]
            print(f"[{path}] {'OK' if ok else 'FAIL'} (len={len(src)})")
        except Exception as e:
            print(f"[{path}] EXC {e}")
finally:
    driver.quit()
print("DONE")
