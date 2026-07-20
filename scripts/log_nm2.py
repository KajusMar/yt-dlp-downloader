import os, re, json, time, shutil, glob
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users/Kay/yt-dlp-downloader/dist/yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-nmlog"

if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE)
os.makedirs(PROFILE, exist_ok=True)
# Force native-messaging logging via user.js (always honored)
with open(os.path.join(PROFILE, "user.js"), "w") as f:
    f.write('user_pref("xpinstall.signatures.required", false);\n')
    f.write('user_pref("logging.config.add_timestamp", true);\n')
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

opts = Options()
opts.binary_location = FLOORP
opts.add_argument("-profile"); opts.add_argument(PROFILE)
opts.add_argument("--headless")
# Route logging to a file in the profile dir
opts.set_preference("logging.NativeMessaging", "Debug")
opts.set_preference("logging.config.LOG_FILE", r"C:\Users\Kay\yt-dlp-downloader\nm2.log")
opts.set_preference("logging.config.add_timestamp", True)

driver = webdriver.Firefox(service=Service(GECKO), options=opts)
try:
    time.sleep(10)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    m = re.search(r'webextensions\.uuids",\s*"(.*)"\);', line)
    uuid = json.loads(m.group(1).replace('\\"', '"').replace("\\\\", "\\")).get(ADDON_ID)
    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(4)
    def ext_call(msg, t=30000):
        return driver.execute_async_script("""
            const cb=arguments[arguments.length-1];const m=arguments[0];const to=setTimeout(()=>cb({error:'TIMEOUT'}),arguments[1]||30000);
            browser.runtime.sendMessage(m).then(r=>{clearTimeout(to);cb(r);}).catch(e=>{clearTimeout(to);cb({error:String(e)});});
        """, msg, t)
    print("CHECK_HEALTH:", ext_call({"type":"CHECK_HEALTH"}))
finally:
    driver.quit()
print("DONE")
