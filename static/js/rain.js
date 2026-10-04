(function() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var c = document.getElementById('rainCanvas');
    if (!c) return;
    var x = c.getContext('2d');
    var w, h, cols, drops;

    function size() {
        w = c.width = window.innerWidth;
        h = c.height = window.innerHeight;
        cols = Math.floor(w / 16);
        drops = Array(cols).fill(0).map(function() { return Math.random() * h / 16; });
    }

    window.addEventListener('resize', size);
    size();

    var G = '01ｱｲｳｴｵｶｷｸｹｺ<>/#$%&*+=-';

    function tick() {
        x.fillStyle = 'rgba(19,14,11,.12)';
        x.fillRect(0, 0, w, h);
        x.font = '16px VT323';
        drops.forEach(function(d, i) {
            x.fillStyle = Math.random() < .15 ? '#39ff14' : '#ff6a1a';
            x.fillText(G[Math.floor(Math.random() * G.length)], i * 16, d * 16);
            drops[i] = d * 16 > h && Math.random() > .975 ? 0 : d + 1;
        });
        requestAnimationFrame(tick);
    }

    tick();
})();