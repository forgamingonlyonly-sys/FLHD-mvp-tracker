"""Build index.html for GitHub Pages: tracker source + Firebase bridge.
Usage: python3 build/build.py   (reads build/source.html, writes index.html)"""
import pathlib
root = pathlib.Path(__file__).resolve().parent
src = (root / 'source.html').read_text()
shim = (root / 'firebase-shim.html').read_text()
imp = root / 'import.json'
if imp.exists():
    shim = '<script>window.FALSEHOOD_IMPORT = ' + imp.read_text().replace('</', '<\\/') + ';</script>\n' + shim
src = src.replace('</head>', shim + '\n</head>', 1)
fixes = {
  "<b>Open the page while signed in to Claude</b> to see and update the guild’s timers.":
  "<b>Reload the page and enter the guild password</b> to see and update the guild’s timers.",
  "'your Claude name'": "'a guildmate (no name set)'",
  "Ask the page owner to invite you as an <b>Editor</b>.": "Reload the page and enter the guild password again.",
}
for a, b in fixes.items():
    assert a in src, a
    src = src.replace(a, b)
(root.parent / 'index.html').write_text(src)
print('built', len(src))
