// Overlay máy in avatar: nhận lệnh in qua WebSocket, xếp hàng, chạy animation.
(() => {
  const $ = (s) => document.querySelector(s);
  const stage = $("#stage"), strip = $("#strip"), gantry = $("#gantry"), head = $("#head");
  const printer = $("#printer");

  let cfg = { print_seconds: { print: 4, big: 6, legendary: 9 }, sound: true, max_queue: 60 };
  const queue = [];
  let busy = false;
  let ws;

  // ---------------------------------------------------------- scale 9:16 --
  let scale = 1;
  function fit() {
    scale = Math.min(innerWidth / 1080, innerHeight / 1920);
    stage.style.transform = `translate(-50%,-50%) scale(${scale})`;
  }
  addEventListener("resize", fit); fit();

  // ----------------------------------------------------------- websocket --
  function connect() {
    ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
    ws.onmessage = (e) => handle(JSON.parse(e.data));
    ws.onclose = () => setTimeout(connect, 2000);
  }
  const reportQueue = () => {
    if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "queue", size: queue.length + (busy ? 1 : 0) }));
    $("#queueN").textContent = queue.length;
  };

  function handle(m) {
    switch (m.type) {
      case "config": applyConfig(m); break;
      case "job":
        if (queue.length < (cfg.max_queue || 60)) queue.push(m);
        reportQueue(); pump(); break;
      case "feed":
        if (m.gift === "follow") toast(`<b>${esc(m.user)}</b> đã follow ❤️`);
        else toast(`<b>${esc(m.user)}</b> tặng ${esc(m.gift)}${m.count > 1 ? " x" + m.count : ""}`);
        break;
      case "board": renderBoard(m.top || []); break;
      case "clear": queue.length = 0; strip.innerHTML = ""; reportQueue(); break;
    }
  }

  function applyConfig(c) {
    cfg = { ...cfg, ...c };
    if (c.brand) {
      $("#brandTitle").textContent = c.brand.title || "";
      $("#logo").textContent = (c.brand.title || "S")[0];
      $("#brandSub").textContent = c.brand.subtitle || "";
    }
    $("#menu").innerHTML = (c.rules || []).map((r) =>
      `<li class="${r.action}"><span class="em">${r.emoji || "🎁"}</span>
       <div><div class="lbl">${esc(r.label)}</div><div class="hint">${esc(r.hint || r.min_coins + " xu")}</div></div></li>`).join("");
  }

  function renderBoard(top) {
    $("#boardList").innerHTML = top.map((r, i) =>
      `<li><span class="r">${i + 1}</span><img src="${attr(r.avatar)}" onerror="this.style.visibility='hidden'">
       <span class="n">${esc(r.user)}</span><span class="c">${r.coins}🪙</span></li>`).join("")
      || `<li style="opacity:.6;font-size:22px">Chưa có ai — tặng quà để lên bảng!</li>`;
  }

  // --------------------------------------------------------------- queue --
  async function pump() {
    if (busy) return;
    busy = true;
    while (queue.length) {
      const job = queue.shift();
      reportQueue();
      try { await printJob(job); } catch (e) { console.error(e); }
      await sleep(350);
    }
    busy = false;
    reportQueue();
    $("#now").classList.remove("busy");
    $("#nowText").textContent = "Tặng quà để được in!";
    park();
  }

  // --------------------------------------------------------------- print --
  async function printJob(job) {
    const label = { print: "In", big: "In to", legendary: "LEGENDARY" }[job.action] || "In";
    $("#now").classList.add("busy");
    $("#nowText").textContent = `${label}: ${job.user}`;

    if (job.action === "legendary") legendary(job.user);

    const sheet = makeSheet(job);
    const img = sheet.querySelector(".avatar");
    await Promise.race([img.decode().catch(() => {}), sleep(2500)]);

    // kéo giấy (feed) lên đúng bằng chiều cao tấm mới
    strip.appendChild(sheet);
    const h = sheet.offsetHeight + 26;
    strip.style.transition = "none";
    strip.style.transform = `translateY(${h}px)`;
    strip.offsetHeight; // reflow
    strip.style.transition = "transform .9s cubic-bezier(.3,.7,.3,1)";
    strip.style.transform = "translateY(0)";
    sfx.feed();
    await sleep(950);
    while (strip.children.length > 6) strip.firstElementChild.remove();

    // toạ độ tấm giấy trong hệ 1080x1920
    const pr = printer.getBoundingClientRect(), sr = sheet.getBoundingClientRect();
    const sx = (sr.left - pr.left) / scale, sy = (sr.top - pr.top) / scale;
    const sw = sr.width / scale, sh = sr.height / scale;

    const ink = sheet.querySelector(".ink"), wet = sheet.querySelector(".wet");
    const D = (cfg.print_seconds?.[job.action] || 4) * 1000;
    const passes = job.action === "print" ? 7 : 10;
    sheet.classList.add("printing"); head.classList.add("busy");
    sfx.start();

    await new Promise((done) => {
      const t0 = performance.now();
      const frame = (now) => {
        const p = Math.min(1, (now - t0) / D);
        const line = p * sh;
        ink.style.clipPath = `inset(0 0 ${(100 - p * 100).toFixed(2)}% 0)`;
        wet.style.top = `${line - 5}px`;
        // đầu in quét ngang qua lại
        const sweep = 0.5 - 0.5 * Math.cos(p * passes * 2 * Math.PI);
        moveGantry(sy + line, sx + sweep * sw);
        sfx.mod(sweep);
        if (p < 1) requestAnimationFrame(frame); else done();
      };
      requestAnimationFrame(frame);
    });

    sfx.stop(); sfx.ding(job.action);
    sheet.classList.remove("printing"); head.classList.remove("busy");
    if (job.action !== "print") confetti(job.action === "legendary" ? 220 : 90);
    await sleep(job.action === "print" ? 500 : 1300);
  }

  function moveGantry(y, x) {
    gantry.style.transition = "none";
    head.style.transition = "none";
    // nozzle (đáy đầu in ≈ 82px) đặt tại dòng y; gantry gốc top=300
    gantry.style.transform = `translateY(${y - 82 - 300}px)`;
    head.style.transform = `translateX(${x - 96 - 55}px)`;
  }
  function park() {
    gantry.style.transition = "transform 1.2s ease";
    head.style.transition = "transform 1.2s ease";
    gantry.style.transform = "translateY(0)";
    head.style.transform = `translateX(${(1080 - 192) / 2 - 55}px)`;
  }
  park();

  function makeSheet(job) {
    const el = document.createElement("div");
    el.className = `sheet ${job.action}`;
    const fallback = "/demo-avatar/" + encodeURIComponent((job.user || "x").replace(/[^\p{L}\p{N}]/gu, "").slice(0, 12) || "x");
    el.innerHTML = `
      <div class="ink">
        ${job.action === "legendary" ? '<div class="badge">★ VIPP ★</div>' : ""}
        <img class="avatar" src="${attr(job.avatar || fallback)}" onerror="this.onerror=null;this.src='${fallback}'">
        <div class="name">${esc(job.user)}</div>
        <div class="tag">${job.gift_image ? `<img src="${attr(job.gift_image)}">` : "🎁"} ${esc(job.gift || "")}</div>
      </div>
      <div class="wet"></div>`;
    return el;
  }

  // -------------------------------------------------------------- effects --
  function toast(html) {
    const t = document.createElement("div");
    t.className = "toast"; t.innerHTML = html;
    const box = $("#toasts");
    box.appendChild(t);
    while (box.children.length > 3) box.firstElementChild.remove();
    setTimeout(() => t.remove(), 4200);
  }

  function legendary(name) {
    const l = $("#legend");
    $("#legendName").textContent = name;
    l.hidden = false;
    const inner = l.firstElementChild;
    inner.style.animation = "none"; inner.offsetHeight; inner.style.animation = "";
    setTimeout(() => (l.hidden = true), 3300);
    sfx.fanfare();
    confetti(300);
  }

  const cv = $("#fx"), cx = cv.getContext("2d");
  cv.width = 1080; cv.height = 1920;
  let parts = [], running = false;
  function confetti(n) {
    const colors = ["#f7c948", "#ff3b5c", "#00d2ff", "#7cff6b", "#ffffff", "#ff8a00"];
    for (let i = 0; i < n; i++) parts.push({
      x: 540 + (Math.random() - .5) * 300, y: 520, vx: (Math.random() - .5) * 26, vy: -Math.random() * 26 - 6,
      r: Math.random() * Math.PI, vr: (Math.random() - .5) * .4, s: 8 + Math.random() * 10,
      c: colors[(Math.random() * colors.length) | 0], life: 0,
    });
    if (!running) { running = true; requestAnimationFrame(tick); }
  }
  function tick() {
    cx.clearRect(0, 0, 1080, 1920);
    parts = parts.filter((p) => p.y < 2000 && p.life < 260);
    for (const p of parts) {
      p.vy += .55; p.vx *= .99; p.x += p.vx; p.y += p.vy; p.r += p.vr; p.life++;
      cx.save(); cx.translate(p.x, p.y); cx.rotate(p.r); cx.fillStyle = p.c;
      cx.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2); cx.restore();
    }
    if (parts.length) requestAnimationFrame(tick); else { running = false; cx.clearRect(0, 0, 1080, 1920); }
  }

  // ---------------------------------------------------------------- sound --
  // Âm thanh tổng hợp bằng WebAudio (không cần file). OBS: bật "Control audio via OBS".
  const sfx = (() => {
    let ac, motor, lfo, gain, filt;
    const ctx = () => {
      if (!cfg.sound) return null;
      try { ac = ac || new AudioContext(); if (ac.state === "suspended") ac.resume(); } catch { return null; }
      return ac;
    };
    const beep = (f, t0, dur, type = "sine", vol = .15) => {
      const a = ctx(); if (!a) return;
      const o = a.createOscillator(), g = a.createGain();
      o.type = type; o.frequency.value = f;
      g.gain.setValueAtTime(vol, a.currentTime + t0);
      g.gain.exponentialRampToValueAtTime(.0001, a.currentTime + t0 + dur);
      o.connect(g).connect(a.destination); o.start(a.currentTime + t0); o.stop(a.currentTime + t0 + dur + .05);
    };
    return {
      start() {
        const a = ctx(); if (!a || motor) return;
        motor = a.createOscillator(); motor.type = "sawtooth"; motor.frequency.value = 140;
        filt = a.createBiquadFilter(); filt.type = "lowpass"; filt.frequency.value = 900;
        gain = a.createGain(); gain.gain.value = .05;
        lfo = a.createOscillator(); lfo.type = "square"; lfo.frequency.value = 22;
        const lg = a.createGain(); lg.gain.value = .03; lfo.connect(lg).connect(gain.gain);
        motor.connect(filt).connect(gain).connect(a.destination); motor.start(); lfo.start();
      },
      mod(v) { if (motor) motor.frequency.value = 120 + v * 80; },
      stop() { try { motor.stop(); lfo.stop(); } catch {} motor = lfo = null; },
      feed() { beep(220, 0, .5, "triangle", .06); },
      ding(kind) { beep(880, 0, .25); beep(1320, .12, .35); if (kind !== "print") beep(1760, .26, .5); },
      fanfare() { [523, 659, 784, 1047].forEach((f, i) => beep(f, i * .14, .5, "square", .07)); },
    };
  })();

  // ----------------------------------------------------------------- misc --
  const bg = $("#bgvideo");
  bg.addEventListener("loadeddata", () => bg.classList.add("ok"));
  bg.addEventListener("error", () => bg.remove());

  function esc(s) { return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  const attr = esc;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  renderBoard([]);
  connect();
})();
