// deck.js — Pitch presentation: 3-pixel-speaker panel, PLAY TALK auto-play, audio sync
(function () {
  // ── State ──
  var currentSlide = 0;
  var mute = true;
  var isPlaying = false;
  var isPaused = false;
  var manualMode = false;
  var talkFrameTimer = null;
  var typewriterTimer = null;
  var playTimeout = null;
  var totalSlides = SLIDES.length;

  // ── DOM refs ──
  var deck = document.getElementById('deck');
  var speakerBar = document.getElementById('speaker-bar');
  var speechBubble = document.getElementById('speech-bubble');
  var progressFill = document.getElementById('progress-fill');
  var pageIndicator = document.getElementById('page-indicator');
  var overview = document.getElementById('overview');
  var muteIndicator = document.getElementById('mute-indicator');
  var playBtn = document.getElementById('play-btn');
  var fsHint = document.getElementById('fs-hint');

  // ── Audio context ──
  var audioEl = null;
  var audioManifest = (typeof window.AUDIO === 'object') ? window.AUDIO : {};
  var speakersOnBar = ['ran', 'rufus', 'jaro'];

  // ── Build slides ──
  for (var i = 0; i < SLIDES.length; i++) {
    var div = document.createElement('div');
    div.className = 'slide';
    div.id = 'slide-' + i;
    div.innerHTML = SLIDES[i].html();
    deck.appendChild(div);
  }
  var slides = deck.querySelectorAll('.slide');

  // ── Build overview grid ──
  for (var oi = 0; oi < SLIDES.length; oi++) {
    var s = SLIDES[oi];
    var thumb = document.createElement('div');
    thumb.className = 'overview-thumb';
    thumb.innerHTML = '<span class="thumb-num">' + String(oi + 1).padStart(2, '0') + '</span><span class="thumb-title">' + s.title + '</span>';
    thumb.addEventListener('click', (function (idx) { return function () { stopAutoPlay(); goTo(idx); hideOverview(); }; })(oi));
    overview.appendChild(thumb);
  }

  // ── Load speaker bar PNG avatars ──
  for (var ai = 0; ai < speakersOnBar.length; ai++) {
    var agentId = speakersOnBar[ai];
    var wrapper = document.getElementById('spkr-' + agentId);
    if (!wrapper) continue;
    var img = document.createElement('img');
    img.className = 'spkr-img';
    img.src = 'assets/avatars/' + agentId + '.png';
    img.alt = agentId;
    wrapper.appendChild(img);
  }

  // ── Load team PNG avatars (on team slide) ──
  function loadTeamAvatars() {
    var canvases = document.querySelectorAll('.team-avatar-canvas');
    for (var ci = 0; ci < canvases.length; ci++) {
      var canvas = canvases[ci];
      var agentId = canvas.getAttribute('data-agent');
      if (!agentId) continue;
      canvas.width = canvas.clientWidth || 64;
      canvas.height = canvas.clientHeight || 64;
      var img = new Image();
      img.onload = (function (c) { return function () {
        var ctx = c.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(img, 0, 0, c.width, c.height);
      }; })(canvas);
      img.src = 'assets/avatars/' + agentId + '.png';
    }
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

    var pct = ((idx + 1) / totalSlides) * 100;
    progressFill.style.width = pct + '%';
    pageIndicator.textContent = String(idx + 1).padStart(2, '0') + '/' + String(totalSlides).padStart(2, '0');

    var thumbs = overview.querySelectorAll('.overview-thumb');
    for (var ti = 0; ti < thumbs.length; ti++) thumbs[ti].classList.toggle('active', ti === idx);

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

    updateSpeaker(idx);

    // Load team avatars if on team slide
    if (SLIDES[idx].id === 's10') {
      setTimeout(loadTeamAvatars, 100);
    }

    // Manual mode: play audio on slide enter
    if (manualMode && !mute && isPlaying) {
      playSlideAudio(idx);
    }
  }

  // ── Speaker panel logic ──
  function updateSpeaker(idx) {
    var slideData = SLIDES[idx];
    var activeSpeaker = slideData.speaker || 'jaro';
    var scriptEntry = (typeof window.SCRIPT !== 'undefined' && window.SCRIPT[idx]) ? window.SCRIPT[idx] : null;
    var text = scriptEntry ? scriptEntry.text : '';

    // Highlight active speaker, dim others
    for (var si = 0; si < speakersOnBar.length; si++) {
      var sp = speakersOnBar[si];
      var wrapper = document.getElementById('spkr-' + sp);
      if (wrapper) {
        wrapper.classList.toggle('speaking', sp === activeSpeaker);
        wrapper.classList.toggle('dimmed', sp !== activeSpeaker);
      }
    }

    // Show speech bubble text with typewriter
    typeText(text);

    // Set speech bubble position above speaking avatar
    positionBubble(activeSpeaker);
  }

  function positionBubble(agentId) {
    var wrapper = document.getElementById('spkr-' + agentId);
    if (!wrapper) return;
    var rect = wrapper.getBoundingClientRect();
    var barRect = speakerBar.getBoundingClientRect();
    speechBubble.style.left = (rect.left + rect.width / 2) + 'px';
    speechBubble.style.bottom = (window.innerHeight - barRect.top + 10) + 'px';
  }

  var talkFrameInterval = null;
  function startTalkFrames() {
    if (talkFrameInterval) return;
    function toggleTalk() {
      var active = speakerBar.querySelector('.spkr-wrap.speaking');
      if (!active) return;
      var img = active.querySelector('.spkr-img');
      if (!img) return;
      var agentId = active.id.replace('spkr-', '');
      var current = img.src;
      if (current.indexOf('_talk') >= 0) {
        img.src = 'assets/avatars/' + agentId + '.png';
      } else {
        img.src = 'assets/avatars/' + agentId + '_talk.png';
      }
    }
    talkFrameInterval = setInterval(toggleTalk, 160);
  }

  function stopTalkFrames() {
    if (talkFrameInterval) { clearInterval(talkFrameInterval); talkFrameInterval = null; }
    // Reset all to normal frame
    for (var si = 0; si < speakersOnBar.length; si++) {
      var sp = speakersOnBar[si];
      var wrapper = document.getElementById('spkr-' + sp);
      if (!wrapper) continue;
      var img = wrapper.querySelector('.spkr-img');
      if (img) img.src = 'assets/avatars/' + sp + '.png';
    }
  }

  // ── Typewriter ──
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
        typewriterTimer = null;
        speechBubble.classList.remove('speech-cursor');
      }
    }, 30);
  }

  function typeTextWithSpeed(text, totalMs) {
    if (typewriterTimer) clearInterval(typewriterTimer);
    speechBubble.classList.remove('speech-cursor');
    speechBubble.textContent = '';

    var i = 0;
    if (!text.length) return;
    var interval = Math.max(25, totalMs / text.length);
    speechBubble.classList.add('speech-cursor');
    typewriterTimer = setInterval(function () {
      if (i < text.length) {
        speechBubble.textContent += text.charAt(i);
        i++;
      } else {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
        speechBubble.classList.remove('speech-cursor');
      }
    }, interval);
  }

  // ── Audio playback ──
  function playSlideAudio(idx) {
    if (mute) return;
    stopAudio();
    var entry = SLIDES[idx];
    if (!entry || !audioManifest[entry.id]) return;
    var audioFile = audioManifest[entry.id].file;
    var duration = audioManifest[entry.id].duration * 1000;

    audioEl = new Audio(audioFile);
    audioEl.play().catch(function () {});

    // Sync typewriter
    var scriptEntry = window.SCRIPT && window.SCRIPT[idx];
    if (scriptEntry) {
      typeTextWithSpeed(scriptEntry.text, duration);
    }

    startTalkFrames();

    audioEl.onended = function () {
      stopTalkFrames();
      audioEl = null;
    };
  }

  function stopAudio() {
    stopTalkFrames();
    if (audioEl) {
      audioEl.pause();
      audioEl = null;
    }
  }

  // ── Auto-play ──
  function stopAutoPlay() {
    isPlaying = false;
    isPaused = false;
    manualMode = false;
    stopAudio();
    if (typewriterTimer) { clearInterval(typewriterTimer); typewriterTimer = null; }
    if (talkFrameInterval) { clearInterval(talkFrameInterval); talkFrameInterval = null; }
    if (playTimeout) { clearTimeout(playTimeout); playTimeout = null; }
    // Reset all to normal frames
    for (var si = 0; si < speakersOnBar.length; si++) {
      var sp = speakersOnBar[si];
      var wrapper = document.getElementById('spkr-' + sp);
      if (!wrapper) continue;
      var img = wrapper.querySelector('.spkr-img');
      if (img) img.src = 'assets/avatars/' + sp + '.png';
    }
    if (playBtn) { playBtn.classList.remove('playing'); playBtn.textContent = 'PLAY TALK'; }
  }

  function startAutoPlay() {
    if (isPlaying && !isPaused) return;
    if (isPaused) {
      // Resume
      isPaused = false;
      manualMode = false;
      if (!mute) {
        playSlideAudio(currentSlide);
      }
      scheduleNextSlide();
      if (playBtn) { playBtn.classList.add('playing'); playBtn.textContent = 'PAUSE'; }
      return;
    }

    isPlaying = true;
    isPaused = false;
    manualMode = false;
    currentSlide = 0;
    showSlide(currentSlide);
    if (!mute) {
      playSlideAudio(currentSlide);
    }
    scheduleNextSlide();
    if (playBtn) { playBtn.classList.add('playing'); playBtn.textContent = 'PAUSE'; }
  }

  function scheduleNextSlide() {
    if (playTimeout) clearTimeout(playTimeout);
    if (!isPlaying || isPaused) return;

    var entry = SLIDES[currentSlide];
    var duration = (audioManifest[entry.id] && audioManifest[entry.id].duration * 1000) || 8000;
    var pause = 700;

    playTimeout = setTimeout(function () {
      if (!isPlaying || isPaused) return;
      stopTalkFrames();
      if (currentSlide + 1 < totalSlides) {
        currentSlide++;
        showSlide(currentSlide);
        if (!mute) playSlideAudio(currentSlide);
        scheduleNextSlide();
      } else {
        // End of presentation
        stopAutoPlay();
      }
    }, duration + pause);
  }

  function togglePause() {
    if (!isPlaying) { startAutoPlay(); return; }
    if (isPaused) {
      isPaused = false;
      manualMode = false;
      if (!mute) playSlideAudio(currentSlide);
      scheduleNextSlide();
      if (playBtn) { playBtn.classList.add('playing'); playBtn.textContent = 'PAUSE'; }
    } else {
      isPaused = true;
      stopAudio();
      if (typewriterTimer) { clearInterval(typewriterTimer); typewriterTimer = null; }
      if (playTimeout) { clearTimeout(playTimeout); playTimeout = null; }
      stopTalkFrames();
      if (playBtn) { playBtn.classList.remove('playing'); playBtn.textContent = 'PLAY TALK'; }
    }
  }

  // ── Navigation ──
  function goTo(idx) {
    if (idx < 0 || idx >= totalSlides) return;
    var wasPlaying = isPlaying && !isPaused;
    if (wasPlaying) {
      // Manual override: stop auto but keep playing flag for audio
      manualMode = true;
      if (playTimeout) { clearTimeout(playTimeout); playTimeout = null; }
    }
    showSlide(idx);
  }

  function next() {
    stopAudio();
    goTo(currentSlide + 1);
  }

  function prev() {
    stopAudio();
    goTo(currentSlide - 1);
  }

  // ── Overview ──
  function showOverview() { overview.classList.add('show'); }
  function hideOverview() { overview.classList.remove('show'); }
  function toggleOverview() { if (overview.classList.contains('show')) hideOverview(); else showOverview(); }

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
      fsHint.textContent = 'ESC to exit';
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
      case 'ArrowRight': e.preventDefault(); if (isPlaying) { manualMode = true; if (playTimeout) { clearTimeout(playTimeout); playTimeout = null; } } stopAutoPlay(); next(); break;
      case 'ArrowLeft': e.preventDefault(); if (isPlaying) { manualMode = true; if (playTimeout) { clearTimeout(playTimeout); playTimeout = null; } } stopAutoPlay(); prev(); break;
      case 'ArrowDown': e.preventDefault(); next(); break;
      case 'ArrowUp': e.preventDefault(); prev(); break;
      case ' ': e.preventDefault(); togglePause(); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 'o': case 'O': toggleOverview(); break;
      case 'm': case 'M':
        mute = !mute;
        muteIndicator.classList.toggle('on', !mute);
        muteIndicator.textContent = mute ? 'M: MUTED' : 'M: SOUND ON';
        if (mute) stopAudio(); else if (isPlaying && !isPaused) playSlideAudio(currentSlide);
        break;
      case 'Home': e.preventDefault(); stopAutoPlay(); goTo(0); break;
      case 'End': e.preventDefault(); stopAutoPlay(); goTo(totalSlides - 1); break;
    }
  });

  // ── Click navigation ──
  deck.addEventListener('click', function (e) {
    if (e.target.closest('#speaker-bar') || e.target.closest('#speech-bubble') || e.target.closest('#play-btn')) return;
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

  // ── Play button ──
  if (playBtn) {
    playBtn.addEventListener('click', function () {
      if (isPlaying && !isPaused) {
        togglePause();
      } else {
        startAutoPlay();
      }
    });
  }

  // ── Matrix Rain Canvas ──
  (function initRain() {
    var c = document.getElementById('rain');
    if (!c) return;
    var x = c.getContext('2d');
    var w, h, cols, drops;
    function size() { w = c.width = window.innerWidth; h = c.height = window.innerHeight; cols = Math.floor(w / 18); drops = Array(cols).fill(0).map(function () { return Math.random() * h / 18; }); }
    window.addEventListener('resize', size);
    size();
    var G = '01\uFF71\uFF72\uFF73\uFF74\uFF75\uFF76\uFF77\uFF78\uFF79\uFF7A<>/#$%&*+=-';
    function tick() {
      x.fillStyle = 'rgba(19,14,11,0.12)';
      x.fillRect(0, 0, w, h);
      x.font = '16px VT323';
      for (var di = 0; di < drops.length; di++) {
        x.fillStyle = Math.random() < 0.15 ? '#39ff14' : '#ff6a1a';
        x.fillText(G[Math.floor(Math.random() * G.length)], di * 18, drops[di] * 18);
        drops[di] = drops[di] * 18 > h && Math.random() > 0.975 ? 0 : drops[di] + 1;
      }
      requestAnimationFrame(tick);
    }
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) tick();
  })();

  // ── Window resize: reposition bubble ──
  window.addEventListener('resize', function () {
    var slideData = SLIDES[currentSlide];
    if (slideData) positionBubble(slideData.speaker);
  });

  // ── Start ──
  showSlide(0);
  muteIndicator.textContent = 'M: MUTED';

  // ── Periodic glitch ──
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