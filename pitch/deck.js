// deck.js — Präsentations-Logik: Navigation, Sprecher, Matrix-Regen, Steuerung

(function () {
  // ── State ──
  let currentSlide = 0;
  let speakerVisible = true;
  let voiceEnabled = false;
  let synthVoice = null;
  let typewriterTimer = null;
  const totalSlides = SLIDES.length;

  // ── DOM refs ──
  const deck = document.getElementById('deck');
  const speakerPanel = document.getElementById('speaker-panel');
  const speechBubble = document.querySelector('.speech-bubble');
  const speakerAvatar = document.querySelector('.speaker-avatar');
  const speakerNameEl = document.querySelector('.speaker-name');
  const speakerRoleEl = document.querySelector('.speaker-role');
  const progressFill = document.getElementById('progress-fill');
  const pageIndicator = document.getElementById('page-indicator');
  const overview = document.getElementById('overview');
  const voiceIndicator = document.getElementById('voice-indicator');
  const fsHint = document.getElementById('fs-hint');

  // ── Build slides ──
  SLIDES.forEach(function (slideData, idx) {
    var div = document.createElement('div');
    div.className = 'slide';
    div.id = 'slide-' + idx;
    div.innerHTML = slideData.html();
    deck.appendChild(div);
  });

  var slides = deck.querySelectorAll('.slide');

  // ── Build overview grid ──
  SLIDES.forEach(function (s, i) {
    var thumb = document.createElement('div');
    thumb.className = 'overview-thumb';
    thumb.innerHTML = '<span class="thumb-num">' + String(i + 1).padStart(2, '0') + '</span><span class="thumb-title">' + s.title + '</span>';
    thumb.addEventListener('click', function () { goTo(i); hideOverview(); });
    overview.appendChild(thumb);
  });

  // ── Pixel Avatars ──
  function renderAvatars() {
    var canvases = document.querySelectorAll('.team-avatar-canvas, .speaker-avatar');
    canvases.forEach(function (canvas) {
      var agentId = canvas.getAttribute('data-agent');
      if (agentId) {
        canvas.width = canvas.clientWidth || 64;
        canvas.height = canvas.clientHeight || 56;
        // Check for png fallback
        var img = new Image();
        img.onload = function () {
          var ctx = canvas.getContext('2d');
          ctx.imageSmoothingEnabled = false;
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.onerror = function () {
          drawPixelAvatar(canvas, agentId);
        };
        img.src = 'assets/avatars/' + agentId + '.png';
      }
    });
  }

  // ── Show slide ──
  function showSlide(idx) {
    if (idx < 0 || idx >= totalSlides) return;

    var oldSlide = slides[currentSlide];
    if (oldSlide && oldSlide.classList.contains('active')) {
      oldSlide.classList.remove('active');
      oldSlide.classList.add('exit-wipe');
      setTimeout(function () { oldSlide.classList.remove('exit-wipe'); }, 350);
    }

    currentSlide = idx;
    var newSlide = slides[idx];
    newSlide.classList.add('active', 'enter-glitch');
    setTimeout(function () { newSlide.classList.remove('enter-glitch'); }, 400);

    // Update progress
    var pct = ((idx + 1) / totalSlides) * 100;
    progressFill.style.width = pct + '%';
    pageIndicator.textContent = String(idx + 1).padStart(2, '0') + '/' + String(totalSlides).padStart(2, '0');

    // Update overview
    var thumbs = overview.querySelectorAll('.overview-thumb');
    thumbs.forEach(function (t, i) { t.classList.toggle('active', i === idx); });

    // Glitch title every ~6s
    var glitchTitle = newSlide.querySelector('.glitch-title');
    if (glitchTitle) {
      setInterval(function () {
        if (currentSlide === idx) {
          glitchTitle.classList.add('glitch-active');
          setTimeout(function () { glitchTitle.classList.remove('glitch-active'); }, 180);
        }
      }, 6000);
    }

    // Trigger speaker change
    updateSpeaker(idx);
  }

  // ── Speaker Panel ──
  function updateSpeaker(idx) {
    if (!speakerVisible) {
      speakerPanel.classList.add('hidden');
      return;
    }
    speakerPanel.classList.remove('hidden');

    var slideData = SLIDES[idx];
    var agentId = slideData.speaker;
    var agent = AGENTS[agentId] || AGENTS['timo'];

    speakerNameEl.textContent = agent.name;
    speakerRoleEl.textContent = agent.role;
    speakerAvatar.setAttribute('data-agent', agentId);
    drawPixelAvatar(speakerAvatar, agentId);

    // Typewriter
    typeText(SPEAKER_TEXTS[slideData.id] || '');

    // Text-to-speech
    if (voiceEnabled) speak(SPEAKER_TEXTS[slideData.id] || '');
  }

  function typeText(text) {
    if (typewriterTimer) clearInterval(typewriterTimer);
    speechBubble.classList.remove('speech-cursor');
    speechBubble.textContent = '';

    var i = 0;
    speechBubble.classList.add('speech-cursor');
    typewriterTimer = setInterval(function () {
      if (i < text.length) {
        speechBubble.textContent += text.charAt(i);
        i++;
      } else {
        clearInterval(typewriterTimer);
        speechBubble.classList.remove('speech-cursor');
      }
    }, 30);
  }

  // ── Speech Synthesis ──
  function initVoice() {
    var voices = speechSynthesis.getVoices();
    for (var i = 0; i < voices.length; i++) {
      if (voices[i].lang.startsWith('de')) {
        synthVoice = voices[i];
        break;
      }
    }
    if (!synthVoice && voices.length > 0) synthVoice = voices[0];
  }
  speechSynthesis.onvoiceschanged = initVoice;
  initVoice();

  function speak(text) {
    if (!synthVoice) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    u.voice = synthVoice;
    u.lang = 'de-DE';
    u.rate = 0.95;
    u.pitch = 1.0;
    speechSynthesis.speak(u);
  }

  // ── Navigation ──
  function goTo(idx) {
    if (idx < 0 || idx >= totalSlides) return;
    showSlide(idx);
  }
  function next() { goTo(currentSlide + 1); }
  function prev() { goTo(currentSlide - 1); }

  // ── Overview ──
  function showOverview() {
    overview.classList.add('show');
  }
  function hideOverview() {
    overview.classList.remove('show');
  }
  function toggleOverview() {
    if (overview.classList.contains('show')) hideOverview();
    else showOverview();
  }

  // ── Fullscreen ──
  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function () {});
    } else {
      document.exitFullscreen();
    }
  }
  document.addEventListener('fullscreenchange', function () {
    if (document.fullscreenElement) {
      fsHint.textContent = 'ESC zum Verlassen';
      fsHint.style.opacity = '1';
      setTimeout(function () { fsHint.style.opacity = '0'; }, 3000);
    }
  });

  // ── Keyboard ──
  document.addEventListener('keydown', function (e) {
    if (overview.classList.contains('show')) {
      if (e.key === 'Escape' || e.key === 'o' || e.key === 'O') { hideOverview(); return; }
      return;
    }

    switch (e.key) {
      case 'ArrowRight': case ' ': e.preventDefault(); next(); break;
      case 'ArrowLeft': e.preventDefault(); prev(); break;
      case 'ArrowDown': e.preventDefault(); next(); break;
      case 'ArrowUp': e.preventDefault(); prev(); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 'o': case 'O': toggleOverview(); break;
      case 'n': case 'N':
        speakerVisible = !speakerVisible;
        if (speakerVisible) updateSpeaker(currentSlide);
        else speakerPanel.classList.add('hidden');
        break;
      case 'v': case 'V':
        voiceEnabled = !voiceEnabled;
        voiceIndicator.classList.toggle('on', voiceEnabled);
        voiceIndicator.textContent = voiceEnabled ? 'V: SPRACHE AN' : 'V: Sprache aus';
        if (!voiceEnabled) {
          speechSynthesis.cancel();
          initVoice();
        }
        break;
      case 'Home': e.preventDefault(); goTo(0); break;
      case 'End': e.preventDefault(); goTo(totalSlides - 1); break;
    }
  });

  // ── Click navigation ──
  deck.addEventListener('click', function (e) {
    if (e.target.closest('.speech-bubble') || e.target.closest('#speaker-panel')) return;
    var w = window.innerWidth;
    if (e.clientX > w * 0.65) next();
    else if (e.clientX < w * 0.35) prev();
  });

  // ── Touch swipe ──
  var touchStartX = 0;
  document.addEventListener('touchstart', function (e) { touchStartX = e.touches[0].clientX; });
  document.addEventListener('touchend', function (e) {
    var diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) next();
      else prev();
    }
  });

  // ── Matrix Rain Canvas ──
  (function initRain() {
    var c = document.getElementById('rain');
    if (!c) return;
    var x = c.getContext('2d');
    var w, h, cols, drops;
    function size() { w = c.width = window.innerWidth; h = c.height = window.innerHeight; cols = Math.floor(w / 18); drops = Array(cols).fill(0).map(function () { return Math.random() * h / 18; }); }
    window.addEventListener('resize', size);
    size();
    var G = '01ｱｲｳｴｵｶｷｸｹｺ<>/#$%&*+=-';
    function tick() {
      x.fillStyle = 'rgba(19,14,11,0.12)';
      x.fillRect(0, 0, w, h);
      x.font = '16px VT323';
      drops.forEach(function (d, i) {
        x.fillStyle = Math.random() < 0.15 ? '#39ff14' : '#ff6a1a';
        x.fillText(G[Math.floor(Math.random() * G.length)], i * 18, d * 18);
        drops[i] = d * 18 > h && Math.random() > 0.975 ? 0 : d + 1;
      });
      requestAnimationFrame(tick);
    }
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) tick();
  })();

  // ── Start ──
  showSlide(0);
  voiceIndicator.textContent = 'V: Sprache aus';
  speakerVisible = true;

  // ── Worker-Demo-Glitch ──
  setInterval(function () {
    if (Math.random() < 0.25) {
      var el = document.querySelector('.slide.active .glitch-title');
      if (el) {
        el.classList.add('glitch-active');
        setTimeout(function () { el.classList.remove('glitch-active'); }, 180);
      }
    }
  }, 6000);
})();