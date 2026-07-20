import os, re, json, time, glob, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-headed"
DOWNLOAD_DIR = os.path.expanduser(r"~\Videos\yt-dlp")
YT_URL = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"  # Big Buck Bunny

# clean slate
for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3")):
    os.remove(f)
if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE, ignore_errors=True)
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
# PERMANENT install: copy XPI into profile/extensions/<id>.xpi
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

def make_driver():
    opts = Options()
    opts.binary_location = FLOORP
    opts.add_argument("-profile"); opts.add_argument(PROFILE)
    # HEADED — no --headless. Headless Floorp does NOT spawn native-messaging hosts.
    opts.set_preference("xpinstall.signatures.required", False)
    opts.set_preference("extensions.autoDisableScopes", 0)
    opts.set_preference("extensions.enabledScopes", 15)
    return webdriver.Firefox(service=Service(GECKO), options=opts)

# First launch registers the permanently-installed addon, then we restart so
# content scripts + background inject cleanly.
d = make_driver(); time.sleep(8); d.quit(); time.sleep(2)

driver = make_driver()
try:
    time.sleep(8)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    m = re.search(r'webextensions\.uuids",\s*"(.*)"\);', line)
    uuid = json.loads(m.group(1).replace('\\"', '"').replace("\\\\", "\\")).get(ADDON_ID)
    print("UUID:", uuid)

    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(4)

    def ext_call(msg, t=180000):
        return driver.execute_async_script("""
            const cb=arguments[arguments.length-1];const m=arguments[0];
            const to=setTimeout(()=>cb({error:'TIMEOUT'}), arguments[1]||180000);
            browser.runtime.sendMessage(m).then(r=>{clearTimeout(to);cb(r);}).catch(e=>{clearTimeout(to);cb({error:String(e)});});
        """, msg, t)

    print("CHECK_HEALTH:", ext_call({"type": "CHECK_HEALTH"}))
    dl = ext_call({"type": "DOWNLOAD", "url": YT_URL, "options": {"format": "bestaudio", "extractAudio": True, "audioFormat": "mp3"}})
    print("DOWNLOAD ack:", dl)

    found = None
    for _ in range(180):
        mp3s = glob.glob(os.path.join(DOWNLOAD_DIR, "*.mp3"))
        if mp3s:
            found = max(mp3s, key=os.path.getmtime)
            # wait for file to stabilize
            s1 = os.path.getsize(found); time.sleep(2); s2 = os.path.getsize(found)
            if s1 == s2 and s1 > 100000:
                break
        time.sleep(1)
    if found and os.path.getsize(found) > 100000:
        print("IN-BROWSER DOWNLOAD OK:", found, os.path.getsize(found), "bytes")
    else:
        print("IN-BROWSER DOWNLOAD FAILED. files:", glob.glob(os.path.join(DOWNLOAD_DIR, "*")))
finally:
    driver.quit()
print("DONE")
