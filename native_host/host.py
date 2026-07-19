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
            result = subprocess.run(
                [sys.executable, '-m', 'yt_dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=10
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
            cmd = [
                sys.executable, '-m', 'yt_dlp',
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
    
    def run_download(self, request_id, url, options):
        """Run download in a thread"""
        try:
            output_dir = options.get('outputDir', DOWNLOAD_DIR)
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Build yt-dlp command
            cmd = [sys.executable, '-m', 'yt_dlp']
            
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
                '--newline',  # Progress on newlines
                '--progress-template', 'download:%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s',
                url
            ])
            
            # Add cookies if available
            cookies_file = Path.home() / '.config' / 'yt-dlp' / 'cookies.txt'
            if cookies_file.exists():
                cmd.extend(['--cookies', str(cookies_file)])
            
            self.log(f"Starting download: {' '.join(cmd)}")
            
            # Run with progress tracking
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Track this download
            with self._lock:
                self.pending_downloads[request_id] = proc
            
            # Read output line by line
            for line in proc.stdout:
                with self._lock:
                    if request_id not in self.pending_downloads:
                        # Cancelled
                        proc.terminate()
                        break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse progress
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
                    except:
                        pass
                elif '[download]' in line and '100%' in line:
                    self.send_response(request_id, progress={
                        'percent': 100,
                        'status': 'processing'
                    })
                
                # Log all output
                self.log(line)
            
            # Wait for completion
            proc.wait()
            
            with self._lock:
                self.pending_downloads.pop(request_id, None)
            
            if proc.returncode == 0:
                self.send_response(request_id, {
                    'status': 'completed',
                    'message': 'Download completed successfully'
                })
            else:
                self.send_response(request_id, error=f"Download failed with code {proc.returncode}")
                
        except Exception as e:
            with self._lock:
                self.pending_downloads.pop(request_id, None)
            self.log(f"Download error: {e}")
            self.send_response(request_id, error=str(e))
    
    def handle_download(self, request_id, url, options):
        """Start download in a background thread"""
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