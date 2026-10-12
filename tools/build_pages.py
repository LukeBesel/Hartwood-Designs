"""Static website pages from one layout and the kit data (website/assets/kits/kits.json).

    .venv/bin/python tools/build_pages.py
"""
from __future__ import annotations

import html
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE = os.path.join(ROOT, 'website')
KITS = json.load(open(os.path.join(SITE, 'assets', 'kits', 'kits.json')))
BY = {k['kit']: k for k in KITS}
E = html.escape

FEATURES = {
    'blaster': ['A clockwork star wheel holds up to 7 rubber bands', 'One band flies per trigger pull',
                'Blaze orange nose, plug and cap, so it always reads as a toy',
                'Launch stand with a swinging target, a band rack and a safety plaque',
                'Test steps built into the instructions, so the mechanism works the first time'],
    'dragon': ['The jaw opens on a hidden wooden pin', 'A treasure chest with a lid that opens',
               'Layered purple wings with laser-drawn bones', 'Scales drawn on every body slice',
               'Claws that grip the battlements of a ruined tower'],
    'floral': ['Plays a tune: an 18-note wind-up music movement is included', 'The whole bouquet turns while it plays',
               'Eight layered flowers that never wilt', 'Pastel colored wood, no paint needed',
               'A picket fence and two butterflies to finish the garden'],
}
DIFF_WORDS = {1: 'Easy', 2: 'Easy', 3: 'Medium', 4: 'Challenging', 5: 'Expert'}
STORE_NOTE = 'TODO_LUCAS: add your store link'


def nav(active=''):
    links = [('/#kits', 'Kits', 'kits'), ('/build/', 'Build in 3D', 'build'), ('/faq/', 'FAQ', 'faq'), ('/about/', 'About', 'about')]
    cur = ' aria-current="page"'
    items = ''.join(f'<li><a href="{h}"{cur if a == active else ""}>{t}</a></li>' for h, t, a in links)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
  <div class="wrap head-row">
    <a class="brand" href="/" aria-label="Hartwood Designs home"><img src="/assets/logo.svg" alt="Hartwood Designs" width="190" height="44"></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="siteNav" aria-label="Menu">
      <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg></button>
    <nav id="siteNav" class="site-nav" aria-label="Main"><ul>{items}</ul></nav>
    <a class="cart-link" href="/checkout/" aria-label="Cart"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M3 4h2l2.4 10.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 1.9-1.4L21 8H6.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="10" cy="20" r="1.6" fill="currentColor"/><circle cx="17" cy="20" r="1.6" fill="currentColor"/></svg><span class="cart-count" data-cart-count>0</span></a>
  </div>
</header>'''


FOOT = '''<footer class="site-foot">
  <div class="wrap foot-grid">
    <div><img src="/assets/logo_on_dark.svg" alt="Hartwood Designs" width="180" height="42">
      <p>Wooden model kits that move. Designed and laser-cut in Minnesota.</p></div>
    <div><h3>Kits</h3><ul>KITLINKS</ul></div>
    <div><h3>Help</h3><ul><li><a href="/build/">3D instructions</a></li><li><a href="/faq/">FAQ</a></li>
      <li><a href="/safety/">Safety</a></li><li><a href="/contact/">Contact and spare parts</a></li></ul></div>
    <div><h3>Company</h3><ul><li><a href="/about/">About</a></li><li><a href="/terms/">Terms and shipping</a></li>
      <li><a href="/privacy/">Privacy</a></li></ul></div>
  </div>
  <div class="wrap foot-legal"><p>&copy; 2026 <span class="todo">TODO_LUCAS: legal company name</span>. All kits are for ages 14 and up.</p></div>
</footer>'''


def page(title, desc, body, active='', extra_head='', scripts=''):
    kitlinks = ''.join(f'<li><a href="/kits/{k["url"]}/">{E(k["name"])}</a></li>' for k in KITS)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta name="theme-color" content="#0F8B7F">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="stylesheet" href="/css/site.css">
<link rel="stylesheet" href="/css/pages.css">
{extra_head}
</head>
<body>
{nav(active)}
<main id="main">
{body}
</main>
{FOOT.replace('KITLINKS', kitlinks)}
<script src="/js/site.js" defer></script>
{scripts}
</body>
</html>
'''


def dots(n):
    return '<span class="dots" aria-label="Difficulty {0} of 5">{1}</span>'.format(
        n, ''.join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(5)))


def kit_card(k):
    return f'''<article class="kit-card">
  <a href="/kits/{k["url"]}/" class="kit-img"><img src="/assets/kits/{k["kit"]}/renders/three_quarter_sm.webp" alt="{E(k["name"])} wooden model kit, assembled" width="640" height="480" loading="lazy"></a>
  <div class="kit-body">
    <h3><a href="/kits/{k["url"]}/">{E(k["name"])}</a></h3>
    <p>{E(k["tagline"])}</p>
    <p class="meta">{k["pieces"]} pieces &middot; {k["hours"]} &middot; {DIFF_WORDS[k["difficulty"]]} {dots(k["difficulty"])}</p>
    <div class="price-row"><span class="price">${k["price"]:.2f}</span>
      <a class="btn btn-primary" href="/kits/{k["url"]}/">See the kit</a></div>
  </div>
</article>'''


def home():
    cards = '\n'.join(kit_card(k) for k in KITS)
    body = f'''<section class="hero">
  <div class="wrap hero-grid">
    <div class="hero-copy">
      <p class="eyebrow">Laser-cut wooden model kits</p>
      <h1>Wooden kits that move.</h1>
      <p class="lead">A starship that slings rubber bands. A dragon whose jaw opens. A flower garden that turns while it plays music.
        150 pieces or more each, no glue, and step-by-step 3D instructions on your phone.</p>
      <div class="cta-row"><a class="btn btn-primary" href="#kits">Shop the kits</a>
        <a class="btn" href="/build/">Try the 3D instructions</a></div>
    </div>
    <div class="hero-art" aria-hidden="true">
      <img class="h1" src="/assets/kits/dragon/renders/cut_three_quarter.webp" alt="" width="900" height="675">
      <img class="h2" src="/assets/kits/floral/renders/cut_three_quarter.webp" alt="" width="900" height="675">
      <img class="h3" src="/assets/kits/blaster/renders/cut_three_quarter.webp" alt="" width="900" height="675">
    </div>
  </div>
</section>
<section class="trust" aria-label="Why our kits">
  <div class="wrap trust-row">
    <div><img src="/assets/icons/no-glue.svg" alt="" width="44" height="44"><span>No glue needed</span></div>
    <div><img src="/assets/icons/press.svg" alt="" width="44" height="44"><span>150+ pieces, press-fit</span></div>
    <div><img src="/assets/icons/test.svg" alt="" width="44" height="44"><span>Mechanisms tested step by step</span></div>
    <div><img src="/assets/icons/sort.svg" alt="" width="44" height="44"><span>Spare small parts included</span></div>
  </div>
</section>
<section id="kits" class="section">
  <div class="wrap">
    <h2>The kits</h2>
    <p class="sub">Three builds for one evening or a whole weekend. Every kit comes flat-packed on pre-colored wood sheets.</p>
    <div class="kit-grid">{cards}</div>
  </div>
</section>
<section class="section how">
  <div class="wrap">
    <h2>How it works</h2>
    <ol class="how-grid">
      <li><img src="/assets/icons/push-out.svg" alt="" width="64" height="64"><h3>1. Push out</h3><p>Every part is cut and coded. Press it out from the back of the sheet.</p></li>
      <li><img src="/assets/icons/press.svg" alt="" width="64" height="64"><h3>2. Build</h3><p>Follow the picture booklet, or turn each step around in 3D on your phone.</p></li>
      <li><img src="/assets/icons/test.svg" alt="" width="64" height="64"><h3>3. Make it move</h3><p>Test the moving parts as you go. Then set it on a shelf and show it off.</p></li>
    </ol>
  </div>
</section>
<section class="section app-promo">
  <div class="wrap promo-grid">
    <div class="phone"><img src="/assets/site/app_phone.webp" alt="The 3D instruction app on a phone, showing step 4 of the Star Slinger" width="390" height="844" loading="lazy"></div>
    <div>
      <h2>Instructions you can turn around</h2>
      <p>Scan the code on any page of the booklet. The same step opens in 3D: new parts glow orange and slide into place.
        Spin the model with a finger, tap any part to see its code and sheet, and pick up where you left off.
        It even works without internet after the first visit.</p>
      <a class="btn btn-primary" href="/build/">Open the 3D instructions</a>
    </div>
  </div>
</section>
<section class="section faq-teaser">
  <div class="wrap">
    <h2>Good to know</h2>
    <div class="qa-grid">
      <div><h3>Do I need glue or tools?</h3><p>No. Parts press together. A wax stick and sandpaper are in the box for moving parts and tight spots.</p></div>
      <div><h3>Who are the kits for?</h3><p>Ages 14 and up. Many adults build them as a relaxing evening project or as a gift.</p></div>
      <div><h3>What if I lose a part?</h3><p>Many small parts have a spare on the sheet. For anything else, send us the part code and we will mail one free.</p></div>
    </div>
    <p><a href="/faq/">All questions</a></p>
  </div>
</section>
<section class="section signup">
  <div class="wrap signup-box">
    <h2>New kits, first</h2>
    <p>Get one email when a new kit is ready. No spam.</p>
    <form class="signup-form" action="#" onsubmit="return false">
      <label class="sr-only" for="email">Email</label>
      <input id="email" type="email" placeholder="you@example.com" autocomplete="email" disabled>
      <button class="btn btn-primary" disabled>Sign up</button>
    </form>
    <p class="small"><span class="todo">TODO_LUCAS: connect an email list (for example Mailchimp or Buttondown) before launch.</span></p>
  </div>
</section>'''
    return page('Hartwood Designs | Wooden model kits that move',
                'Laser-cut wooden 3D model kits with real mechanisms: a rubber band starship, a dragon and a flower music box. No glue, 3D instructions.',
                body, extra_head='<link rel="preload" as="image" href="/assets/kits/dragon/renders/cut_three_quarter.webp">')


def kit_page(k):
    kit = k['kit']
    views = [('three_quarter', 'Three-quarter view'), ('front', 'Front view'), ('side', 'Side view'), ('back', 'Back view'),
             ('top', 'Top view')]
    rdir = os.path.join(SITE, 'assets', 'kits', kit, 'renders')
    avail = [v for v in views if os.path.exists(os.path.join(rdir, v[0] + '.webp'))]
    closeups = sorted(f[:-5] for f in os.listdir(rdir) if f.startswith('closeup') and f.endswith('.webp') and not f.endswith('_sm.webp'))
    shots = avail + [(c, c.replace('closeup_', 'Close-up: ').replace('_', ' ')) for c in closeups]
    thumbs = ''.join(f'<button class="thumb{" active" if i == 0 else ""}" data-src="/assets/kits/{kit}/renders/{v}.webp" aria-label="{E(t)}">'
                     f'<img src="/assets/kits/{kit}/renders/{v}_sm.webp" alt="" width="120" height="90" loading="lazy"></button>'
                     for i, (v, t) in enumerate(shots))
    feats = ''.join(f'<li>{E(f)}</li>' for f in FEATURES[kit])
    inbox = ''.join(f'<li>{v} x {E(n)}</li>' for n, v in k['extras'].items())
    L, Hh, D = k['size_mm']
    safety = ''
    if kit == 'blaster':
        safety = '''<aside class="safety-box"><img src="/assets/icons/glasses.svg" alt="" width="48" height="48"><div>
  <h3>Safety first</h3><p>Shoots rubber bands. Ages 14 and up. Wear glasses when you fire, aim only at the target,
  and never at faces, people or pets. The blaze orange nose, plug and cap are part of the ship and must stay on.
  <a href="/safety/">Read the safety page</a>.</p></div></aside>'''
    body = f'''<nav class="wrap crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/#kits">Kits</a> / <span>{E(k["name"])}</span></nav>
<section class="wrap product">
  <div class="gallery">
    <div class="main-shot"><img id="mainShot" src="/assets/kits/{kit}/renders/three_quarter.webp" alt="{E(k["name"])}, assembled" width="1400" height="1050"></div>
    <div class="thumbs" role="group" aria-label="More pictures">{thumbs}</div>
  </div>
  <div class="buy">
    <p class="eyebrow">{k["pieces"]} pieces &middot; Ages {k["age"]}</p>
    <h1>{E(k["name"])}</h1>
    <p class="lead">{E(k["tagline"])}</p>
    <p class="price big">${k["price"]:.2f}</p>
    <button class="btn btn-primary btn-wide" data-add-to-cart="{kit}" data-name="{E(k["name"])}" data-price="{k["price"]}">Add to cart</button>
    <p class="small muted">Ships flat in a 12.5 x 12.5 in box. <span class="todo">{STORE_NOTE}</span></p>
    <ul class="feature-list">{feats}</ul>
    {safety}
  </div>
</section>
<section class="section">
  <div class="wrap two-col">
    <div><h2>The story</h2><p>{E(k["story"])}</p>
      <p><a class="btn" href="/build/{kit}/step/1">Preview the 3D instructions</a>
         <a class="btn btn-ghost" href="/assets/kits/{kit}/{kit}_instructions.pdf" download>Download the booklet (PDF)</a></p></div>
    <div><h2>Details</h2>
      <table class="specs">
        <tr><th scope="row">Pieces</th><td>{k["pieces"]} wooden parts</td></tr>
        <tr><th scope="row">Build time</th><td>About {k["hours"]}</td></tr>
        <tr><th scope="row">Difficulty</th><td>{DIFF_WORDS[k["difficulty"]]} {dots(k["difficulty"])}</td></tr>
        <tr><th scope="row">Finished size</th><td>{L} x {D} x {Hh} mm ({L / 25.4:.1f} x {D / 25.4:.1f} x {Hh / 25.4:.1f} in), L x W x H</td></tr>
        <tr><th scope="row">Steps</th><td>{k["steps"]}, each with a 3D view</td></tr>
        <tr><th scope="row">Material</th><td>3 mm basswood plywood, natural and pre-colored sheets</td></tr>
        <tr><th scope="row">Age</th><td>{k["age"]}. Contains small parts.</td></tr>
      </table>
      <h3>Also in the box</h3><ul class="inbox">{inbox}</ul></div>
  </div>
</section>
<section class="section viewer-sec">
  <div class="wrap">
    <h2>Turn it around</h2>
    <div class="viewer" id="viewer" data-glb="/assets/kits/{kit}/kit.glb">
      <img src="/assets/kits/{kit}/renders/back_sm.webp" alt="" class="viewer-poster" onerror="this.remove()">
      <button class="btn btn-primary" id="viewerBtn">Load the 3D model ({os.path.getsize(os.path.join(SITE, "assets", "kits", kit, "kit.glb")) / 1e6:.1f} MB)</button>
      <canvas id="viewerCanvas" aria-label="3D model of {E(k["name"])}. Drag to turn."></canvas>
    </div>
  </div>
</section>'''
    ld = json.dumps({'@context': 'https://schema.org', '@type': 'Product', 'name': k['name'], 'description': k['tagline'],
                     'brand': {'@type': 'Brand', 'name': 'Hartwood Designs'},
                     'image': f'/assets/kits/{kit}/renders/three_quarter.webp',
                     'offers': {'@type': 'Offer', 'priceCurrency': 'USD', 'price': f"{k['price']:.2f}", 'availability': 'https://schema.org/PreOrder'}})
    return page(f'{k["name"]} wooden model kit | Hartwood Designs', f'{k["tagline"]} {k["pieces"]} pieces, no glue, ages {k["age"]}.',
                body, active='kits', extra_head=f'<script type="application/ld+json">{ld}</script>'
                '<script type="importmap">{"imports":{"three":"/vendor/three/three.module.min.js","three/addons/":"/vendor/three/addons/"}}</script>',
                scripts='<script type="module" src="/js/viewer.js"></script>')


def text_page(slug, title, desc, inner, active=''):
    body = f'<section class="wrap prose"><h1>{E(title)}</h1>{inner}</section>'
    return slug, page(f'{title} | Hartwood Designs', desc, body, active=active)


FAQ = [
    ('Do I need glue or tools?', 'No. Every joint is a press fit: tabs into slots, square pegs through layers, and wooden dowels for parts that turn. A wax stick and a piece of sandpaper are in the box.'),
    ('How long does a kit take?', 'About 4 to 8 hours, depending on the kit. Most people build over two or three evenings.'),
    ('What age are the kits for?', 'Ages 14 and up. The parts are small and some joints need a firm, careful press.'),
    ('A part is too tight. What do I do?', 'Rub the tab two or three times on the sandpaper, then try again. Never force a part: thin parts can snap.'),
    ('A part broke or is missing.', 'Many small parts have a spare on the sheet (the code ends in s). For anything else, send us the part code from the parts map and we will mail a new one free.'),
    ('How do the 3D instructions work?', 'Scan the QR code on any booklet page, or open the Build in 3D page. Each step shows the new parts in orange sliding into place. Turn the model with a finger and tap a part to see its code.'),
    ('Do the 3D instructions need internet?', 'Only the first time. After that the app and the kits you opened work offline on that device.'),
    ('Is the Star Slinger safe?', 'It shoots standard #64 rubber bands. Wear glasses, aim only at the target, never at faces, people or pets. Its blaze orange nose, plug and cap mark it as a toy and must stay on.'),
    ('What music does Blossom Waltz play?', 'It comes with an 18-note wind-up movement. TODO_LUCAS: name the tune once the movement supplier is chosen.'),
    ('Where do you ship?', 'TODO_LUCAS: shipping countries, rates and delivery times.'),
    ('Can I return a kit?', 'TODO_LUCAS: return policy (for example 30 days for unopened kits).'),
]


def faq():
    todo = '<span class="todo">TODO_LUCAS</span>'
    inner = ''.join(f'<details class="qa"><summary>{E(q)}</summary><p>{E(a).replace("TODO_LUCAS", todo)}</p></details>'
                    for q, a in FAQ)
    ld = json.dumps({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ if 'TODO' not in a]})
    body = f'<section class="wrap prose"><h1>Questions and answers</h1>{inner}</section>'
    return page('FAQ | Hartwood Designs', 'Answers about building Hartwood wooden model kits: glue, time, age, spare parts and the 3D instructions.',
                body, active='faq', extra_head=f'<script type="application/ld+json">{ld}</script>')


SAFETY = '''<p>Our kits are hobby models for ages 14 and up. Please read this before you build.</p>
<h2>For every kit</h2>
<ul><li>Small parts. Keep loose parts away from young children and pets.</li>
<li>Laser-cut edges can be slightly sharp or sooty. Wipe them with a dry cloth if you like.</li>
<li>Do not force parts. If one is tight, sand the tab a little. Thin parts can snap.</li>
<li>Wood burns. Keep the finished model away from candles, heaters and stoves.</li></ul>
<h2>Star Slinger (rubber band shooter)</h2>
<ul><li>Wear glasses when you fire it. Bands can bounce back.</li>
<li>Aim only at the paper target. Never at faces, people or animals.</li>
<li>Use #64 rubber bands only, at most 7 at a time.</li>
<li>The blaze orange nose, plug and cap are part of the ship. They show it is a toy. Do not remove or paint them.</li>
<li>Do not carry it in public places where someone could mistake it for something else.</li></ul>
<h2>Blossom Waltz (music box)</h2>
<ul><li>Do not over-wind the key. Stop when it gets firm.</li></ul>
<p class="small">Questions about safety? <a href="/contact/">Contact us</a>.</p>'''

ABOUT = '''<p>Hartwood Designs makes wooden model kits that move: a starship with a clockwork trigger, a dragon whose jaw opens,
a flower garden that turns while it plays.</p>
<p>Every kit is designed on a computer, checked by software for fit, strength and build order, and then laser-cut from
3 mm basswood in our Minnesota workshop. We test every moving part on real wood before a kit goes on sale.</p>
<p>We use pre-colored wood instead of paint, press-fit joints instead of glue, and print the part code beside every piece,
so building feels calm, not fiddly.</p>
<p class="small"><span class="todo">TODO_LUCAS: add your own story and a photo of the workshop.</span></p>'''

CONTACT = '''<p>Questions, a missing part, or an idea for a new kit? Write to us. We answer within two working days.</p>
<p><strong>Email:</strong> <span class="todo">TODO_LUCAS: support email</span></p>
<p><strong>Spare parts:</strong> tell us the kit name and the part code from the parts map (for example: Emberwing, part C12).</p>
<form class="contact-form" action="#" onsubmit="return false">
  <label for="cname">Name</label><input id="cname" autocomplete="name" disabled>
  <label for="cmail">Email</label><input id="cmail" type="email" autocomplete="email" disabled>
  <label for="cmsg">Message</label><textarea id="cmsg" rows="5" disabled></textarea>
  <button class="btn btn-primary" disabled>Send</button>
</form>
<p class="small"><span class="todo">TODO_LUCAS: connect this form (for example Formspree or Netlify Forms) or replace it with your email link.</span></p>'''

TERMS = '''<p><span class="todo">TODO_LUCAS: shipping rates and times, returns, warranty, and your business address. Have these checked before launch (see the legal checklist in supply/legal_checklist.md).</span></p>'''
PRIVACY = '''<p>This site does not use tracking cookies. The 3D instructions save your build progress only on your own device
(browser storage). <span class="todo">TODO_LUCAS: update this page when you add a store, analytics or an email list.</span></p>'''

CHECKOUT = '''<section class="wrap checkout">
  <h1>Your cart</h1>
  <div id="cartItems" class="cart-items"><p class="muted">Your cart is empty. <a href="/#kits">See the kits</a>.</p></div>
  <div class="cart-total" id="cartTotal" hidden><span>Subtotal</span><strong id="cartSubtotal">$0.00</strong></div>
  <p class="small muted">Shipping and sales tax are calculated at checkout.</p>
  <button class="btn btn-primary btn-wide" id="checkoutBtn" disabled>Checkout</button>
  <div class="todo-box"><strong>Checkout is not connected yet.</strong>
    <p>TODO_LUCAS: choose one and paste the link or code here: a Shopify store (Buy Button), Stripe Payment Links (one per kit),
    or an Etsy listing for each kit. The cart on this page is only a preview kept in this browser.</p></div>
</section>'''

NOT_FOUND = '''<section class="wrap prose"><h1>Page not found</h1><p>That page does not exist. Try the <a href="/">home page</a> or the
<a href="/build/">3D instructions</a>.</p></section>
<script>
// hosts without rewrites (for example GitHub Pages): send app links to the hash route
if (location.pathname.startsWith('/build/')) {
  const m = location.pathname.match(/^\\/build\\/([\\w-]+)(?:\\/step\\/(\\d+))?/);
  if (m) location.replace('/build/#/' + m[1] + (m[2] ? '/step/' + m[2] : ''));
}
</script>'''


def write(rel, content):
    p = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w').write(content)


def main():
    write('index.html', home())
    for k in KITS:
        write(f'kits/{k["url"]}/index.html', kit_page(k))
        # short links used by the booklet QR codes (/kits/<kit>) forward to the product page
        write(f'kits/{k["kit"]}/index.html', f'<!doctype html><meta charset="utf-8"><title>{E(k["name"])}</title>'
              f'<meta http-equiv="refresh" content="0; url=/kits/{k["url"]}/"><link rel="canonical" href="/kits/{k["url"]}/">'
              f'<a href="/kits/{k["url"]}/">{E(k["name"])}</a>')
    write('faq/index.html', faq())
    for slug, title, desc, inner, active in (
            ('safety', 'Safety', 'Safety notes for Hartwood wooden model kits.', SAFETY, ''),
            ('about', 'About Hartwood Designs', 'Who makes Hartwood wooden model kits.', ABOUT, 'about'),
            ('contact', 'Contact and spare parts', 'Contact Hartwood Designs or order a spare part.', CONTACT, ''),
            ('terms', 'Terms and shipping', 'Terms, shipping and returns.', TERMS, ''),
            ('privacy', 'Privacy', 'Privacy at Hartwood Designs.', PRIVACY, '')):
        s, html_ = text_page(slug, title, desc, inner, active)
        write(f'{slug}/index.html', html_)
    write('checkout/index.html', page('Cart | Hartwood Designs', 'Your cart.', CHECKOUT))
    write('404.html', page('Not found | Hartwood Designs', 'Page not found.', NOT_FOUND))
    print('pages written')


if __name__ == '__main__':
    main()
