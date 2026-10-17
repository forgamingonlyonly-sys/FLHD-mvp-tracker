"""Build index.html for GitHub Pages.
Usage: python3 build/build.py

source.html          the tracker (all pages, styles and logic)
firebase-shim.html   Firebase sign-in, roles, presence; goes into <head>
autodetect.html      Auto-detect (reads kill / Boss Event lines from the shared game window)
discord.html         Discord board and posts
review.html          Admin review list of Auto-detect logs
modloader.html       loads Auto-detect / Discord / review only for the people who use them
scene.html           night scene behind the tracker (dark theme)
updater.html         "new version" bar and version label (gets the build id)
Writes ../index.html, ../version.json and large images to ../assets/."""
import pathlib, time, json
root = pathlib.Path(__file__).resolve().parent
src = (root / 'source.html').read_text()
shim = (root / 'firebase-shim.html').read_text()
icons = ('<link rel="icon" type="image/png" sizes="192x192" href="favicon.png">\n'
         '<link rel="icon" href="favicon.ico" sizes="any">\n'
         '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n')
src = src.replace('</head>', icons + shim + '\n</head>', 1)

build_id = time.strftime('%Y%m%d%H%M%S', time.gmtime())
def add_before_body(html):
    global src
    i = src.rfind('</body>')
    src = src[:i] + html + '\n' + src[i:]
# Auto-detect, Discord and the Admin review list load only for the people who use them:
# their scripts become separate files (assets/mod-*.js, named by content so browsers keep them between updates);
# their styles stay in the page. modloader.html decides who loads what.
import re, base64, hashlib
assets = root.parent / 'assets'
assets.mkdir(exist_ok=True)
LAZY = {'autodetect.html': 'ad', 'discord.html': 'dc', 'review.html': 'rv'}
lazy_code, mod_urls = {}, {}
for name in ['scene.html', 'autodetect.html', 'discord.html', 'review.html', 'modloader.html', 'updater.html']:
    html = (root / name).read_text().replace('__BUILD__', build_id)
    if name in LAZY:
        scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.S)
        assert len(scripts) == 1, name
        lazy_code[LAZY[name]] = scripts[0]
        html = re.sub(r'<script>.*?</script>', '', html, flags=re.S)
    add_before_body(html)

# big built-in images and sounds become separate files, so browsers keep them between updates
def _extract(m):
    kind, data = m.group(1), m.group(2)
    if len(data) < 4000: return m.group(0)
    raw = base64.b64decode(data)
    name = 'img-' + hashlib.sha1(raw).hexdigest()[:10] + '.' + {'svg+xml': 'svg'}.get(kind, kind)
    (assets / name).write_bytes(raw)
    return 'assets/' + name
src = re.sub(r'data:image/([a-z+]+);base64,([A-Za-z0-9+/=]+)', _extract, src)
sfx_made = set()
def _extract_audio(m):
    raw = base64.b64decode(m.group(2))
    name = 'sfx-' + hashlib.sha1(raw).hexdigest()[:10] + '.' + {'mpeg': 'mp3'}.get(m.group(1), m.group(1))
    (assets / name).write_bytes(raw)
    sfx_made.add(name)
    return 'assets/' + name
src = re.sub(r'data:audio/([a-z0-9]+);base64,([A-Za-z0-9+/=]{4000,})', _extract_audio, src)
for f in assets.glob('sfx-*'):                      # sounds no longer in the page
    if f.name not in sfx_made: f.unlink()
# compact the published page: inline <style> and <script> blocks are minified with esbuild
# (build/node_modules: run `npm install` in build/). Without esbuild the page is published as is.
import subprocess, shutil
esb = root / 'node_modules' / '.bin' / 'esbuild'
esb = str(esb) if esb.exists() else shutil.which('esbuild')
def _minify(code, loader):
    r = subprocess.run([esb, '--loader=' + loader, '--minify', '--charset=utf8', '--log-level=error'],
                       input=code.encode(), capture_output=True)
    if r.returncode != 0:
        raise SystemExit('esbuild failed (' + loader + '):\n' + r.stderr.decode()[:2000])
    return r.stdout.decode().rstrip('\n')
if esb:
    before = len(src)
    src = re.sub(r'(<style>)(.*?)(</style>)', lambda m: m.group(1) + _minify(m.group(2), 'css') + m.group(3), src, flags=re.S)
    src = re.sub(r'(<script>)(.*?)(</script>)', lambda m: m.group(1) + _minify(m.group(2), 'js') + m.group(3), src, flags=re.S)
    if '</script' in ''.join(re.findall(r'<script>(.*?)</script>', src, flags=re.S)): raise SystemExit('minified script contains </script')
    print('compacted', before, '->', len(src))
else:
    print('esbuild not found: published without compacting')
# the lazy modules: minify, name by content, and tell the page where they are
for f in assets.glob('mod-*.js'): f.unlink()
for key, code in lazy_code.items():
    js = _minify(code, 'js') if esb else code
    name = 'mod-' + key + '-' + hashlib.sha1(js.encode()).hexdigest()[:10] + '.js'
    (assets / name).write_text(js)
    mod_urls[key] = 'assets/' + name
src = src.replace('__MODS__', json.dumps(mod_urls))
(root.parent / 'version.json').write_text(json.dumps({'build': build_id}))
(root.parent / 'index.html').write_text(src)
print('built', len(src))
