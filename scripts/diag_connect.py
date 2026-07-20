"""
Diagnostic: connect to the LIVE Floorp via Marionette and read the REAL
connectNative error from the yt-dlp background page. This tells us exactly
why the native host fails, instead of guessing with pixel clicks.
"""
import glob, subprocess, time, os, sys
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

PROFILE = glob.glob(r'C:\Users\Kay\AppData\Roaming\Floorp\Profiles\16sprtbv*')[0]
PORT_FILE = glob.glob(os.path.join(PROFILE, 'MarionetteActivePort'))[0]
PORT = open(PORT_FILE).read().strip()
GECKO = r'C:\Users\Kay\.cache\selenium\geckodriver\win64\0.37.0\geckodriver.exe'

# Start geckodriver connecting to existing Floorp
gd = subprocess.Popen(
    [GECKO, '--connect-existing', '--marionette-port', PORT, '--port', '4466'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
time.sleep(4)

o = Options()
o.binary_location = r'C:\Program Files\Ablaze Floorp\floorp.exe'
o.set_preference('marionette.enabled', True)
# Reuse existing profile so we talk to the already-loaded extension
o.add_argument('-profile')
o.add_argument(PROFILE)

try:
    d = webdriver.Firefox(service=Service(executable_path=GECKO, port=4466), options=o)
    print("Connected to Floorp via Marionette")

    # Get the yt-dlp extension's internal UUID by listing addons
    uuids = d.execute_script("""
        return await browser.management.getAll().then(
            addons => addons.filter(a => a.name.includes('yt-dlp')).map(a => a.id)
        );
    """)
    print("yt-dlp extension runtime id(s):", uuids)

    if uuids:
        uid = uuids[0]
        # Open the background page and try connectNative, capture lastError
        result = d.execute_script("""
            const uid = arguments[0];
            return new Promise((resolve) => {
                const bg = browser.extension.getBackgroundPage ? null : null;
                // Try connectNative directly from a content/privileged scope
                try {
                    const port = browser.runtime.connectNative('com.kajusmar.ytdlp_downloader');
                    let done = false;
                    port.onDisconnect.addListener(() => {
                        if (done) return; done = true;
                        resolve({connected:false, error: browser.runtime.lastError ? browser.runtime.lastError.message : 'disconnected-no-error'});
                    });
                    port.onMessage.addListener((m) => {
                        if (done) return; done = true;
                        resolve({connected:true, message:m});
                    });
                    port.postMessage({id:1, command:'health_check'});
                    setTimeout(() => { if(!done){done=true; resolve({connected:false, error:'timeout-no-response'});} }, 8000);
                } catch(e) {
                    resolve({connected:false, error: 'throw: ' + e.message});
                }
            });
        """, uid)
        print("connectNative result:", result)
    else:
        print("yt-dlp extension NOT found in management.getAll()")

    d.quit()
finally:
    gd.terminate()
