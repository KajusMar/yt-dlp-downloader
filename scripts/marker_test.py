import os
try:
    open(r"C:\Users\Kay\launch_marker.txt", "w").write("LAUNCHED")
except Exception as e:
    open(r"C:\Users\Kay\launch_marker_err.txt", "w").write(str(e))
import sys, time
sys.stdout.buffer.write(b"\x05\x00\x00\x00hello")
sys.stdout.buffer.flush()
time.sleep(3)
