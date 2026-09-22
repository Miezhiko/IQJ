/*
 * Ink / flow-field background.
 *
 * A curl-noise particle field standing in for Русло — the riverbed the whole
 * manifesto is written around. `window.inkMood` is set by main.js (driven by
 * ScrollTrigger, one entry per <section data-mood="...">) and read here every
 * frame; parameters lerp toward the active mood so transitions stay organic.
 *
 * Moods:
 *   source  — hero / Book I: wide, slow, luminous swirl (the Исток)
 *   flow    — default reading mood: steady curl-noise current
 *   murk    — Book IV (Помутнение): dense, fast, dark churn
 *   network — Book VI (Империя): particles occasionally link like a mycelium
 *   crystal — Axioms: near-still, sparse, sharp points of light
 *   calm    — Заключение: slow, wide, fading out
 */
(function () {
  "use strict";

  const MOODS = {
    source:  { speed: 0.55, scale: 0.0011, chaos: 0.55, count: 420, alpha: 26, size: 1.7, hue: 42, sat: 55, bri: 82, glow: 1.25, link: 0 },
    flow:    { speed: 0.85, scale: 0.0016, chaos: 0.9,  count: 460, alpha: 30, size: 1.35, hue: 34, sat: 60, bri: 70, glow: 0.9,  link: 0 },
    murk:    { speed: 1.35, scale: 0.0026, chaos: 1.6,  count: 620, alpha: 40, size: 1.1, hue: 18, sat: 45, bri: 42, glow: 0.55, link: 0 },
    network: { speed: 0.45, scale: 0.0013, chaos: 0.5,  count: 260, alpha: 20, size: 2.0, hue: 40, sat: 50, bri: 88, glow: 1.4,  link: 1 },
    crystal: { speed: 0.12, scale: 0.0009, chaos: 0.15, count: 160, alpha: 14, size: 2.4, hue: 45, sat: 40, bri: 95, glow: 1.7,  link: 0 },
    calm:    { speed: 0.28, scale: 0.001,  chaos: 0.35, count: 220, alpha: 16, size: 1.6, hue: 40, sat: 45, bri: 80, glow: 1.1,  link: 0 },
  };

  const cur = { ...MOODS.source };
  let target = MOODS.source;

  window.setInkMood = function (mood) {
    target = MOODS[mood] || MOODS.flow;
  };

  const sketch = (p) => {
    let particles = [];
    let t = 0;
    let canvasEl;
    let dpr = 1;

    function makeParticle() {
      return {
        x: p.random(p.width),
        y: p.random(p.height),
        px: 0,
        py: 0,
        life: p.random(200, 900),
      };
    }

    function resize() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      p.resizeCanvas(w, h);
      p.clear();
      p.background(14, 9, 6);
    }

    p.setup = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvasEl = p.createCanvas(window.innerWidth, window.innerHeight);
      canvasEl.id("ink-canvas-inner");
      canvasEl.parent(document.body);
      const realCanvas = document.getElementById("ink-canvas");
      if (realCanvas && realCanvas.tagName === "CANVAS") {
        // move our drawing surface into the placeholder left by the template
        realCanvas.replaceWith(canvasEl.elt);
        canvasEl.elt.id = "ink-canvas";
      }
      p.pixelDensity(dpr);
      p.colorMode(p.HSB, 360, 100, 100, 100);
      p.background(14, 9, 6);
      p.noStroke();
      for (let i = 0; i < cur.count; i++) particles.push(makeParticle());
      p.frameRate(60);
    };

    p.windowResized = resize;

    function lerpMood() {
      const k = 0.02;
      for (const key in cur) {
        cur[key] += (target[key] - cur[key]) * k;
      }
      const desired = Math.round(cur.count);
      while (particles.length < desired) particles.push(makeParticle());
      if (particles.length > desired) particles.length = desired;
    }

    p.draw = () => {
      lerpMood();
      t += 0.0016 * cur.speed;

      // fade-to-void wash instead of clear() -> trailing ink streaks
      p.noStroke();
      p.fill(14, 60, 3, 10 + cur.alpha * 0.18);
      p.rect(0, 0, p.width, p.height);

      const scale = cur.scale;
      const chaos = cur.chaos;

      for (let i = 0; i < particles.length; i++) {
        const pt = particles[i];
        pt.px = pt.x;
        pt.py = pt.y;

        const angle =
          p.noise(pt.x * scale, pt.y * scale, t) * Math.PI * 2 * 2.2 * chaos;
        const speed = cur.speed * 1.6;
        pt.x += Math.cos(angle) * speed;
        pt.y += Math.sin(angle) * speed;
        pt.life -= 1;

        if (
          pt.life <= 0 ||
          pt.x < -20 ||
          pt.x > p.width + 20 ||
          pt.y < -20 ||
          pt.y > p.height + 20
        ) {
          particles[i] = makeParticle();
          continue;
        }

        const alphaJ = cur.alpha * (0.5 + 0.5 * Math.sin(i * 12.9898 + t * 3));
        p.stroke(cur.hue, cur.sat, cur.bri, alphaJ);
        p.strokeWeight(cur.size);
        p.line(pt.px, pt.py, pt.x, pt.y);
      }

      if (cur.link > 0.3) {
        p.stroke(cur.hue, cur.sat * 0.6, cur.bri, 10);
        p.strokeWeight(0.6);
        const step = 3;
        for (let i = 0; i < particles.length; i += step) {
          for (let j = i + step; j < particles.length; j += step * 4) {
            const a = particles[i];
            const b = particles[j];
            const dx = a.x - b.x;
            const dy = a.y - b.y;
            const d2 = dx * dx + dy * dy;
            if (d2 < 140 * 140) {
              p.line(a.x, a.y, b.x, b.y);
            }
          }
        }
      }

      // soft vignette so page edges stay dark regardless of mood
      p.noFill();
    };
  };

  window.addEventListener("DOMContentLoaded", () => {
    new p5(sketch);
  });
})();
