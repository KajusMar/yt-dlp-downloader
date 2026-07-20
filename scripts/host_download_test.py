#!/usr/bin/env python3
"""Prove host.py performs a REAL YouTube download via yt-dlp.
Drives the native host protocol directly (no browser needed)."""
import json, struct, subprocess, time, glob, os

HOST = r"C:\Users\Kay\yt-dlp-downloader\native_host\host.bat"
OUT = os.path.expanduser("~/Videos/yt-dlp")
URL = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"  # Big Buck Bunny

proc = subprocess.Popen([HOST], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def send(msg):
    enc = json.dumps(msg).encode("utf-8")
    proc.stdin.write(struct.pack("@I", len(enc)) + enc); proc.stdin.flush()

def recv():
    raw = proc.stdout.read(4)
    if not raw: return None
    n = struct.unpack("@I", raw)[0]
    return json.loads(proc.stdout.read(n).decode("utf-8"))

# started ack
send({"id": 1, "command": "download", "url": URL, "options": {"format": "bestaudio", "extractAudio": True, "audioFormat": "mp3"}})
print("sent download request")
t0 = time.time()
final = None
while time.time() - t0 < 180:
    msg = recv()
    if not msg: break
    res = msg.get("result", {})
    print("progress:", res.get("status"), res.get("progress"), "%", res.get("message", "")[:80])
    if res.get("status") in ("completed", "error"):
        final = res; break
print("FINAL:", final)
files = glob.glob(os.path.join(OUT, "*.mp3"))
if files:
    f = max(files, key=os.path.getmtime)
    print("DOWNLOADED FILE:", f, os.path.getsize(f), "bytes")
else:
    print("NO MP3 FOUND")
proc.terminate()
