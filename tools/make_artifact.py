"""Package viewer/index.html + models as a self-contained artifact page (models embedded as base64 .js).

Usage: python3 tools/make_artifact.py <out_dir>
"""
import base64
import os
import sys

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs(os.path.join(out, "models"), exist_ok=True)
for st in ("camp", "travel"):
    b = base64.b64encode(open(os.path.join(repo, "viewer", "models", f"fitout_{st}.glb"), "rb").read()).decode()
    with open(os.path.join(out, "models", f"fitout_{st}.js"), "w") as f:
        f.write(f'window.__GLB=window.__GLB||{{}};window.__GLB["{st}"]="{b}";\n')
s = open(os.path.join(repo, "viewer", "index.html")).read()
reps = [
    ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n', ''),
    ('<title>Tasman Fit-out Viewer</title>', '<title>Tasman Fit-out Viewer</title>\n<meta name="claude:viewport-fit-sides" content="cover">'),
    ('</style>\n</head>\n<body>', '</style>'),
    ('</body>\n</html>\n', ''),
    ('#ui { position:fixed; top:12px; left:12px;', '#ui { position:fixed; top:calc(12px + env(safe-area-inset-top, 0px)); left:max(16px, env(safe-area-inset-left, 0px));'),
    ('@media (max-width:600px) { #ui { width:calc(100% - 32px); left:16px; max-height:45%; } }',
     '@media (max-width:600px) { #ui { width:auto; right:max(16px, env(safe-area-inset-right, 0px)); max-height:42%; } }\n'
     '  #ui.min > :not(.head) { display:none; }\n  .head { display:flex; justify-content:space-between; align-items:center; gap:8px; }\n'
     '  button:focus-visible, input:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }'),
    ('<div id="ui">\n  <h1>Kia Tasman fit-out</h1>',
     '<div id="ui">\n  <div class="head"><h1>Kia Tasman fit-out</h1><button id="min" type="button" aria-expanded="true">Hide</button></div>'),
    ("  const gltf = await loader.loadAsync(`models/fitout_${state}.glb?v=${Date.now() % 1e6}`);",
     "  if (!(window.__GLB && window.__GLB[state])) await new Promise((res, rej) => {\n"
     "    const sc = document.createElement('script'); sc.src = `models/fitout_${state}.js`; sc.onload = res; sc.onerror = rej; document.head.appendChild(sc);\n"
     "  });\n  const bin = Uint8Array.from(atob(window.__GLB[state]), c => c.charCodeAt(0)).buffer;\n"
     "  const gltf = await loader.parseAsync(bin, '');"),
    ("(async () => {\n  const root",
     "document.getElementById('min').onclick = e => { const u = document.getElementById('ui'); const m = u.classList.toggle('min'); "
     "e.target.textContent = m ? 'Show' : 'Hide'; e.target.setAttribute('aria-expanded', String(!m)); };\n\n(async () => {\n  const root"),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(os.path.join(out, "tasman-fitout-viewer.html"), "w").write(s)
print("wrote", out)
