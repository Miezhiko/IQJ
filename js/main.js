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
    if (!roman || !title) return;

    gsap.set(roman, { opacity: 0, y: 24 });
    gsap.set(title, { opacity: 0, scale: 0.92, y: 16 });

    if (reduceMotion) {
      gsap.set([roman, title], { opacity: 1, y: 0, scale: 1 });
      return;
    }

    const tl = gsap.timeline({
      scrollTrigger: {
        trigger: div,
        start: "top 65%",
        toggleActions: "play none none reverse",
      },
    });
    tl.to(roman, { opacity: 1, y: 0, duration: 1.0, ease: "power2.out" }).to(
      title,
      { opacity: 1, scale: 1, y: 0, duration: 1.1, ease: "power3.out" },
      "-=0.55"
    );
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

  /* ---------------- refresh on load & resize ---------------- */

  window.addEventListener("load", () => {
    ScrollTrigger.refresh();
    if (initialHash) {
      // let one frame pass so ScrollTrigger has real geometry to jump to
      requestAnimationFrame(() => scrollToTarget(initialHash));
    }
  });
})();
