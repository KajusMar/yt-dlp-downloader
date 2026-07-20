import os, re, json, time, glob, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-health"

if os.path.exists(PROFILE):
    shutil.rmtree(PROFILE, ignore_errors=True)
os.makedirs(os.path.join(PROFILE, "extensions"), exist_ok=True)
shutil.copy(XPI, os.path.join(PROFILE, "extensions", ADDON_ID + ".xpi"))

def mk():
    o = Options(); o.binary_location = FLOORP
    o.add_argument("-profile"); o.add_argument(PROFILE)
    o.set_preference("xpinstall.signatures.required", False)
    o.set_preference("extensions.autoDisableScopes", 0)
    s = Service(GECKO)
    s.service_args = []
    # Capture Firefox's native-messaging debug output
    os.environ["MOZ_LOG"] = "NativeMessaging:5"
    os.environ["MOZ_LOG_FILE"] = r"C:\Users\Kay\yt-dlp-downloader\nm_firefox.log"
    return webdriver.Firefox(service=s, options=o)

d = mk(); time.sleep(7); d.quit(); time.sleep(2)  # register addon
driver = mk()
try:
    time.sleep(7)
    prefs = open(os.path.join(PROFILE, "prefs.js"), encoding="utf-8", errors="ignore").read()
    line = [l for l in prefs.splitlines() if "webextensions.uuids" in l][0]
    uuid = json.loads(re.search(r'webextensions\.uuids",\s*"(.*)"\);', line).group(1).replace('\\"','"').replace("\\\\","\\")).get(ADDON_ID)
    print("UUID:", uuid)
    driver.get(f"moz-extension://{uuid}/popup/popup.html")
    time.sleep(3)

    # Probe connectNative from the BACKGROUND page context (this is where the
    # real extension calls it from) -- NOT the popup page.
    print("opening background page...")
    driver.get(f"moz-extension://{uuid}/background/background.html")
    # background.html may not exist; fallback: call via the popup's bg channel
    time.sleep(2)
    res = driver.execute_async_script("""
        const cb = arguments[arguments.length-1];
        let done=false; const finish=(o)=>{if(!done){done=true;cb(o);}};
        // Try calling background's connectNative through runtime if exposed.
        // Simplest: reproduce exactly what the extension does from a page that
        // has the extension's CSP/capabilities.
        try {
            const port = browser.runtime.connectNative('com.kajusmar.ytdlp_downloader');
            let got=false;
            port.onMessage.addListener((m)=>{ got=true; finish({ok:true, msg:m}); });
            port.onDisconnect.addListener(()=>{ finish({ok:false, disconnect:true, lastError: browser.runtime.lastError && browser.runtime.lastError.message}); });
            port.postMessage({id:1, command:'health_check'});
            setTimeout(()=>finish({ok:false, timeout:true, got}), 20000);
        } catch(e){ finish({ok:false, threw:String(e)}); }
    """)
    print("connectNative probe (page ctx):", json.dumps(res))
finally:
    driver.quit()
print("DONE")
