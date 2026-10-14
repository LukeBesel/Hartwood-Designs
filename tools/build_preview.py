"""Build a private preview of the website, 3D app, planner, SOPs and guides, for hosting as one claude.ai Artifact.

    .venv/bin/python tools/build_preview.py OUTDIR

The real site uses absolute paths, server routes (/build/<kit>/step/<n>), local fonts, a vendored three.js and an
offline service worker. The Artifact host serves files under its own origin and blocks service workers, print and
confirm dialogs, so the preview copy:
  - makes every path relative and uses the app's hash routes (#/<kit>/step/<n>);
  - loads three.js 0.169.0 from jsDelivr and the fonts from Google Fonts (both allowed by the host);
  - turns the service worker off (offline mode works on the real site only);
  - links repository files (cut files, booklets, docs) to GitHub.
Nothing here changes the real site.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import sys

import markdown
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE = os.path.join(ROOT, 'website')
THREE = 'https://cdn.jsdelivr.net/npm/three@0.169.0'
GH = 'https://github.com/LukeBesel/Hartwood-Designs'
BRANCH = 'claude/new-session-wxpxe8'
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap">')
SKIP_SITE = {'vendor', 'fonts', 'sw.js', 'manifest.webmanifest', '_redirects'}


def gh(path):
    """GitHub link for a repository path (folder or file)."""
    path = path.lstrip('./')
    kind = 'tree' if path.endswith('/') or os.path.isdir(os.path.join(ROOT, path)) else 'blob'
    return f'{GH}/{kind}/{BRANCH}/{path.rstrip("/")}'


# ------------------------------------------------------------------ website
def site_url(u, slug_prefix=''):
    """Absolute site path -> path relative to the site root (pages use <base> pointing at the root)."""
    if u == '/':
        return 'index.html'
    m = re.match(r'^/build/([a-z0-9-]+)/step/(\d+)/?$', u)
    if m:
        return f'build/index.html#/{m.group(1)}/step/{m.group(2)}'
    m = re.match(r'^/build/([a-z0-9-]+)/?$', u)
    if m:
        return f'build/index.html#/{m.group(1)}/step/1'
    if u.startswith('/#'):
        return 'index.html' + u[1:]
    u = u[1:]
    path, frag = (u.split('#', 1) + [''])[:2]
    if path.endswith('/') or path == '':
        path += 'index.html'
    elif '.' not in os.path.basename(path):
        path += '/index.html'
    return path + ('#' + frag if frag else '')


def rewrite_html(text, rel):
    """rel = the page's path from the site root, e.g. 'faq/index.html'."""
    base = '../' * rel.count('/') or './'
    text = re.sub(r'<script type="importmap">.*?</script>',
                  f'<script type="importmap">{{"imports":{{"three":"{THREE}/build/three.module.min.js","three/addons/":"{THREE}/examples/jsm/"}}}}</script>',
                  text, flags=re.S)
    text = re.sub(r'<link rel="manifest"[^>]*>', '', text)
    if '<head>' in text:
        text = text.replace('<head>', f'<head>\n<base href="{base}">\n{FONTS}', 1)
    else:                                   # the short redirect pages for old kit addresses have no <head>
        text = re.sub(r'(<meta charset="utf-8">)', rf'\1<base href="{base}">', text, count=1)
    text = re.sub(r'(content="\d+;\s*url=)(/[^"]*)"', lambda m: m.group(1) + site_url(m.group(2)) + '"', text)
    text = re.sub(r'((?:href|src|data-[a-z-]+)=")(/[^"]*)"', lambda m: m.group(1) + site_url(m.group(2)) + '"', text)
    # absolute paths inside inline scripts
    text = re.sub(r"(['\"`])/(assets|js|css|build|kits)/", r'\1\2/', text)
    # With <base> at the site root, a bare "#main" would point at the site folder, not this page.
    text = text.replace('href="#', f'href="{rel}#')
    return text


def rewrite_js(text, rel_path):
    depth = rel_path.count('/')
    up = '../' * depth or './'
    text = re.sub(r"from '/js/([a-z0-9_]+\.js)'", lambda m: f"from '{up}js/{m.group(1)}'", text)
    text = text.replace("navigator.serviceWorker.register('/sw.js')", 'Promise.reject(new Error("no service worker in the preview"))')
    text = re.sub(r'const usePath = [^;]+;', 'const usePath = false;   // preview: hash routes only', text)
    text = re.sub(r"(['\"`])/(assets|build|kits)/", r'\1\2/', text)
    text = text.replace('href="/#kits"', 'href="index.html#kits"')
    # Links the app builds from hash routes need the page name too, because of <base> (see rewrite_html).
    text = text.replace('href="${routeUrl(', 'href="build/index.html${routeUrl(')
    return text


def rewrite_css(text, rel_path):
    text = re.sub(r'@font-face\s*\{[^}]*\}\s*', '', text)
    up = '../' * rel_path.count('/')
    return re.sub(r"url\('?/([^)'\"]+)'?\)", lambda m: f"url('{up}{m.group(1)}')", text)


def glb_to_gltf_json(src, dst):
    """GLB -> glTF JSON with the binary buffer embedded as base64. The Artifact host does not serve .glb files,
    but serves .json, and three.js GLTFLoader reads both."""
    import base64
    import struct
    data = open(src, 'rb').read()
    magic, version, length = struct.unpack_from('<4sII', data, 0)
    assert magic == b'glTF', src
    off, gltf, binary = 12, None, b''
    while off < length:
        clen, ctype = struct.unpack_from('<I4s', data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == b'JSON':
            gltf = json.loads(chunk.decode('utf-8').rstrip(' \x00'))
        elif ctype == b'BIN\x00':
            binary = chunk
        off += 8 + clen
    gltf['buffers'][0]['uri'] = 'data:application/octet-stream;base64,' + base64.b64encode(binary).decode('ascii')
    json.dump(gltf, open(dst, 'w'), separators=(',', ':'))


def build_site(out):
    dst = os.path.join(out, 'site')
    for dirpath, dirs, files in os.walk(SITE):
        rel_dir = os.path.relpath(dirpath, SITE)
        if rel_dir.split(os.sep)[0] in SKIP_SITE:
            continue
        for f in files:
            rel = os.path.normpath(os.path.join(rel_dir, f)).replace(os.sep, '/')
            if rel in SKIP_SITE:
                continue
            src, tgt = os.path.join(dirpath, f), os.path.join(dst, rel)
            os.makedirs(os.path.dirname(tgt), exist_ok=True)
            if f.endswith('.glb'):
                glb_to_gltf_json(src, tgt[:-4] + '.gltf.json')
            elif f.endswith('.html'):
                open(tgt, 'w').write(rewrite_html(open(src).read(), rel).replace('kit.glb', 'kit.gltf.json'))
            elif f.endswith('.js'):
                open(tgt, 'w').write(rewrite_js(open(src).read(), rel).replace("'kit.glb'", "'kit.gltf.json'"))
            elif f.endswith('.css'):
                open(tgt, 'w').write(rewrite_css(open(src).read(), rel))
            else:
                shutil.copy(src, tgt)


# ------------------------------------------------------------------ guides (Markdown -> pages)
PAGE_CSS = """
:root { --bg:#FCF8F1; --card:#ffffff; --fg:#3A2A1F; --muted:#5C4636; --line:#E6D9C4; --accent:#0B6158; --tint:#F6EEE1; --code:#F1E7D6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#1d1612; --card:#28201a; --fg:#f3e9dc; --muted:#cbb9a3; --line:#3d3128; --accent:#5fd0c2; --tint:#2e251e; --code:#3a2f26; color-scheme: dark; } }
:root[data-theme="dark"] { --bg:#1d1612; --card:#28201a; --fg:#f3e9dc; --muted:#cbb9a3; --line:#3d3128; --accent:#5fd0c2; --tint:#2e251e; --code:#3a2f26; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.6 Inter, system-ui, sans-serif; }
.wrap { max-width: 980px; margin: 0 auto; padding-inline: 16px; padding-block: 18px 48px; }
nav.top { font-size: .9rem; padding-block: 6px 14px; } nav.top a { color: var(--accent); }
h1, h2 { font-family: Fraunces, Georgia, serif; line-height: 1.15; text-wrap: balance; }
h1 { font-size: clamp(1.8rem, 4vw, 2.5rem); margin: .2em 0 .4em; } h2 { font-size: 1.45rem; margin: 1.6em 0 .5em; } h3 { margin: 1.2em 0 .4em; }
p, li { max-width: 72ch; } a { color: var(--accent); }
img { max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--line); background: var(--tint); }
code { background: var(--code); padding: 1px 5px; border-radius: 5px; font-size: .88em; overflow-wrap: anywhere; }
.tw { overflow-x: auto; margin: 12px 0; border: 1px solid var(--line); border-radius: 12px; background: var(--card); }
table { border-collapse: collapse; width: 100%; font-size: .93rem; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { background: var(--tint); font-size: .78rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
tr:last-child td { border-bottom: 0; }
"""


def md_page(md_path, out_path, title, img_dir):
    text = open(md_path).read()
    src_dir = os.path.dirname(md_path)

    def img(m):
        alt, url = m.group(1), m.group(2)
        src = os.path.normpath(os.path.join(src_dir, url))
        name = os.path.basename(src)
        os.makedirs(img_dir, exist_ok=True)
        im = Image.open(src).convert('RGB')
        im.thumbnail((1400, 1400))
        name = os.path.splitext(name)[0] + '.jpg'
        im.save(os.path.join(img_dir, name), quality=85)
        return f'![{alt}](img/{name})'
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img, text)
    text = re.sub(r'(?<!!)\[([^\]]+)\]\((\.\./[^)]+)\)', lambda m: f'[{m.group(1)}]({gh(os.path.relpath(os.path.normpath(os.path.join(src_dir, m.group(2))), ROOT))})', text)
    text = re.sub(r'\]\((HOW_TO_CUT|BLASTER_TEST)\.md\)', lambda m: f']({m.group(1).lower()}.html)', text)
    body = markdown.markdown(text, extensions=['tables'])
    body = body.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(title)}</title>{FONTS}<style>{PAGE_CSS}</style></head><body><div class="wrap">'
            f'<nav class="top"><a href="../index.html">Hartwood preview</a></nav>{body}</div></body></html>')
    open(out_path, 'w').write(page)


# ------------------------------------------------------------------ planner and SOPs
def build_planner(out):
    dst = os.path.join(out, 'planner')
    os.makedirs(dst, exist_ok=True)
    src = os.path.join(ROOT, 'production', 'planner')
    for f in os.listdir(src):
        p = os.path.join(src, f)
        t = open(p).read() if f.endswith(('.html', '.js', '.css', '.csv')) else None
        if f == 'index.html':
            t = t.replace('../../website/favicon.svg', '../site/favicon.svg').replace('<head>', '<head>\n' + FONTS, 1)
            t = t.replace('<button class="btn primary" id="printSched">Print the schedule</button>',
                          '<button class="btn primary" id="printSched" hidden>Print the schedule</button>'
                          '<span class="muted">Printing works in the real planner on your tablet.</span>')
        if f == 'planner.js':
            t = t.replace('confirm(', '(() => true)(')        # the preview host blocks confirm() dialogs
        if t is not None:
            open(os.path.join(dst, f), 'w').write(t)
        else:
            shutil.copy(p, dst)


def build_sops(out):
    dst = os.path.join(out, 'sops')
    src = os.path.join(ROOT, 'production', 'sops')
    shutil.copytree(os.path.join(src, 'img'), os.path.join(dst, 'img'))
    os.makedirs(os.path.join(dst, 'thumbs'), exist_ok=True)
    for f in sorted(os.listdir(src)):
        p = os.path.join(src, f)
        if f.endswith('.pdf'):
            shutil.copy(p, dst)
        elif f.endswith('.html'):
            t = open(p).read()
            t = re.sub(r'@font-face \{[^}]*\}\s*', '', t).replace('<head>', '<head>' + FONTS, 1)
            t = t.replace('<title>', '<title>', 1)
            if f == 'index.html':
                def th(m):
                    name = m.group(1)
                    im = Image.open(os.path.join(ROOT, 'review', 'production', 'sops', name)).convert('RGB')
                    im.save(os.path.join(dst, 'thumbs', name[:-4] + '.jpg'), quality=82)
                    return f'src="thumbs/{name[:-4]}.jpg"'
                t = re.sub(r'src="\.\./\.\./review/production/sops/([^"]+\.png)"', th, t)
                t = t.replace('href="../layout/workshop_layout.svg"', f'href="{gh("production/layout/workshop_layout.png")}" target="_blank"')
                t = t.replace('href="../quality_loop.md"', f'href="{gh("production/quality_loop.md")}" target="_blank"')
                t = t.replace('<p>Station map:', '<p><a href="../index.html">Back to the preview</a>. Station map:')
            open(os.path.join(dst, f), 'w').write(t)


# ------------------------------------------------------------------ hub page (the Artifact's main page)
def shot(src, dst, width=1200, crop=None):
    im = Image.open(src).convert('RGB')
    if crop:
        im = im.crop(crop)
    im.thumbnail((width, width * 3))
    im.save(dst, quality=84)


def build_hub(out):
    a = os.path.join(out, 'hub')
    os.makedirs(a, exist_ok=True)
    shot(os.path.join(ROOT, 'review', 'site', 'home_desktop.png'), os.path.join(a, 'site.jpg'), 900, (0, 0, 1280, 820))
    shot(os.path.join(ROOT, 'review', 'app', 'phone_step4.png'), os.path.join(a, 'app.jpg'), 520, (0, 0, 780, 1100))
    shot(os.path.join(ROOT, 'kits', 'blaster', 'renders', 'lifted.jpg'), os.path.join(a, 'lifted.jpg'), 1000, (250, 120, 1600, 1250))
    shot(os.path.join(ROOT, 'review', 'production', 'planner_quality.png'), os.path.join(a, 'planner.jpg'), 700, (0, 0, 1180, 820))
    shot(os.path.join(ROOT, 'review', 'production', 'sops', 'SOP-2_p1.png'), os.path.join(a, 'sop.jpg'), 600, (0, 0, 680, 520))
    shot(os.path.join(ROOT, 'brand', 'packaging', 'mockup_lineup.png'), os.path.join(a, 'boxes.jpg'), 900, (0, 60, 1500, 553))
    rep = {k: json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_report.json'))) for k in ('blaster', 'dragon', 'floral')}
    st = {k: json.load(open(os.path.join(ROOT, 'kits', k, f'{k}_steps.json'))) for k in rep}
    rows = ''.join(f'<tr><td><a href="site/kits/{slug}/index.html">{html.escape(st[k]["name"])}</a></td><td>{st[k]["piece_count"]}</td>'
                   f'<td>{len(rep[k]["sheets"])}</td><td>{rep[k]["cut_minutes_per_kit"]:.1f}</td><td>${st[k]["price"]:.2f}</td>'
                   f'<td><a href="site/build/index.html#/{k}/step/1">Build in 3D</a></td>'
                   f'<td><a href="{gh(f"kits/{k}/cutfiles/")}" target="_blank" rel="noopener">Cut files</a></td></tr>'
                   for k, slug in (('blaster', 'star-slinger'), ('dragon', 'emberwing'), ('floral', 'blossom-waltz')))
    page = f"""<title>Hartwood Preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap">
<style>
/* Layout: a workbench index. One hero row (site, 3D app, the lift-off render), then the blaster test and the workshop tools. */
:root {{ --bg:#FBF6EE; --card:#ffffff; --fg:#33241A; --muted:#6A5442; --line:#E7D9C3; --wood:#E9D3AE; --accent:#0B6158; --accent-ink:#ffffff; --blaze:#E85D0C; --chip:#F3E8D6;
  --display: Fraunces, Georgia, serif; --body: Inter, system-ui, sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#1C1511; --card:#271E18; --fg:#F2E8DA; --muted:#C7B49D; --line:#3B2F26; --wood:#4A3A2C; --accent:#5FD0C2; --accent-ink:#10231F; --blaze:#FF8A45; --chip:#33281F; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg:#1C1511; --card:#271E18; --fg:#F2E8DA; --muted:#C7B49D; --line:#3B2F26; --wood:#4A3A2C; --accent:#5FD0C2; --accent-ink:#10231F; --blaze:#FF8A45; --chip:#33281F; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.55 var(--body); }}
.wrap {{ max-width: 1120px; margin: 0 auto; padding-inline: 16px; padding-block: 22px 56px; display: grid; gap: 34px; }}
.wrap > * {{ min-width: 0; }}
header h1 {{ font: 800 clamp(2rem, 5vw, 3.1rem)/1.05 var(--display); margin: 0 0 8px; text-wrap: balance; }}
header p {{ margin: 0; max-width: 66ch; color: var(--muted); }}
.eyebrow {{ font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; color: var(--blaze); }}
h2 {{ font: 700 1.5rem/1.2 var(--display); margin: 0 0 12px; }}
.row {{ display: grid; gap: 14px; grid-template-columns: 1.35fr 0.75fr 1.15fr; align-items: stretch; }}
.tile {{ display: flex; flex-direction: column; background: var(--card); border: 1px solid var(--line); border-radius: 16px; overflow: hidden; color: inherit; text-decoration: none; min-width: 0; }}
.tile img {{ display: block; width: 100%; height: 230px; object-fit: cover; object-position: top; background: var(--wood); }}
.tile .t {{ padding: 12px 14px 14px; display: grid; gap: 4px; }}
.tile b {{ font: 700 1.1rem var(--display); }}
.tile span {{ color: var(--muted); font-size: .92rem; }}
.tile:hover b, .tile:focus-visible b {{ color: var(--accent); }}
.tile:focus-visible, a:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 2px; }}
.go {{ display: inline-flex; align-items: center; justify-content: center; min-height: 44px; padding: 0 18px; border-radius: 999px; background: var(--accent); color: var(--accent-ink); font-weight: 700; text-decoration: none; }}
.test {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.panel {{ background: var(--card); border: 1px solid var(--line); border-radius: 16px; padding: 16px; display: grid; gap: 8px; align-content: start; min-width: 0; }}
.panel p {{ margin: 0; color: var(--muted); }}
.panel ol {{ margin: 0; padding-left: 20px; }}
.tw {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 14px; background: var(--card); }}
table {{ border-collapse: collapse; width: 100%; font-size: .95rem; font-variant-numeric: tabular-nums; }}
th, td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid var(--line); white-space: nowrap; }}
th {{ font-size: .76rem; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); background: var(--chip); }}
tr:last-child td {{ border-bottom: 0; }}
a {{ color: var(--accent); }}
.tools {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }}
.note {{ font-size: .9rem; color: var(--muted); border-left: 3px solid var(--blaze); padding-left: 12px; max-width: 80ch; }}
@media (max-width: 860px) {{ .row, .test, .tools {{ grid-template-columns: 1fr; }} .tile img {{ height: 210px; }} }}
</style>
<div class="wrap">
<header><div class="eyebrow">Hartwood Designs</div><h1>Everything built so far</h1>
<p>A private preview of the website, the 3D build app and the workshop tools. Tap anything to open it. Cut files, booklets and source files open on GitHub.</p></header>

<section class="row" aria-label="Main previews">
  <a class="tile" href="site/index.html"><img src="hub/site.jpg" alt="Hartwood website home page"><div class="t"><b>The website</b><span>Home, the three kit pages with a 3D model you can spin, FAQ, safety and checkout placeholders.</span></div></a>
  <a class="tile" href="site/build/index.html#/blaster/step/1"><img src="hub/app.jpg" alt="3D build app on a phone"><div class="t"><b>3D build app</b><span>Step through the Star Slinger. Parts slide in, tap one to see its code.</span></div></a>
  <a class="tile" href="site/kits/star-slinger/index.html"><img src="hub/lifted.jpg" alt="Star Slinger lifted off its stand"><div class="t"><b>Star Slinger lifts off</b><span>The ship drops into a U cradle on the stand and lifts straight off to play.</span></div></a>
</section>

<section aria-labelledby="test"><h2 id="test">Blaster test</h2>
<div class="test">
  <div class="panel"><b>What to order</b><p>Wood, colored sheets, rubber bands, dowels and wax for 3 blasters, about $165. Plus the laser and safety gear, each with a direct link.</p><a class="go" href="guides/blaster_test.html">Open the order list</a></div>
  <div class="panel"><b>How to cut</b><p>Which file to open in LightBurn, layer settings, lining up the sheets with the camera, and what to do when a part sticks.</p><a class="go" href="guides/how_to_cut.html">Open the cutting guide</a></div>
</div></section>

<section aria-labelledby="kits"><h2 id="kits">The kits</h2>
<div class="tw"><table><thead><tr><th>Kit</th><th>Pieces</th><th>Sheets</th><th>Laser min per kit</th><th>Price</th><th></th><th></th></tr></thead><tbody>{rows}</tbody></table></div>
</section>

<section aria-labelledby="shop"><h2 id="shop">Workshop tools</h2>
<div class="tools">
  <a class="tile" href="planner/index.html"><img src="hub/planner.jpg" alt="Workshop planner"><div class="t"><b>Workshop planner</b><span>Orders, cut queue, schedule, tracking board, inventory and the quality Pareto. Saved in this browser.</span></div></a>
  <a class="tile" href="sops/index.html"><img src="hub/sop.jpg" alt="Load and cut SOP"><div class="t"><b>Seven picture SOPs</b><span>One page per station: start-up, load and cut, pop-out check, kitting, maintenance, fire, shipping.</span></div></a>
  <a class="tile" href="{gh('START_HERE.html')}" target="_blank" rel="noopener"><img src="hub/boxes.jpg" alt="Kit boxes"><div class="t"><b>Everything else on GitHub</b><span>Research, supply lists, unit economics, packaging, the engine and every decision.</span></div></a>
</div></section>

<p class="note">This preview cannot do three things the real site does: work offline (the host blocks service workers), open the print dialog, or take orders (the store links are placeholders until you add Shopify, Stripe or Etsy).</p>
</div>"""
    open(os.path.join(out, 'index.html'), 'w').write(page)


def main(out):
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    build_site(out)
    g = os.path.join(out, 'guides')
    os.makedirs(g)
    md_page(os.path.join(ROOT, 'guides', 'BLASTER_TEST.md'), os.path.join(g, 'blaster_test.html'), 'Blaster Test Order', os.path.join(g, 'img'))
    md_page(os.path.join(ROOT, 'guides', 'HOW_TO_CUT.md'), os.path.join(g, 'how_to_cut.html'), 'Cutting Guide', os.path.join(g, 'img'))
    build_planner(out)
    build_sops(out)
    build_hub(out)
    files = [os.path.relpath(os.path.join(d, f), out) for d, _, fs in os.walk(out) for f in fs]
    size = sum(os.path.getsize(os.path.join(out, f)) for f in files)
    print(f'{len(files)} files, {size / 1e6:.1f} MB in {out}')


if __name__ == '__main__':
    main(sys.argv[1])
