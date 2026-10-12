// Site behaviour: mobile menu, product gallery, a preview cart kept in this browser.
(function () {
  const $ = s => document.querySelector(s);
  const store = {
    get() { try { return JSON.parse(localStorage.getItem('hw:cart')) || []; } catch { return []; } },
    set(v) { try { localStorage.setItem('hw:cart', JSON.stringify(v)); } catch { /* storage blocked: cart lasts for this page only */ } },
  };
  let mem = store.get();
  const save = v => { mem = v; store.set(v); renderCount(); };

  // menu
  const t = $('.nav-toggle'), nav = $('#siteNav');
  if (t && nav) t.addEventListener('click', () => { const o = nav.classList.toggle('open'); t.setAttribute('aria-expanded', String(o)); });

  // cart count badge
  function renderCount() {
    const n = mem.reduce((a, b) => a + b.qty, 0);
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = n; el.toggleAttribute('data-zero', n === 0); });
  }
  renderCount();

  // add to cart
  document.querySelectorAll('[data-add-to-cart]').forEach(b => b.addEventListener('click', () => {
    const kit = b.dataset.addToCart, items = mem.slice();
    const it = items.find(i => i.kit === kit);
    if (it) it.qty += 1; else items.push({ kit, name: b.dataset.name, price: +b.dataset.price, qty: 1 });
    save(items);
    b.textContent = 'Added to cart';
    setTimeout(() => { b.textContent = 'Add to cart'; }, 1800);
  }));

  // gallery
  const main = $('#mainShot');
  document.querySelectorAll('.thumb').forEach(th => th.addEventListener('click', () => {
    document.querySelectorAll('.thumb').forEach(x => x.classList.remove('active'));
    th.classList.add('active'); main.src = th.dataset.src; main.alt = th.getAttribute('aria-label');
  }));

  // checkout preview
  const list = $('#cartItems');
  if (list) {
    const draw = () => {
      if (!mem.length) { list.innerHTML = '<p class="muted">Your cart is empty. <a href="/#kits">See the kits</a>.</p>'; $('#cartTotal').hidden = true; return; }
      list.innerHTML = mem.map((i, k) => `<div class="cart-row"><img src="/assets/kits/${i.kit}/renders/three_quarter_sm.webp" alt="">
        <div><strong>${i.name}</strong><br><span class="qty"><button aria-label="One less" data-d="-1" data-k="${k}">-</button>${i.qty}
        <button aria-label="One more" data-d="1" data-k="${k}">+</button></span></div><strong>$${(i.price * i.qty).toFixed(2)}</strong></div>`).join('');
      $('#cartTotal').hidden = false;
      $('#cartSubtotal').textContent = '$' + mem.reduce((a, b) => a + b.price * b.qty, 0).toFixed(2);
      list.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
        const items = mem.slice(); const it = items[+b.dataset.k]; it.qty += +b.dataset.d;
        save(items.filter(x => x.qty > 0)); draw();
      }));
    };
    draw();
  }
})();
