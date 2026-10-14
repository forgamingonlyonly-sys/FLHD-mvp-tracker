"""Build index.html for GitHub Pages: tracker source + Firebase bridge.
Usage: python3 build/build.py   (reads build/source.html, writes index.html)"""
import pathlib
root = pathlib.Path(__file__).resolve().parent
src = (root / 'source.html').read_text()
shim = (root / 'firebase-shim.html').read_text()
imp = root / 'import.json'
if imp.exists():
    shim = '<script>window.FALSEHOOD_IMPORT = ' + imp.read_text().replace('</', '<\\/') + ';</script>\n' + shim
icons = '<link rel="icon" type="image/png" sizes="192x192" href="favicon.png">\n<link rel="icon" href="favicon.ico" sizes="any">\n<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
src = src.replace('</head>', icons + shim + '\n</head>', 1)
fixes = {
  "<b>Open the page while signed in to Claude</b> to see and update the guild’s timers.":
  "<b>Reload the page and enter the guild password</b> to see and update the guild’s timers.",
  "showNotice('Not connected to the shared board.":
  "showNotice((window.FALSEHOOD_FB_ERROR ? '<b>Firebase error: ' + window.FALSEHOOD_FB_ERROR + '.</b> ' : '') + 'Not connected to the shared board.",
  "const canEditStorage = ()=>{ try {": "const canEditStorage = ()=>{ if(window.FALSEHOOD_ROLE === 'timer') return false; try {",
  """        const v = document.getElementById('stMeName').value.trim().slice(0, 24);
        const ref = db.collection('names').doc(me);""": """        const v = document.getElementById('stMeName').value.trim().slice(0, 24);
        const nErr = window.falsehoodNickError ? window.falsehoodNickError(v) : '';
        if(nErr){ showToast(nErr); return; }
        const ref = db.collection('names').doc(me);""",
  "'your Claude name'": "'a guildmate (no name set)'",
  "You can see the guild’s timers but can’t log kills. Ask the page owner to invite you as an <b>Editor</b>.":
  "<b>View only.</b> You can see the timers and storage but can’t make changes.<button class=\"unlock\" onclick=\"falsehoodUnlock()\">🔑 Enter editor password</button>",
}
for a, b in fixes.items():
    assert a in src, a
    src = src.replace(a, b)
auto = root / 'autodetect.html'
if auto.exists():
    i = src.rfind('</body>')
    src = src[:i] + auto.read_text() + '\n' + src[i:]
import time, json
build_id = time.strftime('%Y%m%d%H%M%S', time.gmtime())
upd = root / 'updater.html'
if upd.exists():
    i = src.rfind('</body>')
    src = src[:i] + upd.read_text().replace('__BUILD__', build_id) + '\n' + src[i:]
(root.parent / 'version.json').write_text(json.dumps({'build': build_id}))
(root.parent / 'index.html').write_text(src)
print('built', len(src))
