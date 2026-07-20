import os, re, json, time, shutil, subprocess
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-log"

if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE)
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

# Capture native-messaging discovery via MOZ_LOG
env = os.environ.copy()
env["MOZ_LOG"] = "nativeMessaging:5"
env["MOZ_LOG_FILE"] = r"C:\Users\Kay\yt-dlp-downloader\moz_native.log"

opts = Options()
opts.binary_location = FLOORP
opts.add_argument("-profile"); opts.add_argument(PROFILE)
opts.add_argument("--headless")
opts.set_preference("xpinstall.signatures.required", False)

service = Service(GECKO, log_output=r"C:\Users\Kay\yt-dlp-downloader\gecko_native.log")
driver = webdriver.Firefox(service=service, options=opts)
try:
    time.sleep(12)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    m = re.search(r'webextensions\.uuids",\s*"(.*)"\);', line)
    uuid = json.loads(m.group(1).replace('\\"', '"').replace("\\\\", "\\")).get(ADDON_ID)
    print("UUID:", uuid)
    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(4)
    def ext_call(message, timeout=30000):
        return driver.execute_async_script("""
            const cb = arguments[arguments.length-1];
            const message = arguments[0];
            const t = arguments[1] || 30000;
            const to = setTimeout(() => cb({error:'TIMEOUT'}), t);
            browser.runtime.sendMessage(message).then(r => { clearTimeout(to); cb(r); })
                .catch(e => { clearTimeout(to); cb({error:String(e)}); });
        """, message, timeout)
    print("CHECK_HEALTH:", ext_call({"type": "CHECK_HEALTH"}))
finally:
    driver.quit()
print("DONE")
