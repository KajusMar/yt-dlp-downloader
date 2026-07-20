import glob, os, shutil, json

P = r'C:\Users\Kay\AppData\Roaming\Floorp\Profiles\16sprtbv.default-release'
ext_dir = os.path.join(P, 'extensions')
os.makedirs(ext_dir, exist_ok=True)
dst = os.path.join(ext_dir, 'yt-dlp-downloader@kajusmar.com.xpi')
shutil.copy(r'C:\Users\Kay\yt-dlp-downloader\dist\yt-dlp-downloader.xpi', dst)
print('copied:', os.path.getsize(dst))

ej = glob.glob(os.path.join(P, 'extensions.json'))[0]
d = json.load(open(ej))
addons = [a for a in d.get('addons', []) if a.get('id') != 'yt-dlp-downloader@kajusmar.com']
addons.append({
    'id': 'yt-dlp-downloader@kajusmar.com', 'version': '1.0.2', 'type': 'extension',
    'loader': None, 'manifestVersion': 2, 'visible': True, 'active': True,
    'userDisabled': False, 'appDisabled': False, 'embedderDisabled': False,
    'softDisabled': False, 'foreignInstall': False, 'strictCompatibility': True,
    'path': dst.replace('/', '\\'),
    'defaultLocale': {'name': 'yt-dlp Video Downloader', 'description': 'Download videos from YouTube and 1000+ sites using yt-dlp. No quality limits, no ads, open source.', 'creator': 'Kay'}
})
d['addons'] = addons
json.dump(d, open(ej, 'w'), indent=2)
print('extensions.json updated')