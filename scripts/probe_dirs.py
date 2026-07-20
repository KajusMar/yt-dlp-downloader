import os, re, json, time, shutil
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

FLOORP = r"C:\Program Files\Ablaze Floorp\floorp.exe"
GECKO = r"C:\Users\Kay\.hermes_ppx\geckodriver.exe"
XPI = r"C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi"
ADDON_ID = "yt-dlp-downloader@kajusmar.com"
PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\e2e-path"

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
    time.sleep(10)
    info = driver.execute_async_script("""
        const cb = arguments[arguments.length-1];
        (async () => {
            try {
                const { Services } = ChromeUtils.import("resource://gre/modules/Services.jsm");
                const dirs = {};
                for (const k of ["XREAppDist","ULoc","DfltDcnts","ProfD","DefRt","CurWorkD","ProgF"]) {
                    try { dirs[k] = Services.dirsvc.get(k, Ci.nsIFile).path; } catch(e) { dirs[k] = "ERR:"+e; }
                }
                const appDir = Services.dirsvc.get("XREAppDist", Ci.nsIFile);
                // Firefox joins this with "NativeMessagingHosts"
                const nm = appDir.clone(); nm.append("NativeMessagingHosts");
                dirs["NM_APP"] = nm.path;
                const prof = Services.dirsvc.get("ProfD", Ci.nsIFile);
                const nm2 = prof.clone(); nm2.append("NativeMessagingHosts");
                dirs["NM_PROFILE"] = nm2.path;
                // Also try the AppData/Roaming based path via Services.dirsvc "UAppData"
                try { dirs["UAppData"] = Services.dirsvc.get("UAppData", Ci.nsIFile).path; } catch(e){ dirs["UAppData"]="ERR"; }
                cb(dirs);
            } catch (e) { cb({error:String(e)}); }
        })();
    """)
    print("DIRS:", json.dumps(info, indent=2))
finally:
    driver.quit()
print("DONE")
