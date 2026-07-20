import glob, os, socket, json, time, sys

P = glob.glob(r'C:\Users\Kay\AppData\Roaming\Floorp\Profiles\16sprtbv*')[0]
port = int(open(glob.glob(os.path.join(P, 'MarionetteActivePort'))[0]).read().strip())
xpi_path = os.path.abspath('dist/yt-dlp-downloader.xpi')
print('port', port, 'xpi', xpi_path, file=sys.stderr, flush=True)

s = socket.create_connection(('127.0.0.1', port), timeout=30)
s.settimeout(30)
buf = b''

def read_frame():
    global buf
    while True:
        idx = buf.find(b':')
        if idx == -1:
            buf += s.recv(65536); continue
        try:
            length = int(buf[:idx])
        except ValueError:
            buf = buf[idx+1:]; continue
        if len(buf) < idx+1+length:
            buf += s.recv(65536); continue
        payload = buf[idx+1:idx+1+length]; buf = buf[idx+1+length:]
        return json.loads(payload.decode('utf-8'))

def send_frame(obj):
    frame = json.dumps(obj).encode('utf-8')
    s.sendall(str(len(frame)).encode() + b':' + frame)

# 1) welcome
w = read_frame()
print('WELCOME:', w, file=sys.stderr, flush=True)

# 2) Per Marionette v3: client must send a 'WebDriver:NewSession' to root.
cid = 0
def cmd(to, typ, params=None):
    global cid
    cid += 1
    obj = {'to': to, 'type': typ, 'id': cid, 'from': 'client'}
    if params is not None:
        obj['params'] = params
    send_frame(obj)
    return read_frame()

r = cmd('root', 'WebDriver:NewSession', {'capabilities': {}})
print('NEWSSESSION:', r, file=sys.stderr, flush=True)
if r.get('error'):
    # try alternate actor name
    r = cmd('Marionette', 'WebDriver:NewSession', {'capabilities': {}})
    print('NEWSSESSION(Marionette):', r, file=sys.stderr, flush=True)

r = cmd('root', 'Addon:install', {'path': xpi_path, 'temporary': True})
print('ADDON INSTALL:', r, file=sys.stderr, flush=True)
if r.get('error'):
    r = cmd('Marionette', 'Addon:install', {'path': xpi_path, 'temporary': True})
    print('ADDON INSTALL(Marionette):', r, file=sys.stderr, flush=True)

# Print final result to stdout for parsing
print('RESULT:' + json.dumps({'newSession': not bool(r.get('error')) if 'WebDriver' in str(r) else None, 'install': r.get('error') or 'OK', 'detail': str(r.get('result'))[:200]}))
s.close()
