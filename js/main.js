/*
 * Scroll orchestration: Lenis (smooth momentum scroll) driving GSAP's
 * ticker, ScrollTrigger firing the reveal / mood / nav work off that same
 * clock. Kept as one flat file on purpose — there is one page, one
 * scrollytelling script, no build step; edit in place and reload.
 */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  // Lenis owns scroll position; the browser's own jump-to-#hash on load
  // races it and used to leave the page blank at a deep link. Take manual
  // control and replay the jump ourselves once everything below is ready.
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  const initialHash = location.hash ? location.hash.slice(1) : null;
  window.scrollTo(0, 0);

  /* ---------------- language switch ---------------- */
  /* The head bootstrap script (template.html) handles geolocation and
     redirecting; this just highlights the current language and remembers
     an explicit click so it sticks on the next visit. */
  (function setupLangSwitch() {
    const nav = document.getElementById("lang-switch");
    if (!nav) return;
    const current = document.documentElement.lang || "ru";
    nav.querySelectorAll("a").forEach((a) => {
      a.classList.toggle("active", a.dataset.lang === current);
      a.addEventListener("click", () => {
        try { localStorage.setItem("iqj-lang", a.dataset.lang); } catch (e) {}
      });
    });
  })();

  gsap.registerPlugin(ScrollTrigger);

  /* ---------------- Lenis smooth scroll ---------------- */

  let lenis = null;
  if (!reduceMotion) {
    lenis = new Lenis({
      duration: 1.1,
      easing: (t) => 1 - Math.pow(1 - t, 3),
      smoothWheel: true,
    });
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((time) => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
  }

  window.__lenis = lenis;

  function scrollToTarget(id) {
    const el = document.getElementById(id);
    if (!el) return;
    if (lenis) lenis.scrollTo(el, { offset: 0, duration: 1.3 });
    else el.scrollIntoView({ behavior: "smooth" });
  }

  /* ---------------- paragraph / list reveals ---------------- */

  gsap.utils.toArray(".reveal").forEach((el) => {
    if (reduceMotion) {
      el.style.opacity = 1;
      el.style.transform = "none";
      return;
    }
    gsap.fromTo(
      el,
      { opacity: 0, y: 28 },
      {
        opacity: 1,
        y: 0,
        duration: 0.9,
        ease: "power2.out",
        scrollTrigger: {
          trigger: el,
          start: "top 88%",
          toggleActions: "play none none reverse",
        },
      }
    );
  });

  /* ---------------- chapter dividers ---------------- */

  gsap.utils.toArray(".book-divider").forEach((div) => {
    const roman = div.querySelector(".book-roman");
    const title = div.querySelector(".reveal-title");
    // Not every divider has a roman numeral (Заключение, Садхана,
    // Аксиоматика, Словарь aren't numbered "books"), but the title must
    // still be animated in - otherwise it stays at the CSS default
    // opacity:0 for .reveal-title forever.
    if (!title) return;

    if (roman) gsap.set(roman, { opacity: 0, y: 24 });
    gsap.set(title, { opacity: 0, scale: 0.92, y: 16 });

    if (reduceMotion) {
      gsap.set([roman, title].filter(Boolean), { opacity: 1, y: 0, scale: 1 });
      return;
    }

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: div,
        start: "top 65%",
        toggleActions: "play none none reverse",
      },
    });
    if (roman) {
      tl.to(roman, { opacity: 1, y: 0, duration: 1.0, ease: "power2.out" }).to(
        title,
        { opacity: 1, scale: 1, y: 0, duration: 1.1, ease: "power3.out" },
        "-=0.55"
      );
    } else {
      tl.to(title, { opacity: 1, scale: 1, y: 0, duration: 1.1, ease: "power3.out" });
    }
  });

  /* ---------------- mood-driven background ---------------- */

  gsap.utils.toArray("[data-mood]").forEach((section) => {
    const mood = section.dataset.mood;
    ScrollTrigger.create({
      trigger: section,
      start: "top 55%",
      end: "bottom 45%",
      onEnter: () => window.setInkMood && window.setInkMood(mood),
      onEnterBack: () => window.setInkMood && window.setInkMood(mood),
    });
  });

  /* ---------------- progress rail ---------------- */

  gsap.to("#progress-fill", {
    width: "100%",
    ease: "none",
    scrollTrigger: {
      trigger: document.body,
      start: "top top",
      end: "bottom bottom",
      scrub: 0.3,
    },
  });

  /* ---------------- side nav: click-to-scroll + active state ---------------- */

  const navDots = gsap.utils.toArray(".nav-dot");
  navDots.forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      scrollToTarget(a.dataset.target);
    });
  });

  navDots.forEach((a) => {
    const target = document.getElementById(a.dataset.target);
    if (!target) return;
    ScrollTrigger.create({
      trigger: target,
      start: "top 60%",
      end: "bottom 40%",
      onEnter: () => setActiveDot(a),
      onEnterBack: () => setActiveDot(a),
    });
  });

  function setActiveDot(active) {
    navDots.forEach((d) => d.classList.toggle("active", d === active));
  }

  /* ---------------- ambient sound toggle ---------------- */
  /* A small generated drone + filtered noise standing in for the sound of
     water over a riverbed. No audio file: two oscillators, filtered noise,
     and a slow LFO on the filter cutoff. Created lazily on first click,
     since browsers require a user gesture before audio can start. */

  (function setupSound() {
    const btn = document.getElementById("sound-toggle");
    if (!btn) return;
    let ctx = null;
    let nodes = null;
    let on = false;

    function build() {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      const master = ctx.createGain();
      master.gain.value = 0;
      master.connect(ctx.destination);

      // low drone
      const osc1 = ctx.createOscillator();
      osc1.type = "sine";
      osc1.frequency.value = 55;
      const osc2 = ctx.createOscillator();
      osc2.type = "sine";
      osc2.frequency.value = 82.5;
      const droneGain = ctx.createGain();
      droneGain.gain.value = 0.25;
      osc1.connect(droneGain);
      osc2.connect(droneGain);

      // filtered noise (river texture)
      const bufferSize = 2 * ctx.sampleRate;
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      noise.loop = true;
      const noiseFilter = ctx.createBiquadFilter();
      noiseFilter.type = "bandpass";
      noiseFilter.frequency.value = 700;
      noiseFilter.Q.value = 0.6;
      const noiseGain = ctx.createGain();
      noiseGain.gain.value = 0.06;
      noise.connect(noiseFilter).connect(noiseGain);

      // slow LFO breathing the filter
      const lfo = ctx.createOscillator();
      lfo.type = "sine";
      lfo.frequency.value = 0.06;
      const lfoGain = ctx.createGain();
      lfoGain.gain.value = 260;
      lfo.connect(lfoGain).connect(noiseFilter.frequency);

      droneGain.connect(master);
      noiseGain.connect(master);

      osc1.start();
      osc2.start();
      noise.start();
      lfo.start();

      nodes = { master };
    }

    btn.addEventListener("click", () => {
      if (!ctx) build();
      on = !on;
      btn.classList.toggle("on", on);
      const target = on ? 0.55 : 0;
      nodes.master.gain.cancelScheduledValues(ctx.currentTime);
      nodes.master.gain.linearRampToValueAtTime(
        target,
        ctx.currentTime + 1.2
      );
      if (ctx.state === "suspended") ctx.resume();
    });
  })();

  /* ---------------- text size: reading comfort (A- / A+) ---------------- */

  (function setupTextScale() {
    const dec = document.getElementById("text-size-dec");
    const inc = document.getElementById("text-size-inc");
    if (!dec || !inc) return;

    const KEY = "iqj-text-scale";
    const MIN = 0.85;
    const MAX = 1.4;
    const STEP = 0.1;
    const root = document.documentElement;

    let scale = parseFloat(localStorage.getItem(KEY));
    if (!scale || isNaN(scale)) scale = 1;
    scale = Math.min(MAX, Math.max(MIN, scale));

    function apply() {
      root.style.setProperty("--text-scale", scale.toFixed(2));
      dec.disabled = scale <= MIN + 1e-9;
      inc.disabled = scale >= MAX - 1e-9;
      try { localStorage.setItem(KEY, scale.toFixed(2)); } catch (e) {}
      // layout heights shift with font size, so scroll-triggered reveals
      // need to recompute against the new geometry
      requestAnimationFrame(() => ScrollTrigger.refresh());
    }

    dec.addEventListener("click", () => {
      scale = Math.max(MIN, Math.round((scale - STEP) * 100) / 100);
      apply();
    });
    inc.addEventListener("click", () => {
      scale = Math.min(MAX, Math.round((scale + STEP) * 100) / 100);
      apply();
    });

    apply();
  })();

  /* ---------------- text-to-speech: "listen to the treatise" ---------------- */
  /* Walks the content in document order, queues one SpeechSynthesisUtterance
     per block (paragraph, axiom, glossary entry...), highlights whichever
     one is currently being read, and gently scrolls it into view if it has
     drifted off-screen. No audio files, no server: the browser's own
     speechSynthesis API, chunked per-block so long sections don't hit the
     well-known "utterances over ~15s silently stop" bug in Chrome. */

  (function setupTTS() {
    const btn = document.getElementById("tts-toggle");
    const wrap = document.getElementById("tts-wrap");
    const voiceBtn = document.getElementById("tts-voice-btn");
    const voicePanel = document.getElementById("tts-voice-panel");
    const PAGE_LANG = document.documentElement.lang || "ru";
    // Thai speech synthesis support is bad enough across browsers/OSes
    // (missing voices, mangled pronunciation) that offering the feature
    // does more harm than leaving it off entirely on this page.
    if (!btn || !("speechSynthesis" in window) || PAGE_LANG === "th") {
      if (wrap) wrap.style.display = "none";
      return;
    }

    const SELECTOR = [
      ".hero-title",
      ".hero-subtitle",
      ".preamble p",
      ".book-divider .book-title",
      "h3",
      ".passage p",
      ".passage-list li",
      "li.axiom",
      ".book-body p",
      "p.invocation",
      ".gloss-entry",
    ].join(", ");

    const BCP47 = { ru: "ru-RU", en: "en-US", th: "th-TH" }[PAGE_LANG] || "ru-RU";

    let items = null; // [{el, text}], built lazily on first play
    let voice = null;
    let voiceOptions = []; // every installed voice matching PAGE_LANG
    let voiceOptionsSig = ""; // cheap signature, avoids rebuilding the panel on every poll
    let idx = 0;
    let state = "idle"; // idle | reading | paused
    let currentUtterance = null; // kept referenced on purpose, see speakFrom()
    let watchdog = null;

    const VOICE_KEY = "iqj-tts-voice-" + PAGE_LANG;

    function pickVoice() {
      const voices = speechSynthesis.getVoices();
      voiceOptions = voices.filter((v) => v.lang && v.lang.toLowerCase().startsWith(PAGE_LANG));

      const sig = voiceOptions.map((v) => v.voiceURI).join("|");
      if (sig === voiceOptionsSig) {
        // Same voice list as last time - still make sure `voice` itself
        // points at one of today's actual Voice objects (some browsers
        // hand out fresh objects on every getVoices() call).
        if (voice) voice = voiceOptions.find((v) => v.voiceURI === voice.voiceURI) || voice;
      } else {
        voiceOptionsSig = sig;
        let saved = null;
        try { saved = localStorage.getItem(VOICE_KEY); } catch (e) {}
        voice = (saved && voiceOptions.find((v) => v.voiceURI === saved)) || voiceOptions[0] || null;
        renderVoicePanel();
      }
    }

    function renderVoicePanel() {
      if (!voiceBtn || !voicePanel) return;
      if (voiceOptions.length < 2) {
        voiceBtn.hidden = true;
        closeVoicePanel();
        return;
      }
      voiceBtn.hidden = false;
      voicePanel.innerHTML = "";
      voiceOptions.forEach((v) => {
        const row = document.createElement("button");
        row.type = "button";
        row.className = "tts-voice-option";
        row.setAttribute("role", "menuitemradio");
        row.textContent = v.name.replace(/\s*\([^)]*\)\s*$/, ""); // trim "(ru-RU)" suffixes some browsers add
        row.title = v.name;
        const isActive = !!voice && v.voiceURI === voice.voiceURI;
        row.setAttribute("aria-checked", isActive ? "true" : "false");
        row.classList.toggle("active", isActive);
        row.addEventListener("click", () => {
          voice = v;
          try { localStorage.setItem(VOICE_KEY, v.voiceURI); } catch (e) {}
          renderVoicePanel();
          closeVoicePanel();
          // Changing voice mid-sentence isn't possible with this API; the
          // next-best thing is restarting the current block so the choice
          // is actually audible right away instead of waiting.
          if (state === "reading") speakFrom(idx);
        });
        voicePanel.appendChild(row);
      });
    }

    function openVoicePanel() {
      if (!voiceBtn || !voicePanel || voiceBtn.hidden) return;
      voicePanel.hidden = false;
      requestAnimationFrame(() => {
        voicePanel.classList.add("open");
        voiceBtn.classList.add("open");
      });
      voiceBtn.setAttribute("aria-expanded", "true");
      document.addEventListener("click", onDocClickCloseVoicePanel, true);
      document.addEventListener("keydown", onEscCloseVoicePanel);
    }

    function closeVoicePanel() {
      if (!voiceBtn || !voicePanel) return;
      voicePanel.classList.remove("open");
      voiceBtn.classList.remove("open");
      voiceBtn.setAttribute("aria-expanded", "false");
      document.removeEventListener("click", onDocClickCloseVoicePanel, true);
      document.removeEventListener("keydown", onEscCloseVoicePanel);
      setTimeout(() => {
        if (!voicePanel.classList.contains("open")) voicePanel.hidden = true;
      }, 250);
    }

    function onDocClickCloseVoicePanel(e) {
      if (wrap && !wrap.contains(e.target)) closeVoicePanel();
    }
    function onEscCloseVoicePanel(e) {
      if (e.key === "Escape") closeVoicePanel();
    }

    if (voiceBtn) {
      voiceBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (voicePanel.classList.contains("open")) closeVoicePanel();
        else openVoicePanel();
      });
    }

    pickVoice();
    if ("onvoiceschanged" in speechSynthesis) {
      speechSynthesis.onvoiceschanged = pickVoice;
    }
    // Firefox doesn't always fire onvoiceschanged even though it loads the
    // voice list asynchronously, so poll a couple of times early on too.
    [300, 1000, 2500].forEach((ms) => setTimeout(pickVoice, ms));

    function extractText(el) {
      const clone = el.cloneNode(true);
      clone.querySelectorAll("br").forEach((br) => br.replaceWith(" "));
      let text = clone.textContent.replace(/\s+/g, " ").trim();
      if (el.classList.contains("axiom")) text = text.replace(/^△\s*/, "");
      if (el.classList.contains("gloss-entry")) {
        const dt = el.querySelector("dt");
        const dd = el.querySelector("dd");
        const term = dt ? dt.textContent.trim() : "";
        const def = dd ? dd.textContent.trim() : "";
        text = def ? `${term}. ${def}` : term;
      }
      return text;
    }

    function buildItems() {
      items = Array.from(document.querySelectorAll(SELECTOR))
        .map((el) => ({ el, text: extractText(el) }))
        .filter((it) => it.text.length > 0);
    }

    function clearHighlight() {
      document.querySelectorAll(".tts-active").forEach((el) => el.classList.remove("tts-active"));
    }

    function revealCurrent(el) {
      if (reduceMotion) return;
      const rect = el.getBoundingClientRect();
      if (rect.top > 80 && rect.bottom < window.innerHeight - 80) return;
      if (lenis) lenis.scrollTo(el, { offset: -window.innerHeight * 0.35, duration: 1.0 });
      else el.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function setBtnState(reading) {
      btn.classList.toggle("on", reading);
      btn.setAttribute("aria-pressed", reading ? "true" : "false");
    }

    function speakFrom(i) {
      if (!items || i >= items.length) {
        stop();
        return;
      }
      idx = i;
      const item = items[idx];

      pickVoice(); // re-check right before speaking, in case it just loaded
      const utter = new SpeechSynthesisUtterance(item.text);
      utter.lang = BCP47;
      if (voice) utter.voice = voice;
      utter.rate = 0.98;
      // Firefox is known to garbage-collect SpeechSynthesisUtterance objects
      // that nothing in JS still references, cutting speech off mid-queue.
      // Keeping this assignment alive for the duration is the standard fix.
      currentUtterance = utter;

      let started = false;
      utter.onstart = () => {
        // Highlighting/scrolling here, not before speak() is called, keeps
        // the page in sync with what's actually audible: speak() can have
        // a noticeable startup lag, and doing this eagerly made the page
        // visibly jump ahead of the voice still finishing the prior block.
        started = true;
        clearTimeout(watchdog);
        clearHighlight();
        item.el.classList.add("tts-active");
        revealCurrent(item.el);
      };
      utter.onend = () => {
        clearTimeout(watchdog);
        if (state === "reading") speakFrom(idx + 1);
      };
      utter.onerror = () => {
        clearTimeout(watchdog);
        if (state === "reading") speakFrom(idx + 1);
      };
      speechSynthesis.speak(utter);

      // Some browsers (seen on Firefox) silently drop an utterance without
      // ever firing start/end/error — missing voice, a stale voice
      // reference, or the GC issue above. Rather than hang forever on one
      // click, skip ahead if nothing happened after a few seconds.
      clearTimeout(watchdog);
      watchdog = setTimeout(() => {
        if (!started && state === "reading" && idx === i) speakFrom(i + 1);
      }, 4000);
    }

    function start() {
      if (!items) buildItems();
      if (!items.length) return;
      state = "reading";
      setBtnState(true);
      speakFrom(0);
    }

    function pause() {
      // The native speechSynthesis.pause()/resume() pair is unreliable
      // across browsers (resume() silently doing nothing is a long-known
      // issue). Pausing is done ourselves instead: cancel the current
      // utterance outright and simply remember which block we were on;
      // resume() just re-speaks that same block. Block-level granularity
      // (not mid-sentence) is the trade-off, in exchange for it actually
      // working reliably every time.
      state = "paused";
      setBtnState(false);
      clearTimeout(watchdog);
      speechSynthesis.cancel();
    }

    function resume() {
      if (!items) return;
      state = "reading";
      setBtnState(true);
      speakFrom(idx);
    }

    function stop() {
      state = "idle";
      setBtnState(false);
      clearTimeout(watchdog);
      speechSynthesis.cancel();
      currentUtterance = null;
      clearHighlight();
      idx = 0;
    }

    btn.addEventListener("click", () => {
      if (state === "idle") start();
      else if (state === "reading") pause();
      else resume();
    });

    // Deliberately no visibilitychange handler: switching tabs should not
    // stop the reading, and modern browsers keep speechSynthesis running
    // in a backgrounded tab just fine.
    window.addEventListener("beforeunload", () => speechSynthesis.cancel());
  })();

  /* ---------------- refresh on load & resize ---------------- */

  window.addEventListener("load", () => {
    ScrollTrigger.refresh();
    if (initialHash) {
      // let one frame pass so ScrollTrigger has real geometry to jump to
      requestAnimationFrame(() => scrollToTarget(initialHash));
    }
  });
})();
