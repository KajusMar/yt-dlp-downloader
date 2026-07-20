"""
yt-dlp Video Downloader - Native Messaging Host (Python)
Communicates with browser extension via stdin/stdout (native messaging protocol)
"""

import sys
import os
import json
import struct
import subprocess
import threading
import time
import signal
from pathlib import Path

# Configuration
DOWNLOAD_DIR = os.path.expanduser('~/Videos/yt-dlp')
NATIVE_HOST_NAME = 'com.kajusmar.ytdlp_downloader'

# Ensure download directory exists
Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

class NativeHost:
    def __init__(self):
        self.request_id = 0
        self.pending_downloads = {}
        self.running = True
        self._lock = threading.Lock()
        
    def read_message(self):
        """Read a message from stdin (native messaging protocol)"""
        try:
            # Read 4 bytes for length
            raw_length = sys.stdin.buffer.read(4)
            if not raw_length:
                return None
            length = struct.unpack('@I', raw_length)[0]
            
            # Read the message
            message = sys.stdin.buffer.read(length).decode('utf-8')
            return json.loads(message)
        except Exception as e:
            self.log(f"Read error: {e}")
            return None
    
    def write_message(self, message):
        """Write a message to stdout (native messaging protocol)"""
        try:
            encoded = json.dumps(message).encode('utf-8')
            length = struct.pack('@I', len(encoded))
            sys.stdout.buffer.write(length)
            sys.stdout.buffer.write(encoded)
            sys.stdout.buffer.flush()
        except Exception as e:
            self.log(f"Write error: {e}")
    
    def log(self, msg):
        """Log to stderr (visible in browser console)"""
        print(f"[yt-dlp-host] {msg}", file=sys.stderr, flush=True)
    
    def send_response(self, request_id, result=None, error=None, progress=None):
        """Send response back to extension"""
        msg = {'id': request_id}
        if progress is not None:
            msg['progress'] = progress
        elif error:
            msg['error'] = error
        else:
            msg['result'] = result
        self.write_message(msg)
    
    def check_ffmpeg(self):
        """Check if ffmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def handle_health_check(self, request_id):
        """Check if yt-dlp is available"""
        try:
            py = self._yt_dlp_python()
            result = subprocess.run(
                [py, '-m', 'yt_dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.send_response(request_id, {
                    'status': 'ok',
                    'yt_dlp_version': version,
                    'download_dir': DOWNLOAD_DIR,
                    'ffmpeg_available': self.check_ffmpeg()
                })
            else:
                self.send_response(request_id, error=f"yt-dlp error: {result.stderr}")
        except Exception as e:
            self.send_response(request_id, error=str(e))
    
    def handle_get_info(self, request_id, url):
        """Get video info without downloading"""
        try:
            py = self._yt_dlp_python()
            cmd = [
                py, '-m', 'yt_dlp',
                '--dump-json',
                '--no-download',
                '--no-warnings',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                info = json.loads(result.stdout.strip())
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                self.send_response(request_id, {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'thumbnail': info.get('thumbnail'),
                    'webpage_url': info.get('webpage_url'),
                    'formats_count': len(formats),
                    'video_formats': len(video_formats),
                    'audio_formats': len(audio_formats),
                    'available_qualities': sorted(set(
                        f.get('height') for f in video_formats if f.get('height')
                    ), reverse=True)
                })
            else:
                self.send_response(request_id, error=f"yt-dlp error: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.send_response(request_id, error="Timeout getting video info")
        except Exception as e:
            self.send_response(request_id, error=str(e))
    
    def _yt_dlp_python(self):
        """Find a python interpreter that actually has yt-dlp installed.

        When bundled as a PyInstaller .exe, sys.executable IS host.exe, which
        would 'accept' any args and produce a malformed yt-dlp command. So we
        NEVER return our own executable; we probe real python launchers and the
        known uv interpreter, and cache the winner."""
        if getattr(self, '_cached_py', None):
            return self._cached_py
        exe = os.path.realpath(sys.executable).lower()
        candidates = ['python', 'py', 'python3']
        uv_py = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                             'uv', 'python', 'cpython-3.11-windows-x86_64-none', 'python.exe')
        candidates.append(uv_py)
        # Only trust sys.executable if we are NOT frozen (i.e. real python).
        if not getattr(sys, 'frozen', False):
            candidates.append(sys.executable)
        for cand in candidates:
            try:
                c = os.path.realpath(cand).lower() if os.path.exists(cand) else cand.lower()
                if c == exe:
                    continue  # never use our own executable as the yt-dlp runner
                r = subprocess.run(
                    [cand, '-c', 'import yt_dlp'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
                if r.returncode == 0:
                    self._cached_py = cand
                    return cand
            except Exception:
                continue
        # Last resort: plain python on PATH
        self._cached_py = 'python'
        return 'python'

    def run_download(self, request_id, url, options):
        """Run download in a thread"""
        try:
            # Resolve output dir: prefer explicit outputDir, else DOWNLOAD_DIR,
            # else a sane default. Guard against empty/invalid values so the
            # file never lands in host.exe's CWD by accident.
            output_dir = options.get('outputDir') or DOWNLOAD_DIR or os.path.join(os.path.expanduser('~'), 'Videos', 'yt-dlp')
            output_dir = os.path.abspath(os.path.expanduser(output_dir))
            if not output_dir or output_dir.strip() in ('', '.'):
                output_dir = os.path.join(os.path.expanduser('~'), 'Videos', 'yt-dlp')
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Pick a python that has yt-dlp
            py = self._yt_dlp_python()
            if py == sys.executable:
                self.log("WARNING: using sys.executable for yt-dlp; yt-dlp may be missing")
            
            # Build yt-dlp command
            cmd = [py, '-m', 'yt_dlp']
            
            # Format selection
            fmt = options.get('format', 'bestvideo[height<=1080]+bestaudio/best[height<=1080]')
            cmd.extend(['-f', fmt])
            
            # Audio extraction
            if options.get('extractAudio'):
                cmd.extend(['-x', '--audio-format', options.get('audioFormat', 'mp3')])
            
            # Output template
            output_template = os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s')
            cmd.extend(['-o', output_template])
            
            # Other options
            cmd.extend([
                '--no-warnings',
                '--progress-template', 'download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s',
                url
            ])
            
            # Add cookies if available
            cookies_file = Path.home() / '.config' / 'yt-dlp' / 'cookies.txt'
            if cookies_file.exists():
                cmd.extend(['--cookies', str(cookies_file)])
            
            self.log(f"Starting download: {' '.join(cmd)}")

            # Run with progress tracking.
            # IMPORTANT: give the child its own stdin (DEVNULL) so it does NOT
            # inherit host.py's native-messaging stdin pipe. If it inherited it,
            # closing that pipe (e.g. when the client disconnects) would SIGTERM
            # the child and the download would die with code 143.
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            
            # Register so cancel works; do this BEFORE the read loop.
            with self._lock:
                self.pending_downloads[request_id] = proc

            # Read output as bytes and split on BOTH \r and \n. yt-dlp progress
            # lines may use bare \r (when --newline is absent it uses \r for
            # in-place updates), and Python's text-mode "for line in stream"
            # only splits on \n, which would block until a \n arrives.
            output_file = None
            buf = b''
            cancelled = False
            while True:
                with self._lock:
                    if request_id not in self.pending_downloads:
                        cancelled = True
                        proc.terminate()
                        break
                chunk = proc.stdout.read(1)
                if not chunk:
                    break
                if chunk in (b'\r', b'\n'):
                    if buf:
                        line = buf.decode('utf-8', errors='replace').strip()
                        buf = b''
                        if 'Destination:' in line:
                            output_file = line.split('Destination:', 1)[1].strip()
                        if line.startswith('download:'):
                            try:
                                parts = line[9:].split('|')
                                if len(parts) >= 3:
                                    percent = parts[0].strip().replace('%', '')
                                    speed = parts[1].strip()
                                    eta = parts[2].strip()
                                    self.send_response(request_id, progress={
                                        'percent': float(percent) if percent != 'N/A' else 0,
                                        'speed': speed,
                                        'eta': eta,
                                        'status': 'downloading'
                                    })
                            except Exception:
                                pass
                        elif '[download]' in line and '100%' in line:
                            self.send_response(request_id, progress={'percent': 100, 'status': 'processing'})
                        self.log(line)
                else:
                    buf += chunk

            # Child stdout hit EOF; ensure the process has fully exited and
            # its return code is available (proc.returncode can be None until wait()).
            try:
                proc.wait(timeout=30)
            except Exception:
                proc.kill()
                proc.wait()

            with self._lock:
                self.pending_downloads.pop(request_id, None)

            if cancelled:
                self.send_response(request_id, {'status': 'cancelled'})
            elif proc.returncode == 0:
                self.send_response(request_id, {
                    'status': 'completed',
                    'message': 'Download completed successfully',
                    'file': output_file
                })
            else:
                self.send_response(request_id, error=f"Download failed with code {proc.returncode}")
                
        except Exception as e:
            with self._lock:
                self.pending_downloads.pop(request_id, None)
            self.log(f"Download error: {e}")
            self.send_response(request_id, error=str(e))
    
    def handle_download(self, request_id, url, options):
        """Acknowledge immediately, then run download in a background thread"""
        # Immediate ack so the extension can register/show this download by requestId
        self.send_response(request_id, result={
            'status': 'started',
            'requestId': request_id,
            'message': 'Download started'
        })
        thread = threading.Thread(
            target=self.run_download,
            args=(request_id, url, options),
            daemon=True
        )
        thread.start()
    
    def handle_open_folder(self, request_id, dir_path):
        """Open download folder in file explorer"""
        try:
            target = dir_path or DOWNLOAD_DIR
            Path(target).mkdir(parents=True, exist_ok=True)
            
            if sys.platform == 'win32':
                os.startfile(target)
            elif sys.platform == 'darwin':
                subprocess.run(['open', target])
            else:
                subprocess.run(['xdg-open', target])
            
            self.send_response(request_id, {'status': 'opened', 'path': target})
        except Exception as e:
            self.send_response(request_id, error=str(e))
    
    def handle_cancel(self, request_id):
        """Cancel a download"""
        with self._lock:
            if request_id in self.pending_downloads:
                proc = self.pending_downloads[request_id]
                proc.terminate()
                del self.pending_downloads[request_id]
                self.send_response(request_id, {'status': 'cancelled'})
            else:
                self.send_response(request_id, error='No active download to cancel')
    
    def process_message(self, msg):
        """Process incoming message"""
        if not msg or 'id' not in msg:
            return
        
        request_id = msg['id']
        command = msg.get('command')
        
        if command == 'health_check':
            self.handle_health_check(request_id)
        elif command == 'get_info':
            self.handle_get_info(request_id, msg.get('url', ''))
        elif command == 'download':
            self.handle_download(request_id, msg.get('url', ''), msg.get('options', {}))
        elif command == 'open_folder':
            self.handle_open_folder(request_id, msg.get('dir', ''))
        elif command == 'cancel':
            self.handle_cancel(request_id)
        else:
            self.send_response(request_id, error=f"Unknown command: {command}")
    
    def run(self):
        """Main loop"""
        self.log("Native host started")
        
        while self.running:
            msg = self.read_message()
            if msg is None:
                break
            self.process_message(msg)
        
        self.log("Native host stopped")


def main():
    # Handle signals gracefully
    def signal_handler(sig, frame):
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    host = NativeHost()
    host.run()


if __name__ == '__main__':
    main()