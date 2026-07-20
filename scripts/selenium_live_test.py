"""
Live end-to-end test via Selenium launching Firefox with the real profile
(the extension is already installed as a drop-in XPI there). Drives a real
YouTube download through the extension's content-script postMessage bridge
-> background -> native host, and confirms the file lands.
"""
import time, os, glob
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

PROFILE = r"C:\Users/Kay/AppData/Roaming\Floorp\Profiles\16sprtbv.default-release"
GECKO = r"C:\Users\Kay\yt-dlp-downloader\geckodriver.exe"
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")
TEST_URL = "https://youtu.be/aqz-KE-bpKQ"

opt = Options()
opt.binary_location = r"C:\Program Files\Ablaze Floorp\floorp.exe"
# Use the existing profile (extension installed there). Don't create a fresh one.
opt.add_argument("-profile")
opt.add_argument(PROFILE)
opt.set_preference("marionette", True)

driver = webdriver.Firefox(service=webdriver.FirefoxService(executable_path=GECKO), options=opt)
print("Selenium launched Firefox with real profile")

driver.get(TEST_URL)
time.sleep(6)

# Use the content script's postMessage bridge to trigger a download through
# the REAL extension path (content -> background -> native host).
result = driver.execute_script("""
  return new Promise((resolve) => {
    var token = 'e2e_' + Date.now();
    var done = false;
    window.addEventListener('message', function(ev){
      var d = ev.data || {};
      if (d.__yt_dlp_e2e_result && d.token === token && !done){
        done = true; resolve({ok:true, result:d.result});
      }
    });
    window.postMessage({
      __yt_dlp_e2e: true, token: token,
      message: {type:'DOWNLOAD_VIDEO', payload:{url:'__URL__', options:{format:'bestaudio', extractAudio:true}}}
    }, '*');
    setTimeout(function(){ if(!done) resolve({ok:false, error:'no response from extension'}); }, 25000);
  });
""".replace("__URL__", TEST_URL))
print("trigger:", result)

print("Watching download dir for 70s...")
WATCH = os.path.expanduser("~/Videos/yt-dlp")
before = set(glob.glob(os.path.join(WATCH, "*.mp3"))) | set(glob.glob(os.path.join(os.path.expanduser("~/yt-dlp-downloader/native_host"), "*.mp3")))
done = False
for i in range(14):
    time.sleep(5)
    now = set(glob.glob(os.path.join(WATCH, "*.mp3"))) | set(glob.glob(os.path.join(os.path.expanduser("~/yt-dlp-downloader/native_host"), "*.mp3")))
    new = now - before
    if new:
        f = max(new, key=os.path.getsize)
        sz = os.path.getsize(f)
        print(f"t={(i+1)*5}s -> {os.path.basename(f)} {sz} bytes {'DONE' if sz>9_000_000 else 'downloading'}")
        if sz > 9_000_000:
            done = True; break
    else:
        print(f"t={(i+1)*5}s -> no file yet")
driver.quit()
print("LIVE E2E " + ("PASSED" if done else "FAILED"))
