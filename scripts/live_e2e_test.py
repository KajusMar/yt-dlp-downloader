"""
End-to-end test in LIVE Floorp via the REAL extension path:
content-script hook window.ytdlpDetector.download -> background -> native host.
We navigate a tab to the YouTube page (content script injected), then call
the detector's download() from page context. Confirms the file lands.
"""
import socket, json, time, os, glob

PROFILE = r"C:\Users\Kay\AppData\Roaming\Floorp\Profiles\16sprtbv.default-release"
PORT = int(open(os.path.join(PROFILE, "MarionetteActivePort")).read().strip())
TEST_URL = "https://youtu.be/aqz-KE-bpKQ"
DOWNLOAD_DIR = os.path.expanduser("~/Videos/yt-dlp")

def send(s, obj):
    msg = json.dumps(obj).encode()
    s.sendall(b"%d\n" % len(msg) + msg)
    buf = b""
    while b"\n" not in buf:
        buf += s.recv(8192)
    n = int(buf[:buf.index(b"\n")]); buf = buf[buf.index(b"\n")+1:]
    while len(buf) < n:
        buf += s.recv(8192)
    return json.loads(buf[:n].decode())

s = socket.create_connection(("127.0.0.1", PORT), timeout=10)
# Read Marionette's initial greeting frame before sending anything.
def recv_frame(s):
    buf = b""
    while b"\n" not in buf:
        buf += s.recv(8192)
    n = int(buf[:buf.index(b"\n")]); buf = buf[buf.index(b"\n")+1:]
    while len(buf) < n:
        buf += s.recv(8192)
    return json.loads(buf[:n].decode())

greeting = recv_frame(s)   # {"marionetteProtocol": 3, ...}
print("greeting:", json.dumps(greeting)[:120])
send(s, {"to": "root", "type": "marionette:newSession", "name": "e2e"})

# Open a tab to the video page and wait for content script injection.
tab = send(s, {"to": "root", "type": "AddTab", "url": TEST_URL})
print("tab:", json.dumps(tab.get("value", tab))[:120])
time.sleep(5)

# Use the content script's postMessage bridge (window.__yt_dlp_e2e) which
# forwards to the background -> native host (the REAL extension path).
script = """
var callback = arguments[arguments.length - 1];
var token = 'e2e_' + Date.now();
var done = false;
window.addEventListener('message', function(ev){
  var d = ev.data || {};
  if (d.__yt_dlp_e2e_result && d.token === token && !done){
    done = true; callback({ok:true, result:d.result});
  }
});
window.postMessage({
  __yt_dlp_e2e: true, token: token,
  message: {type:'DOWNLOAD_VIDEO', payload:{url:'__URL__', options:{format:'bestaudio', extractAudio:true}}}
}, '*');
setTimeout(function(){ if(!done) callback({ok:false, error:'no response from extension'}); }, 20000);
""".replace("__URL__", TEST_URL)

r = send(s, {"to": "root", "type": "executeAsyncScript", "script": script, "args": [], "timeout": 25000})
print("trigger:", json.dumps(r.get("value", r))[:250])

print("Watching download dir for 70s...")
before = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*aqz-KE-bpKQ*")))
done = False
for i in range(14):
    time.sleep(5)
    now = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*aqz-KE-bpKQ*")))
    new = now - before
    if new:
        f = max(new, key=os.path.getsize)
        sz = os.path.getsize(f)
        print(f"t={(i+1)*5}s -> {sz} bytes {'DONE' if sz>9_000_000 else 'downloading'}")
        if sz > 9_000_000:
            done = True
            break
    else:
        print(f"t={(i+1)*5}s -> no file yet")
s.close()
print("E2E DONE" if done else "E2E INCOMPLETE")

