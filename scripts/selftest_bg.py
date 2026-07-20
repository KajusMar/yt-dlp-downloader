import os, re, json, time, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-selftest"

if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE, ignore_errors=True)
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

def mk():
    o = Options(); o.binary_location = FLOORP
    o.add_argument("-profile"); o.add_argument(PROFILE)
    o.set_preference("xpinstall.signatures.required", False)
    o.set_preference("extensions.autoDisableScopes", 0)
    return webdriver.Firefox(service=Service(GECKO), options=o)

d = mk(); time.sleep(7); d.quit(); time.sleep(2)
driver = mk()
try:
    time.sleep(7)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    uuid = json.loads(re.search(r'webextensions\.uuids",\s*"(.*)"\);', line).group(1).replace('\\"','"').replace("\\\\","\\")).get(ADDON_ID)
    print("UUID:", uuid)
    # Let the background self-test (fires at load+3s) complete
    time.sleep(6)
    res = driver.execute_async_script("""
        const cb = arguments[arguments.length-1];
        try {
            browser.storage.local.get('_selftest').then(r => cb({selftest: r._selftest || 'NO RESULT YET'}));
        } catch(e){ cb({selftest: 'STORAGE ERR '+String(e)}); }
    """)
    print("SELFTEST:", json.dumps(res))
finally:
    driver.quit()
print("DONE")
