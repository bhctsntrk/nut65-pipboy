// NUT-65 Pip-Boy Frontend
// Browser-first: works standalone for design iteration.
// pywebview bridge added in Phase 4.

// ── i18n ─────────────────────────────────────────────────────────────

const LANG = {
  en: {
    title: "NUT-65 TERMINAL v1.0",
    offline: "OFFLINE",
    connected: "CONNECTED",
    demo_mode: "DEMO MODE",
    no_device: "NO DEVICE",
    disconnected: "DISCONNECTED",
    tab_snake: "SNAKE",
    tab_pong: "PONG",
    tab_marquee: "MARQUEE",
    lbl_mode: "MODE",
    lbl_score: "SCORE",
    lbl_fps: "FPS",
    lbl_textinput: "TEXT INPUT",
    ph_marquee: "TYPE YOUR MESSAGE...",
    lbl_hardware: "HARDWARE STATUS",
    lbl_speed: "SPEED",
    lbl_color: "COLOR",
    mode_snake: "SNAKE",
    mode_pong: "PONG",
    mode_marquee: "MARQUEE",
  },
  tr: {
    title: "NUT-65 TERMINAL v1.0",
    offline: "BAGLI DEGIL",
    connected: "BAGLI",
    demo_mode: "DEMO MODU",
    no_device: "CIHAZ YOK",
    disconnected: "BAGLANTI KESILDI",
    tab_snake: "YILAN",
    tab_pong: "PONG",
    tab_marquee: "KAYAN YAZI",
    lbl_mode: "MOD",
    lbl_score: "SKOR",
    lbl_fps: "FPS",
    lbl_textinput: "METIN GIRISI",
    ph_marquee: "MESAJINIZI YAZIN...",
    lbl_hardware: "DONANIM DURUMU",
    lbl_speed: "HIZ",
    lbl_color: "RENK",
    mode_snake: "YILAN",
    mode_pong: "PONG",
    mode_marquee: "KAYAN YAZI",
  }
};

let currentLang = "en";

function setLang(lang) {
  currentLang = lang;
  const dict = LANG[lang] || LANG.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    if (dict[key]) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    const key = el.dataset.i18nPlaceholder;
    if (dict[key]) el.placeholder = dict[key];
  });
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.lang === lang);
  });
  // Update active mode name
  document.getElementById("statMode").textContent = dict["mode_" + currentMode] || currentMode.toUpperCase();
}

// ── Keyboard Layout Data ─────────────────────────────────────────────
// Ported from Weikav_NUT65.js — physical key positions and sizes

const KEY_UNIT = 42; // pixels per 1u key
const KEY_GAP = 2;
const KEY_RADIUS = 4;
const ROWS = 6;
const COLS = 15;

// Key layout: [label, row, col, widthU, heightU]
// widthU is in keyboard units (1u = standard key)
const KEY_LAYOUT = [
  // Row 0
  ["ESC",0,0,1,1],["1",0,1,1,1],["2",0,2,1,1],["3",0,3,1,1],["4",0,4,1,1],
  ["5",0,5,1,1],["6",0,6,1,1],["7",0,7,1,1],["8",0,8,1,1],["9",0,9,1,1],
  ["0",0,10,1,1],["-",0,11,1,1],["=",0,12,1,1],["BS",0,13,1,1],["DEL",0,14,1,1],
  // Row 1
  ["TAB",1,0,1,1],["Q",1,1,1,1],["W",1,2,1,1],["E",1,3,1,1],["R",1,4,1,1],
  ["T",1,5,1,1],["Y",1,6,1,1],["U",1,7,1,1],["I",1,8,1,1],["O",1,9,1,1],
  ["P",1,10,1,1],["[",1,11,1,1],["]",1,12,1,1],["\\",1,13,1,1],["PU",1,14,1,1],
  // Row 2 (col 12 missing)
  ["CAP",2,0,1,1],["A",2,1,1,1],["S",2,2,1,1],["D",2,3,1,1],["F",2,4,1,1],
  ["G",2,5,1,1],["H",2,6,1,1],["J",2,7,1,1],["K",2,8,1,1],["L",2,9,1,1],
  [";",2,10,1,1],["'",2,11,1,1],["ENT",2,13,1,1],["PD",2,14,1,1],
  // Row 3 (col 1 missing)
  ["SHF",3,0,1,1],["Z",3,2,1,1],["X",3,3,1,1],["C",3,4,1,1],["V",3,5,1,1],
  ["B",3,6,1,1],["N",3,7,1,1],["M",3,8,1,1],[",",3,9,1,1],[".",3,10,1,1],
  ["/",3,11,1,1],["RSH",3,12,1,1],["\u2191",3,13,1,1],["END",3,14,1,1],
  // Row 4 (spacebar region)
  ["CTL",4,0,1,1],["WIN",4,1,1,1],["ALT",4,2,1,1],["SPC",4,5,1,1],
  ["RAL",4,10,1,1],["FN",4,11,1,1],["\u2190",4,12,1,1],["\u2193",4,13,1,1],["\u2192",4,14,1,1],
];

// Light bar: row 5, cols 0-14 as one long strip
const LIGHTBAR_Y = 5.3;
const LIGHTBAR_HEIGHT = 0.5;

// ── State ────────────────────────────────────────────────────────────

let currentMode = "snake";
let keyElements = {};      // "row,col" -> SVG rect element
let barElements = {};      // "col" -> SVG rect element
let frameCount = 0;
let lastFpsTime = performance.now();
let displayFps = 0;

// Bridge/demo lifecycle flags (module scope for runDemoAnimation access)
let pollingStarted = false;
let demoRunning = false;
let demoStopFlag = false;

// ── Keyboard SVG Builder ─────────────────────────────────────────────

function buildKeyboard() {
  const svg = document.getElementById("keyboardSvg");
  svg.innerHTML = "";

  // Keys
  for (const [label, row, col, wu] of KEY_LAYOUT) {
    const x = col * KEY_UNIT + KEY_GAP;
    const y = row * KEY_UNIT + KEY_GAP;
    const w = wu * KEY_UNIT - KEY_GAP * 2;
    const h = KEY_UNIT - KEY_GAP * 2;

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", x);
    rect.setAttribute("y", y);
    rect.setAttribute("width", w);
    rect.setAttribute("height", h);
    rect.setAttribute("rx", KEY_RADIUS);
    rect.setAttribute("fill", "#111");
    rect.setAttribute("stroke", "#333");
    rect.setAttribute("stroke-width", "1");
    svg.appendChild(rect);

    // Label
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", x + w / 2);
    text.setAttribute("y", y + h / 2 + 4);
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("font-family", "VT323, monospace");
    text.setAttribute("font-size", "11");
    text.setAttribute("fill", "#444");
    text.textContent = label;
    svg.appendChild(text);

    keyElements[`${row},${col}`] = rect;
  }

  // Light bar segments
  for (let c = 0; c < COLS; c++) {
    const x = c * KEY_UNIT + KEY_GAP;
    const y = LIGHTBAR_Y * KEY_UNIT;
    const w = KEY_UNIT - KEY_GAP * 2;
    const h = LIGHTBAR_HEIGHT * KEY_UNIT;

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", x);
    rect.setAttribute("y", y);
    rect.setAttribute("width", w);
    rect.setAttribute("height", h);
    rect.setAttribute("rx", 2);
    rect.setAttribute("fill", "#111");
    rect.setAttribute("stroke", "#333");
    rect.setAttribute("stroke-width", "1");
    svg.appendChild(rect);

    barElements[`${c}`] = rect;
  }
}

// ── Color Conversion ─────────────────────────────────────────────────

function hsvToCSS(hue, sat) {
  // hue: 0-255, sat: 0-255 → CSS hsl()
  if (sat < 10) return "#222";  // off/desaturated = dark
  const h = (hue / 255) * 360;
  const s = (sat / 255) * 100;
  return `hsl(${h}, ${s}%, 50%)`;
}

function hsvToGlow(hue, sat) {
  const h = (hue / 255) * 360;
  const s = (sat / 255) * 100;
  return `0 0 6px hsla(${h}, ${s}%, 50%, 0.6)`;
}

// ── Update Keyboard Colors ───────────────────────────────────────────

function updateKeyboard(colors) {
  // colors: array of {row, col, hue, sat} objects
  for (const {row, col, hue, sat} of colors) {
    const el = row === 5 ? barElements[`${col}`] : keyElements[`${row},${col}`];
    if (el) {
      const color = hsvToCSS(hue, sat);
      el.setAttribute("fill", color);
      el.setAttribute("stroke", sat > 10 ? color : "#333");
      const filter = sat > 10 ? `drop-shadow(${hsvToGlow(hue, sat)})` : "";
      if (el.style.filter !== filter) el.style.filter = filter;
    }
  }
}

// ── Tab Switching ────────────────────────────────────────────────────

function setActiveTab(mode) {
  currentMode = mode;
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.mode === mode));
  const dict = LANG[currentLang] || LANG.en;
  document.getElementById("statMode").textContent = dict["mode_" + mode] || mode.toUpperCase();

  // Show/hide marquee controls
  const mc = document.getElementById("marqueeControls");
  const sp = document.getElementById("statsPanel");
  mc.style.display = mode === "marquee" ? "flex" : "none";
  sp.style.display = mode === "marquee" ? "none" : "flex";

  // Call bridge if available
  if (window.pywebview && pywebview.api) {
    pywebview.api.set_mode(mode);
  }
}

// ── Demo Mode (no pywebview) — real game simulation in JS ────────────

// Active color hue (changed by color palette)
let activeHue = 85; // green by default

// Valid key positions for snake — rows 0-3 only (row 4 has too many gaps from spacebar)
const VALID_KEYS = new Set();
for (const [, r, c] of KEY_LAYOUT) { if (r < 4) VALID_KEYS.add(`${r},${c}`); }

// ── Demo Snake ──
const demoSnake = {
  body: [], food: null, dir: [0,1], nextDir: [0,1],
  init() {
    this.body = [[2,7],[2,6],[2,5]];
    this.dir = [0,1]; this.nextDir = [0,1];
    this.spawnFood();
  },
  spawnFood() {
    const occupied = new Set(this.body.map(p => `${p[0]},${p[1]}`));
    const free = [];
    for (const [,r,c] of KEY_LAYOUT) { if (r < 5 && !occupied.has(`${r},${c}`)) free.push([r,c]); }
    this.food = free.length ? free[Math.floor(Math.random()*free.length)] : null;
  },
  tick() {
    // Simple AI: turn toward food
    if (this.food) {
      const [hr,hc] = this.body[0];
      const [fr,fc] = this.food;
      const dr = fr - hr, dc = fc - hc;
      // Try to move toward food, avoid going backward
      const candidates = [[0,1],[0,-1],[1,0],[-1,0]].filter(
        d => !(d[0]===-this.dir[0] && d[1]===-this.dir[1])
      );
      // Prefer direction toward food
      candidates.sort((a,b) => {
        const da = Math.abs(hr+a[0]-fr)+Math.abs(hc+a[1]-fc);
        const db = Math.abs(hr+b[0]-fr)+Math.abs(hc+b[1]-fc);
        return da - db;
      });
      // Pick first valid move (no wall, no self)
      const occupied = new Set(this.body.slice(0,-1).map(p=>`${p[0]},${p[1]}`));
      for (const d of candidates) {
        const nr = hr+d[0], nc = hc+d[1];
        if (VALID_KEYS.has(`${nr},${nc}`) && !occupied.has(`${nr},${nc}`)) {
          this.nextDir = d; break;
        }
      }
    }
    this.dir = this.nextDir;
    const [hr,hc] = this.body[0];
    const newHead = [hr+this.dir[0], hc+this.dir[1]];
    // Wall or self collision → reset
    const occupied = new Set(this.body.map(p=>`${p[0]},${p[1]}`));
    if (!VALID_KEYS.has(`${newHead[0]},${newHead[1]}`) || occupied.has(`${newHead[0]},${newHead[1]}`)) {
      this.init(); return;
    }
    this.body.unshift(newHead);
    if (this.food && newHead[0]===this.food[0] && newHead[1]===this.food[1]) {
      this.spawnFood(); // grow
    } else {
      this.body.pop();
    }
    if (this.body.length > 30) this.init(); // reset when too long
  }
};

// ── Demo Pong ──
const demoPong = {
  ballR: 2, ballC: 7, velR: 0.5, velC: 1.2,
  leftY: 1, rightY: 1, leftScore: 0, rightScore: 0, pauseTimer: 0,
  init() {
    this.leftScore=0; this.rightScore=0;
    this.leftY=1; this.rightY=1;
    this.serve();
  },
  serve() {
    this.ballR = 2; this.ballC = 7;
    this.velR = (Math.random()-0.5) * 1.5;
    this.velC = (Math.random()>0.5 ? 1 : -1) * 1.6;
    this.pauseTimer = 8; // brief pause before serve
  },
  tick() {
    if (this.pauseTimer > 0) { this.pauseTimer--; return; }

    // Move paddles (AI with randomness)
    const br = Math.round(this.ballR);
    // Left paddle — decent tracking
    const ltarget = br - 1 + Math.floor(Math.random()*1.5);
    if (this.leftY < ltarget) this.leftY = Math.min(this.leftY+1, 3);
    else if (this.leftY > ltarget) this.leftY = Math.max(this.leftY-1, 0);
    // Right paddle — slightly worse, sometimes lazy
    if (Math.random() > 0.25) {
      const rtarget = br - 1 + Math.floor(Math.random()*1.5);
      if (this.rightY < rtarget) this.rightY = Math.min(this.rightY+1, 3);
      else if (this.rightY > rtarget) this.rightY = Math.max(this.rightY-1, 0);
    }

    // Move ball
    this.ballR += this.velR;
    this.ballC += this.velC;

    // Top/bottom bounce
    if (this.ballR < 0) { this.ballR = Math.abs(this.ballR); this.velR = Math.abs(this.velR); }
    if (this.ballR > 4) { this.ballR = 8 - this.ballR; this.velR = -Math.abs(this.velR); }

    const bCol = Math.round(this.ballC);
    const bRow = Math.round(this.ballR);

    // Left paddle hit (col 0-1)
    if (bCol <= 1 && this.velC < 0) {
      if (bRow >= this.leftY && bRow < this.leftY + 2) {
        this.velC = Math.abs(this.velC) + 0.05;
        this.velR = (bRow - this.leftY - 1) * 0.7 + (Math.random()-0.5)*0.3;
        this.ballC = 2;
      } else if (this.ballC < 0) {
        this.rightScore++;
        if (this.rightScore >= 7) { this.init(); return; }
        this.serve(); return;
      }
    }
    // Right paddle hit (col 13-14)
    if (bCol >= 13 && this.velC > 0) {
      if (bRow >= this.rightY && bRow < this.rightY + 2) {
        this.velC = -(Math.abs(this.velC) + 0.05);
        this.velR = (bRow - this.rightY - 1) * 0.7 + (Math.random()-0.5)*0.3;
        this.ballC = 12;
      } else if (this.ballC > 14) {
        this.leftScore++;
        if (this.leftScore >= 7) { this.init(); return; }
        this.serve(); return;
      }
    }

    // Clamp ball speed
    if (Math.abs(this.velC) > 2) this.velC = Math.sign(this.velC) * 2;
    if (Math.abs(this.velR) > 1.5) this.velR = Math.sign(this.velR) * 1.5;
  }
};

// ── Demo Marquee (5-row font) ──
const DEMO_FONT = {
  ' ':[0,0,0,0,0],
  'A':[14,17,31,17,17],'B':[15,17,15,17,15],'C':[14,17,1,17,14],
  'D':[15,17,17,17,15],'E':[31,1,15,1,31],'F':[31,1,15,1,1],
  'G':[14,1,25,17,14],'H':[17,17,31,17,17],'I':[14,4,4,4,14],
  'J':[16,16,16,17,14],'K':[17,9,7,9,17],'L':[1,1,1,1,31],
  'M':[17,27,21,17,17],'N':[17,19,21,25,17],'O':[14,17,17,17,14],
  'P':[15,17,15,1,1],'Q':[14,17,17,25,30],'R':[15,17,15,9,17],
  'S':[30,1,14,16,15],'T':[31,4,4,4,4],'U':[17,17,17,17,14],
  'V':[17,17,17,10,4],'W':[17,17,21,27,17],'X':[17,10,4,10,17],
  'Y':[17,10,4,4,4],'Z':[31,8,4,2,31],
  '0':[14,17,17,17,14],'1':[4,6,4,4,14],'2':[14,16,14,1,31],
  '3':[14,16,12,16,14],'4':[17,17,31,16,16],'5':[31,1,15,16,15],
  '6':[14,1,15,17,14],'7':[31,16,8,4,4],'8':[14,17,14,17,14],
  '9':[14,17,30,16,14],
  '!':[4,4,4,0,4],'?':[14,16,12,0,4],'.':[0,0,0,0,4],'-':[0,0,14,0,0],
};
const demoMarquee = {
  offset: 0, columns: [],
  init() {
    this.columns = [];
    const text = "  NUT65 PIPBOY  HELLO  ";
    for (let i = 0; i < text.length; i++) {
      const g = DEMO_FONT[text[i]] || DEMO_FONT[' '];
      for (let cx = 0; cx < 5; cx++) {
        const col = []; for (let ry = 0; ry < 5; ry++) col.push(!!(g[ry] & (1<<cx)));
        this.columns.push(col);
      }
      this.columns.push([false,false,false,false,false]); // gap
    }
    this.offset = 0;
  },
  tick() { this.offset = (this.offset + 1) % this.columns.length; }
};

// Speed slider → demo interval mapping (1=very slow 500ms, 10=fast 40ms)
let demoInterval = 120;
const SPEED_TO_MS = { 1:500, 2:350, 3:250, 4:180, 5:120, 6:90, 7:70, 8:55, 9:45, 10:40 };

function runDemoAnimation() {
  demoSnake.init(); demoPong.init(); demoMarquee.init();

  let lastDemoTime = 0;
  const demoColors = [];

  function demoFrame(timestamp) {
    if (demoStopFlag) return;  // kill demo loop when real bridge connects
    if (timestamp - lastDemoTime < demoInterval) { requestAnimationFrame(demoFrame); return; }
    lastDemoTime = timestamp;
    demoColors.length = 0;

    if (currentMode === "snake") {
      demoSnake.tick();
      const bodySet = new Set(demoSnake.body.map(p=>`${p[0]},${p[1]}`));
      for (const [,row,col] of KEY_LAYOUT) {
        const k = `${row},${col}`;
        if (demoSnake.body[0] && row===demoSnake.body[0][0] && col===demoSnake.body[0][1]) {
          demoColors.push({row,col,hue:activeHue+20,sat:255}); // head
        } else if (bodySet.has(k)) {
          demoColors.push({row,col,hue:activeHue,sat:255}); // body
        } else if (demoSnake.food && row===demoSnake.food[0] && col===demoSnake.food[1]) {
          demoColors.push({row,col,hue:0,sat:255}); // food
        } else {
          demoColors.push({row,col,hue:0,sat:0});
        }
      }
      // Update score display
      document.getElementById("statScore").textContent = demoSnake.body.length;
      // Light bar: snake length progress
      const fill = Math.min(15, demoSnake.body.length);
      for (let c=0; c<COLS; c++) demoColors.push({row:5,col:c,hue:activeHue,sat:c<fill?200:0});

    } else if (currentMode === "pong") {
      demoPong.tick();
      const br = Math.max(0,Math.min(4,Math.round(demoPong.ballR)));
      const bc = Math.max(1,Math.min(13,Math.round(demoPong.ballC)));
      for (const [,row,col] of KEY_LAYOUT) {
        let hue=0, sat=0;
        // Left paddle (col 0)
        if (col===0 && row>=demoPong.leftY && row<demoPong.leftY+2) { hue=activeHue; sat=255; }
        // Right paddle (col 14)
        else if (col===14 && row>=demoPong.rightY && row<demoPong.rightY+2) { hue=activeHue; sat=255; }
        // Ball — contrasting color (opposite hue)
        else if (row===br && col===bc) { hue=(activeHue+128)%256; sat=255; }
        // Center net
        else if (col===7) { hue=activeHue; sat=40; }
        demoColors.push({row,col,hue,sat});
      }
      // Update score display
      document.getElementById("statScore").textContent = `${demoPong.leftScore} - ${demoPong.rightScore}`;
      // Light bar: scores
      for (let c=0; c<COLS; c++) {
        if (c<7) demoColors.push({row:5,col:c,hue:activeHue,sat:c<demoPong.leftScore?200:0});
        else if (c===7) demoColors.push({row:5,col:c,hue:0,sat:0});
        else demoColors.push({row:5,col:c,hue:(activeHue+128)%256,sat:(14-c)<demoPong.rightScore?200:0});
      }

    } else if (currentMode === "marquee") {
      // Marquee — all 5 rows (0-4)
      demoMarquee.tick();
      for (const [,row,col] of KEY_LAYOUT) {
        if (row >= 5) continue;
        const ci = (demoMarquee.offset + col) % demoMarquee.columns.length;
        const lit = demoMarquee.columns[ci] && demoMarquee.columns[ci][row];
        demoColors.push({row,col,hue:activeHue,sat:lit?255:0});
      }
      for (let c=0; c<COLS; c++) demoColors.push({row:5,col:c,hue:activeHue,sat:120});

    }

    updateKeyboard(demoColors);

    // FPS counter
    frameCount++;
    const now = performance.now();
    if (now - lastFpsTime >= 1000) {
      displayFps = frameCount;
      frameCount = 0;
      lastFpsTime = now;
      document.getElementById("fpsCounter").textContent = `${displayFps} FPS`;
      document.getElementById("statFps").textContent = `${displayFps}`;
    }

    requestAnimationFrame(demoFrame);
  }

  demoFrame();
}

// ── pywebview Bridge State Handler ────────────────────────────────────

let lastSeq = -1;

// Receives game state from Python (via polling get_state)
function onGameState(data) {
  if (!data) return;
  // Skip duplicate frames (poll can return same state multiple times)
  if (data.seq !== undefined && data.seq === lastSeq) return;
  lastSeq = data.seq || -1;

  // Connection status
  if (data.connected !== undefined) {
    const dict = LANG[currentLang] || LANG.en;
    const dot = document.getElementById("statusDot");
    const txt = document.getElementById("statusText");
    if (data.connected) {
      dot.classList.add("connected");
      txt.textContent = dict.connected;
    } else {
      dot.classList.remove("connected");
      txt.textContent = dict.no_device;
    }
  }

  if (data.colors) {
    updateKeyboard(data.colors);
  }

  if (data.mode) {
    const dict = LANG[currentLang] || LANG.en;
    document.getElementById("statMode").textContent = dict["mode_" + data.mode] || data.mode.toUpperCase();
    // Sync tab highlight
    document.querySelectorAll(".tab").forEach(t =>
      t.classList.toggle("active", t.dataset.mode === data.mode)
    );
    // Show/hide marquee controls
    document.getElementById("marqueeControls").style.display = data.mode === "marquee" ? "flex" : "none";
    document.getElementById("statsPanel").style.display = data.mode === "marquee" ? "none" : "flex";
  }
  if (data.score !== undefined) {
    document.getElementById("statScore").textContent = data.score;
  }
  if (data.fps !== undefined) {
    document.getElementById("statFps").textContent = data.fps;
    document.getElementById("fpsCounter").textContent = `${data.fps} FPS`;
  }
}

// ── Bridge Helpers (serialize calls, latest-wins) ────────────────────

let speedInFlight = false;
let pendingSpeed = null;

function sendSpeed(v) {
  speedInFlight = true;
  pywebview.api.set_speed(v).finally(() => {
    speedInFlight = false;
    if (pendingSpeed !== null) {
      const n = pendingSpeed;
      pendingSpeed = null;
      sendSpeed(n);
    }
  });
}

// ── Init ─────────────────────────────────────────────────────────────

function init() {
  buildKeyboard();

  // Color palette — updates both JS demo and Python backend
  document.querySelectorAll(".color-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".color-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeHue = parseInt(btn.dataset.hue);
      if (window.pywebview && pywebview.api) {
        pywebview.api.set_hue(activeHue);
      }
    });
  });

  // Language buttons
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      setLang(btn.dataset.lang);
    });
  });

  // Tab clicks
  document.querySelectorAll(".tab[data-mode]").forEach(tab => {
    tab.addEventListener("click", () => {
      setActiveTab(tab.dataset.mode);
    });
  });

  // Speed slider — controls demo speed + pywebview bridge
  const slider = document.getElementById("speedSlider");
  slider.addEventListener("input", () => {
    document.getElementById("speedValue").textContent = slider.value;
    const val = parseInt(slider.value);
    // Update demo interval directly
    demoInterval = SPEED_TO_MS[val] || 120;
    // Also send to Python bridge if available
    if (window.pywebview && pywebview.api) {
      if (speedInFlight) {
        pendingSpeed = val;
      } else {
        sendSpeed(val);
      }
    }
  });

  // Fullscreen toggle
  document.getElementById("fullscreenBtn").addEventListener("click", () => {
    if (window.pywebview && pywebview.api) {
      pywebview.api.toggle_fullscreen();
    } else {
      document.documentElement.requestFullscreen?.();
    }
  });

  // F11
  document.addEventListener("keydown", (e) => {
    if (e.key === "F11") {
      e.preventDefault();
      if (window.pywebview && pywebview.api) {
        pywebview.api.toggle_fullscreen();
      } else {
        document.documentElement.requestFullscreen?.();
      }
    }
  });

  // Marquee text input — debounced, updates demo + bridge
  let marqueeTimer = null;
  document.getElementById("marqueeText").addEventListener("input", (e) => {
    clearTimeout(marqueeTimer);
    marqueeTimer = setTimeout(() => {
      // Update demo marquee directly
      const text = e.target.value.toUpperCase().trim() || "NUT65 PIPBOY";
      demoMarquee.columns = [];
      const padded = "  " + text + "  ";
      for (let i = 0; i < padded.length; i++) {
        const g = DEMO_FONT[padded[i]] || DEMO_FONT[' '];
        for (let cx = 0; cx < 5; cx++) {
          const col = []; for (let ry = 0; ry < 5; ry++) col.push(!!(g[ry] & (1<<cx)));
          demoMarquee.columns.push(col);
        }
        demoMarquee.columns.push([false,false,false,false,false]);
      }
      demoMarquee.offset = 0;
      // Also send to Python bridge
      if (window.pywebview && pywebview.api) {
        pywebview.api.set_marquee_text(e.target.value);
      }
    }, 150);
  });

  // Marquee mode radio
  document.querySelectorAll('input[name="marqueeMode"]').forEach(radio => {
    radio.addEventListener("change", (e) => {
      if (window.pywebview && pywebview.api) {
        pywebview.api.set_marquee_mode(e.target.value);
      }
    });
  });

  // pywebview bridge detection
  // CRITICAL: pywebview injects AFTER DOMContentLoaded/load events.
  // window.pywebview is undefined here. We wait for pywebviewready event.
  function startPolling() {
    if (pollingStarted) return;
    pollingStarted = true;

    // Stop demo if it was running
    if (demoRunning) {
      demoStopFlag = true;
      demoRunning = false;
    }

    pywebview.api.client_ready();
    document.getElementById("statusDot").classList.add("connected");
    const dict = LANG[currentLang] || LANG.en;
    document.getElementById("statusText").textContent = dict.connected;

    function poll() {
      pywebview.api.get_state().then(data => {
        if (data) onGameState(data);
      }).catch(() => {});
      setTimeout(poll, 80);
    }
    poll();
  }

  window.addEventListener("pywebviewready", startPolling);

  // If pywebview doesn't appear within 2s, start demo.
  // Demo will auto-stop when pywebview connects later.
  setTimeout(() => {
    if (!pollingStarted) {
      const dict = LANG[currentLang] || LANG.en;
      document.getElementById("statusText").textContent = dict.demo_mode;
      demoRunning = true;
      runDemoAnimation();
    }
  }, 2000);
}

document.addEventListener("DOMContentLoaded", init);
