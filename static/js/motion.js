'use strict';
/* Cypher News: Bewegung. GSAP + ScrollTrigger + Lenis (lokal in static/vendor, kein CDN, kein Build).
   Regeln: nur transform/opacity animieren, bei prefers-reduced-motion nichts davon (statische Seite, kein Lenis),
   fehlt eine Bibliothek, läuft die App trotzdem (alle Funktionen sind dann ruhige No-Ops). */
(function () {
  var $ = function (id) { return document.getElementById(id); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var G = window.gsap, ST = window.ScrollTrigger;
  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  var live = !!(G && ST) && !mq.matches;     // Bewegung aktiv?
  if (G && ST) { G.registerPlugin(ST); ST.config({ignoreMobileResize: true}); }
  if (live) document.body.classList.add('cin');

  // ── Zeichen-Scramble: die "Entschlüsselung" der Wortmarke (Wiedererkennungsmerkmal) ──
  var GL = 'ABCDEFGHJKLMNPRSTUVXYZ0123456789#%&*+/<>';
  function scramble(el, ms, final) {
    if (!el) return;
    if (final != null) el.dataset.final = final; else if (!el.dataset.final) el.dataset.final = el.textContent;
    var fin = el.dataset.final;
    if (mq.matches) { el.textContent = fin; return; }
    var token = el._scr = {}, t0 = performance.now();
    if (!el.style.minWidth && el.offsetWidth) el.style.minWidth = el.getBoundingClientRect().width + 'px';
    (function step(now) {
      if (el._scr !== token) return;
      var p = Math.min(1, (now - t0) / ms), out = '';
      for (var i = 0; i < fin.length; i++) out += fin[i] === ' ' || fin[i] === ':' || i / fin.length < p * 1.1 - .1 ? fin[i] : GL[Math.floor(Math.random() * GL.length)];
      el.textContent = p < 1 ? out : fin;
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }

  // ── Text teilen: Original bleibt für Screenreader (sr-only), die Wörter sind aria-hidden ──
  function split(el, mask) {
    var text = (el._orig != null ? el._orig : el.textContent).replace(/\s+/g, ' ').trim();
    el._orig = text; el.textContent = '';
    var sr = document.createElement('span'); sr.className = 'sr-only'; sr.textContent = text;
    var vis = document.createElement('span'); vis.className = 'sw-s'; vis.setAttribute('aria-hidden', 'true');
    var words = [];
    text.split(' ').forEach(function (w, i) {
      if (i) vis.appendChild(document.createTextNode(' '));
      var s = document.createElement('span'); s.className = 'sw'; s.textContent = w; words.push(s);
      if (mask) { var m = document.createElement('span'); m.className = 'sw-m'; m.appendChild(s); vis.appendChild(m); } else vis.appendChild(s);
    });
    el.appendChild(sr); el.appendChild(vis);
    return words;
  }
  function unsplit(el) { if (el._orig != null) { el.textContent = el._orig; el._orig = null; } }

  // ── Preloader: endet immer (Schutz 4,5 s hier, 6 s per CSS) ──
  var pl = $('preloader'), plResolve, ready = new Promise(function (r) { plResolve = r; }), started = performance.now(), prog = {v: 0};
  function paint() { var n = $('plNum'), b = $('plBar'); if (n) n.textContent = String(Math.round(prog.v)).padStart(3, '0'); if (b) b.style.transform = 'scaleX(' + prog.v / 100 + ')'; }
  function removePl() { if (pl) pl.classList.add('gone'); plResolve(); }
  if (pl && live) {
    scramble($('plWord'), 900); scramble($('plClock'), 1100, '08:00');
    G.to(prog, {v: 88, duration: 1.5, ease: 'power2.out', onUpdate: paint});
    setTimeout(removePl, 4500);
  } else removePl();

  // boot(session, fonts, onMid): wartet höchstens 2,6 s, dann Abgang; onMid startet die Hero-Szene mit Überlappung
  function boot(session, fonts, onMid) {
    if (!pl || !live || pl.classList.contains('gone')) { removePl(); if (onMid) onMid(); return Promise.resolve(); }
    var minWait = new Promise(function (r) { setTimeout(r, Math.max(0, (session ? 450 : 1050) - (performance.now() - started))); });
    var cap = new Promise(function (r) { setTimeout(r, 2600); });
    return Promise.race([Promise.all([fonts, minWait]), cap]).then(function () {
      return new Promise(function (res) {
        var tl = G.timeline({onComplete: function () { removePl(); res(); }}), inner = $$('.pl-top, .pl-word, .pl-foot', pl);
        tl.to(prog, {v: 100, duration: .35, ease: 'power1.out', onUpdate: paint});
        if (session) { tl.add(function () { if (onMid) onMid(); }, '>'); tl.to(pl, {opacity: 0, duration: .35, ease: 'power1.out'}, '>'); }
        else {
          tl.to(inner, {opacity: 0, y: -18, duration: .35, stagger: .05, ease: 'power2.in'}, '+=.12');
          tl.to(pl, {yPercent: -100, duration: .95, ease: 'power4.inOut'}, '>-.1');
          tl.add(function () { if (onMid) onMid(); }, '>-.55');
        }
      });
    });
  }

  // ── Landingpage: Hero, Manifest, Karten-Stapel, Rauschen->Signal, Fakten, Footer-Enthüllung ──
  var landing = null;
  var TERM = ['drop --morgen 08:00', 'quellen: 14 gelesen', 'rauschen: 1241 verworfen', 'drop: 7 treffer bereit'];
  var NOISE = ['@clubnacht', 'r/berlin', 'werbung', 'repost', '#fyp', 'link in bio', 'gewinnspiel?', 'lol', 'story', 'spam', 'unboxing', 'part 2', 'sponsored', '…', 'thread', 'zufall', 'reel', 'meme', 'rabatt', 'live jetzt'];
  var HITS = ['techno-nacht sa', 'sneaker-drop fr', 'festival-tickets', 'mauerpark heute', 'tech: neues modell', 'trend: kassette', 'giveaway: vinyl'];

  function landingStart() {
    if (!live || landing) return {play: function () {}};
    var root = $('welcome'), lenis = null, tickFn = null, intervals = [], offs = [], splits = [];
    if (window.Lenis) {
      lenis = new window.Lenis({lerp: .09, wheelMultiplier: .95});
      lenis.on('scroll', ST.update);
      tickFn = function (t) { lenis.raf(t * 1000); };
      G.ticker.add(tickFn); G.ticker.lagSmoothing(0);
    }
    var hero, mm;
    var ctx = G.context(function () {
      var heroEl = $$('[data-hero]', root)[0];
      // Hero: Wörter steigen aus der Maske, Rest folgt gestaffelt
      var words = [];
      $$('[data-hero] [data-split]', root).forEach(function (el) { splits.push(el); words = words.concat(split(el, true)); });
      G.set(words, {yPercent: 118}); G.set('[data-hero-in]', {autoAlpha: 0, y: 26}); G.set('[data-clock]', {autoAlpha: 0});
      var clock = $$('[data-clock]', root)[0];
      hero = G.timeline({paused: true, defaults: {ease: 'power4.out'}})
        .to(words, {yPercent: 0, duration: 1.15, stagger: .07}, 0)
        .to('[data-hero-in]', {autoAlpha: 1, y: 0, duration: .95, stagger: .09}, .4)
        .to(clock, {autoAlpha: 1, duration: 1.6}, .2)
        .add(function () { scramble(clock, 1300, '08:00'); }, .25);
      clock.textContent = '00:00'; clock.dataset.final = '08:00';
      // Terminalzeile wechselt ruhig alle 3,4 s (nur sichtbar im Hero)
      var tl = $('termLine'), ti = 0, visible = true;
      var io = new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }); io.observe(heroEl); offs.push(function () { io.disconnect(); });
      intervals.push(setInterval(function () { if (!visible || document.hidden) return; ti = (ti + 1) % TERM.length; scramble(tl, 520, TERM[ti]); }, 3400));
      // Parallax im Hero
      var st = {trigger: heroEl, start: 'top top', end: 'bottom top', scrub: true};
      G.to('[data-glow]', {yPercent: 28, ease: 'none', scrollTrigger: st});
      G.to(clock, {yPercent: -26, ease: 'none', scrollTrigger: st});
      G.to('.l-hero-in', {y: -50, autoAlpha: .15, ease: 'none', scrollTrigger: {trigger: heroEl, start: '55% top', end: 'bottom top', scrub: true}});
      // Zeiger-Parallax der Glut (nur feiner Zeiger)
      if (window.matchMedia('(pointer: fine)').matches) {
        var gx = G.quickTo('[data-glow]', 'x', {duration: 1.2, ease: 'power3'}), gy = G.quickTo('[data-glow]', 'y', {duration: 1.2, ease: 'power3'});
        var mv = function (e) { gx((e.clientX / innerWidth - .5) * -60); gy((e.clientY / innerHeight - .5) * -40); };
        addEventListener('pointermove', mv, {passive: true}); offs.push(function () { removeEventListener('pointermove', mv); });
      }
      // Manifest: Wörter werden beim Scrollen hell
      $$('[data-scrub]', root).forEach(function (el) {
        splits.push(el); var ws = split(el, false);
        G.set(ws, {opacity: .16});
        G.to(ws, {opacity: 1, ease: 'none', stagger: {each: .12}, duration: .3, scrollTrigger: {trigger: el, start: 'top 80%', end: 'bottom 52%', scrub: .5}});
      });
      // Überschriften und Fakten: einmalig einblenden
      $$('.l-final [data-split]', root).forEach(function (el) {
        splits.push(el);
        G.from(split(el, true), {yPercent: 118, duration: 1.1, stagger: .08, ease: 'power4.out', scrollTrigger: {trigger: el, start: 'top 85%', once: true}});
      });
      $$('.l-sec-head > *, [data-fact], .l-final .l-btn, .sig-sub', root).forEach(function (el) {
        G.from(el, {y: 44, autoAlpha: 0, duration: 1, ease: 'power4.out', scrollTrigger: {trigger: el, start: 'top 88%', once: true}});
      });
      // Karten-Stapel: Inhalt erscheint, die vorige Karte tritt zurück
      var cards = $$('[data-card]', root);
      cards.forEach(function (card, i) {
        var kids = $$('.viz-src span, .viz-pick li, .viz-drop > *', card);
        G.from(kids, {y: 22, autoAlpha: 0, duration: .8, stagger: .07, ease: 'power3.out', scrollTrigger: {trigger: card, start: 'top 78%', once: true}});
        var next = cards[i + 1];
        if (next) G.to(card, {scale: .93 + i * .02, y: -10, ease: 'none', scrollTrigger: {trigger: next, start: 'top 92%', end: function () { return 'top ' + (76 + (i + 1) * 16) + 'px'; }, scrub: true, invalidateOnRefresh: true}});
      });
      // Rauschen -> Signal (Desktop angeheftet, Mobil frei laufend)
      var sec = $$('[data-signal]', root)[0], noise = $$('[data-noise]', root)[0], num = $$('[data-sig-num]', root)[0];
      var frag = document.createDocumentFragment(), hits = [], junk = [], pool = [];
      for (var k = 0; k < 78; k++) pool.push(NOISE[(k * 7 + (k >> 2)) % NOISE.length]);
      HITS.forEach(function (h, idx) { pool.splice(6 + idx * 11, 0, h); });
      pool.forEach(function (w) { var s = document.createElement('span'), isHit = HITS.indexOf(w) > -1; s.textContent = w; if (isHit) { s.className = 'hit'; hits.push(s); } else junk.push(s); frag.appendChild(s); });
      noise.appendChild(frag); offs.push(function () { noise.textContent = ''; });
      var cnt = {n: 1248};
      var sig = G.timeline({defaults: {ease: 'none'}})
        .to(junk, {autoAlpha: 0, duration: 1, stagger: {amount: .8, from: 'random'}}, 0)
        .to(hits, {scale: 1.35, duration: 1}, .2)
        .to(noise, {opacity: .8, duration: 1}, 0)
        .to(cnt, {n: 7, duration: 1.3, snap: {n: 1}, onUpdate: function () { num.textContent = cnt.n; }}, 0);
      mm = G.matchMedia();
      mm.add('(min-width: 900px)', function () {
        ST.create({animation: sig, trigger: sec, start: 'top top', end: '+=120%', scrub: 1, pin: true, anticipatePin: 1});
      });
      mm.add('(max-width: 899.98px)', function () {
        ST.create({animation: sig, trigger: sec, start: 'top 70%', end: 'bottom 45%', scrub: .8});
      });
      // Footer: Wortmarke fährt wie ein Vorhang hoch
      var foot = $$('[data-foot]', root)[0];
      G.fromTo('[data-foot-in]', {yPercent: -40}, {yPercent: 0, ease: 'none', scrollTrigger: {trigger: foot, start: 'top bottom', end: 'bottom bottom', scrub: true}});
    }, root);
    var onTop = function (e) { var a = e.target.closest && e.target.closest('a[href="#landMain"]'); if (a && lenis) { e.preventDefault(); lenis.scrollTo(0); } };
    root.addEventListener('click', onTop); offs.push(function () { root.removeEventListener('click', onTop); });
    var refresh = function () { ST.refresh(); };
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(refresh);
    addEventListener('load', refresh); offs.push(function () { removeEventListener('load', refresh); });
    landing = {
      stop: function () {
        intervals.forEach(clearInterval); offs.forEach(function (f) { f(); });
        if (mm) mm.revert(); ctx.revert(); splits.forEach(unsplit);
        if (lenis) { G.ticker.remove(tickFn); lenis.destroy(); }
        $$('[data-clock]', root).forEach(function (c) { c.textContent = '08:00'; });
        landing = null;
      }
    };
    return {play: function () { hero.play(0); }};
  }
  function landingStop() { if (landing) landing.stop(); }

  // ── App: Übergänge, Enthüllung des Drops, Mikro-Interaktionen ──
  function pageIn(el) {
    if (!live || !el) return;
    var kids = $$(':scope > *', el); G.killTweensOf(kids);
    G.fromTo(kids, {y: 14, autoAlpha: 0}, {y: 0, autoAlpha: 1, duration: .55, stagger: .05, ease: 'power3.out', clearProps: 'transform,opacity,visibility'});
  }
  function tabInd(btn) {
    var ind = $('tabInd'); if (!ind || !btn || !btn.offsetWidth) return;
    if (window.matchMedia('(min-width: 960px)').matches) ind.style.setProperty('--y', (btn.offsetTop + (btn.offsetHeight - 18) / 2) + 'px');
    else ind.style.setProperty('--x', (btn.offsetLeft + btn.offsetWidth / 2 - 14) + 'px');
  }
  var revealSt = [];
  function wipeCards(cards) {
    // Abtastlinie: eine Abdeckung fährt nach unten weg und deckt den Text auf
    var covers = cards.map(function (c) { var cv = document.createElement('i'); cv.className = 'rv-cover'; c.appendChild(cv); return cv; });
    var t0 = 0;
    cards.forEach(function (c, i) {
      var cv = covers[i], play = function (delay) {
        G.timeline({delay: delay, onComplete: function () { cv.remove(); }})
          .fromTo(cv, {scaleY: 1}, {scaleY: 0, transformOrigin: '50% 100%', duration: .85, ease: 'power3.inOut'}, 0)
          .from(c.children, {y: 18, duration: .8, ease: 'power3.out', stagger: .03, clearProps: 'transform'}, .05);
      };
      var r = c.getBoundingClientRect();
      if (r.top < innerHeight * .95) play(t0++ * .11);
      else revealSt.push(ST.create({trigger: c, start: 'top 94%', once: true, onEnter: function () { play(0); }}));
    });
    setTimeout(function () { covers.forEach(function (cv) { cv.remove(); }); }, 8000);  // Schutz: nie verdeckt lassen
  }
  function revealDrop(viewIsFeed) {
    if (!live) return;
    revealSt.forEach(function (s) { s.kill(); }); revealSt = [];
    ready.then(function () {
      var title = $('introTitle'), strong = $$('#introCount strong')[0], n = strong ? +strong.textContent : 0, c = {n: 0};
      var tw = split(title, true); G.set(tw, {yPercent: 118});
      var tl = G.timeline({defaults: {ease: 'power4.out'}});
      tl.from('.lede-date', {autoAlpha: 0, y: 12, duration: .6}, 0)
        .to(tw, {yPercent: 0, duration: 1.05, stagger: .06}, .08);
      if (strong) tl.to(c, {n: n, duration: .9, ease: 'power2.out', snap: {n: 1}, onUpdate: function () { strong.textContent = c.n; }}, .25);
      tl.from('#introCount, #introText, #introModel, #introFailed', {autoAlpha: 0, y: 16, duration: .7, stagger: .08}, .4)
        .from('.toolbar, #storyProgress, #catFilters', {autoAlpha: 0, y: 12, duration: .6, stagger: .05, clearProps: 'transform,opacity,visibility'}, .6);
      var cards = viewIsFeed ? $$('#feedContainer .feed-card') : $$('#storiesInner .story-card').slice(0, 2);
      if (cards.length) wipeCards(cards);
    });
  }
  function burst(b, kind) {
    if (!live || !b) return;
    var ico = b.querySelector('.ico');
    if (ico) {
      if (kind === 'save') G.fromTo(ico, {scale: .7, rotate: -10}, {keyframes: {scale: [.7, 1.22, 1], rotate: [-10, 4, 0]}, duration: .55, ease: 'power3.out'});
      else G.fromTo(ico, {y: 0, rotate: 0}, {keyframes: {y: [0, kind === 'up' ? -5 : 5, 0], rotate: [0, kind === 'up' ? -14 : 14, 0]}, duration: .5, ease: 'power3.out'});
    }
    if (kind === 'down') return;
    for (var i = 0; i < 7; i++) {
      var s = document.createElement('i'); s.className = 'spark'; b.appendChild(s);
      var a = (i / 7) * Math.PI * 2 + Math.random() * .5, d = 20 + Math.random() * 12;
      G.fromTo(s, {x: 0, y: 0, scale: 1, autoAlpha: 1}, {x: Math.cos(a) * d, y: Math.sin(a) * d, scale: 0, autoAlpha: 0, duration: .6 + Math.random() * .2, ease: 'power3.out', onComplete: (function (el) { return function () { el.remove(); }; })(s)});
    }
  }

  window.CNMotion = {
    live: function () { return live; }, ready: ready, boot: boot, scramble: scramble,
    landingStart: landingStart, landingStop: landingStop,
    pageIn: pageIn, tabInd: tabInd, revealDrop: revealDrop, burst: burst,
    refresh: function () { if (live) ST.refresh(); }
  };
})();
