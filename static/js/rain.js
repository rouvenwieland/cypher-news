/* Zeichenregen: läuft nur, wenn er sichtbar ist (Willkommen, Ladezustand). Sonst steht die Schleife still. */
(function () {
    var c = document.getElementById('rainCanvas');
    if (!c || window.matchMedia('(prefers-reduced-motion: reduce)').matches) { window.CypherRain = {start: function () {}, stop: function () {}}; return; }
    var x = c.getContext('2d'), w, h, cols, drops, raf = 0, last = 0, STEP = 16, GLYPHS = '01<>/#$%&*+=-ｱｲｳｴｵｶｷｸｹｺ';

    function size() {
        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        w = window.innerWidth; h = window.innerHeight;
        c.width = w * dpr; c.height = h * dpr;
        x.setTransform(dpr, 0, 0, dpr, 0, 0);
        cols = Math.floor(w / STEP);
        drops = Array(cols).fill(0).map(function () { return Math.random() * h / STEP; });
    }
    function ember() { return getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#ff6a2b'; }

    function tick(t) {
        raf = requestAnimationFrame(tick);
        if (t - last < 70) return;  // ~14 Bilder pro Sekunde: ruhig und sparsam
        last = t;
        x.globalCompositeOperation = 'destination-out'; x.fillStyle = 'rgba(0,0,0,.14)'; x.fillRect(0, 0, w, h);
        x.globalCompositeOperation = 'source-over';
        x.font = STEP + 'px ui-monospace, Consolas, monospace'; x.fillStyle = ember();
        for (var i = 0; i < cols; i++) {
            x.fillText(GLYPHS[Math.floor(Math.random() * GLYPHS.length)], i * STEP, drops[i] * STEP);
            drops[i] = drops[i] * STEP > h && Math.random() > .975 ? 0 : drops[i] + 1;
        }
    }
    window.addEventListener('resize', function () { if (raf) size(); });
    window.CypherRain = {
        start: function () { if (raf) return; size(); x.clearRect(0, 0, w, h); raf = requestAnimationFrame(tick); },
        stop: function () { if (!raf) return; setTimeout(function () { if (!document.body.classList.contains('rain-on') && raf) { cancelAnimationFrame(raf); raf = 0; } }, 900); }
    };
})();
