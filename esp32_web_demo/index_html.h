#ifndef INDEX_HTML_H
#define INDEX_HTML_H

#include <pgmspace.h>

const char INDEX_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>TMLC ESP32 TinyML Digit Classifier</title>
<style>
  :root {
    --bg-dark: #090d16;
    --card-bg: rgba(30, 41, 59, 0.7);
    --border-color: rgba(255, 255, 255, 0.1);
    --accent-emerald: #10b981;
    --accent-cyan: #38bdf8;
    --accent-indigo: #6366f1;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body {
    background: radial-gradient(circle at top, #1e293b 0%, #090d16 100%);
    color: var(--text-main);
    min-height: 100vh;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .container {
    max-width: 900px;
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  header {
    text-align: center;
    padding: 12px 0 6px;
  }
  .badge-live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: var(--accent-emerald);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
  }
  .badge-live::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent-emerald);
    box-shadow: 0 0 8px var(--accent-emerald);
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }
  h1 { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; }
  .subtitle { font-size: 0.85rem; color: var(--text-muted); margin-top: 4px; }
  
  .specs-bar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
  }
  .spec-pill {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  .spec-pill strong { color: var(--accent-cyan); }

  .main-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
  }
  @media (min-width: 768px) {
    .main-grid { grid-template-columns: 340px 1fr; }
  }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
  }

  /* Canvas Drawing Area */
  .canvas-wrapper {
    position: relative;
    width: 280px;
    height: 280px;
    border-radius: 14px;
    overflow: hidden;
    border: 2px solid rgba(56, 189, 248, 0.3);
    box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8), 0 0 15px rgba(56, 189, 248, 0.15);
    background: #000;
    margin-bottom: 12px;
  }
  #drawCanvas {
    width: 280px;
    height: 280px;
    cursor: crosshair;
    touch-action: none;
    display: block;
  }
  .center-guideline {
    position: absolute;
    top: 35px; left: 35px; right: 35px; bottom: 35px;
    border: 1px dashed rgba(255, 255, 255, 0.15);
    pointer-events: none;
    border-radius: 8px;
  }
  .guide-label {
    position: absolute;
    bottom: 8px;
    left: 0; right: 0;
    text-align: center;
    font-size: 0.65rem;
    color: rgba(255, 255, 255, 0.3);
    pointer-events: none;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Controls */
  .btn-row {
    display: flex;
    width: 100%;
    gap: 8px;
    margin-bottom: 12px;
  }
  button {
    flex: 1;
    padding: 10px 14px;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .btn-primary {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #fff;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }
  .btn-primary:active { transform: scale(0.98); }
  .btn-secondary {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-main);
    border: 1px solid var(--border-color);
  }
  .btn-secondary:hover { background: rgba(255, 255, 255, 0.12); }

  .auto-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.78rem;
    color: var(--text-muted);
    cursor: pointer;
    margin-bottom: 12px;
    user-select: none;
  }

  /* Preset Samples */
  .preset-section {
    width: 100%;
    border-top: 1px solid var(--border-color);
    padding-top: 10px;
  }
  .preset-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    margin-bottom: 8px;
    text-align: center;
  }
  .preset-buttons {
    display: flex;
    gap: 6px;
    justify-content: center;
  }
  .btn-preset {
    flex: 0 1 auto;
    padding: 6px 10px;
    font-size: 0.75rem;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: var(--accent-cyan);
    border-radius: 8px;
  }
  .btn-preset:hover { background: rgba(56, 189, 248, 0.2); }

  /* Output Dashboard */
  .results-card {
    align-items: stretch;
    justify-content: flex-start;
  }
  .hero-result {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
  }
  .digit-display {
    display: flex;
    flex-direction: column;
  }
  .digit-label { font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; }
  .digit-value { font-size: 3.2rem; font-weight: 900; line-height: 1; color: var(--accent-emerald); text-shadow: 0 0 16px rgba(16, 185, 129, 0.4); }
  
  .telemetry-col {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }
  .telem-chip {
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
    display: flex;
    gap: 6px;
  }
  .chip-conf { background: rgba(16, 185, 129, 0.15); color: var(--accent-emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
  .chip-time { background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); border: 1px solid rgba(56, 189, 248, 0.3); }

  .preview-section {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 14px;
  }
  #previewCanvas {
    width: 48px;
    height: 48px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    image-rendering: pixelated;
    background: #000;
  }
  .preview-text { font-size: 0.72rem; color: var(--text-muted); line-height: 1.4; }
  .preview-text strong { color: var(--text-main); }

  /* Probability Bars */
  .bars-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: 100%;
  }
  .bar-row {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.78rem;
    font-family: monospace;
  }
  .bar-digit {
    width: 22px;
    font-weight: 700;
    text-align: right;
    color: var(--text-muted);
  }
  .bar-track {
    flex: 1;
    height: 14px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    overflow: hidden;
    position: relative;
  }
  .bar-fill {
    height: 100%;
    width: 0%;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    transition: width 0.25s ease, background 0.25s ease;
  }
  .bar-row.active .bar-digit { color: var(--accent-emerald); font-size: 0.9rem; }
  .bar-row.active .bar-fill {
    background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
  }
  .bar-val {
    width: 48px;
    text-align: right;
    font-size: 0.72rem;
    color: var(--text-muted);
  }
  .bar-row.active .bar-val { color: var(--accent-emerald); font-weight: 700; }
</style>
</head>
<body>

<div class="container">
  <header>
    <div class="badge-live">ESP32 Inference Engine Online</div>
    <h1>TMLC TinyML Digit Classifier</h1>
    <p class="subtitle">Real-time edge neural network compiled with ANSI C99 int8 quantization</p>
  </header>

  <div class="specs-bar">
    <div class="spec-pill">Model: <strong>784 &rarr; 128 &rarr; 64 &rarr; 10</strong></div>
    <div class="spec-pill">Quantization: <strong>int8 symmetric</strong></div>
    <div class="spec-pill">Weights: <strong>110 KB Flash</strong></div>
    <div class="spec-pill">Peak SRAM: <strong>768 Bytes</strong></div>
    <div class="spec-pill">Zero Malloc: <strong>100% Static</strong></div>
  </div>

  <div class="main-grid">
    <!-- Drawing Card -->
    <div class="card">
      <div class="canvas-wrapper">
        <canvas id="drawCanvas" width="280" height="280"></canvas>
        <div class="center-guideline"></div>
        <div class="guide-label">Draw large in center</div>
      </div>

      <div class="btn-row">
        <button class="btn-primary" id="btnClassify">Classify Digit</button>
        <button class="btn-secondary" id="btnClear">Clear</button>
      </div>

      <label class="auto-toggle">
        <input type="checkbox" id="autoPredict" checked>
        <span>Auto-classify on finger release</span>
      </label>

      <div class="preset-section">
        <div class="preset-title">Test Ground Truth Samples</div>
        <div class="preset-buttons">
          <button class="btn-preset" data-preset="0">Test 0</button>
          <button class="btn-preset" data-preset="1">Test 1</button>
          <button class="btn-preset" data-preset="3">Test 3</button>
          <button class="btn-preset" data-preset="7">Test 7</button>
          <button class="btn-preset" data-preset="8">Test 8</button>
        </div>
      </div>
    </div>

    <!-- Results Card -->
    <div class="card results-card">
      <div class="hero-result">
        <div class="digit-display">
          <span class="digit-label">Predicted Digit</span>
          <span class="digit-value" id="predDigit">-</span>
        </div>
        <div class="telemetry-col">
          <div class="telem-chip chip-conf">
            <span>Confidence:</span> <strong id="predConf">0.0%</strong>
          </div>
          <div class="telem-chip chip-time">
            <span>Latency:</span> <strong id="predTime">0 &mu;s</strong>
          </div>
        </div>
      </div>

      <div class="preview-section">
        <canvas id="previewCanvas" width="28" height="28"></canvas>
        <div class="preview-text">
          <strong>MCU Input Tensor (28&times;28)</strong><br>
          Center-of-mass normalized input fed to C99 kernel
        </div>
      </div>

      <div class="bars-container" id="barsContainer">
        <!-- Generated 0..9 bars -->
      </div>
    </div>
  </div>
</div>

<script>
// Ground-truth benchmark test samples (MNIST t10k partition)
const SAMPLES = {
  "0": "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000b96fdca1f000000000000000000000000000000000000000000000025fbfbfd6b0000000000000000000000000000000000000000000015c5fbfbfd6b0000000000000000000000000000000000000000006ebefbfbfbfda96d3e00000000000000000000000000000000000000fdfbfbfbfbfdfbfbdc330000000000000000000000000000000000b6fffdfdfdfdeadefdfdfd000000000000000000000000000000003fddfdfbfbfb934d3e80fbfb69000000000000000000000000000020e7fbfdfbdc890a00001fe6fbf3710500000000000000000000000025fbfbfdbc1400000000006dfbfdfb2300000000000000000000000025fbfbc91e0000000000001fc8fdfb2300000000000000000000000025fdfd000000000000000020cafffda40000000000000000000000008cfbfb00000000000000006dfbfdfb23000000000000000000000000d9fbfb000000000000153fe7fbfde61e000000000000000000000000d9fbfb00000000000090fbfbfbdd3d00000000000000000000000000d9fbfb0000000000b6ddfbfbfbb40000000000000000000000000000dafdfd4949e4fdfdfffdfdfdfd00000000000000000000000000000071fbfbfdfbfbfbfbfdfbfbfb930000000000000000000000000000001fe6fbfdfbfbfbfbfde6bd230a000000000000000000000000000000003e8efdfbfbfbfbfd6b00000000000000000000000000000000000000000048aefbad47481e000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "1": "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000026fe6d0000000000000000000000000000000000000000000000000057fc520000000000000000000000000000000000000000000000000087f1000000000000000000000000000000000000000000000000002df4960000000000000000000000000000000000000000000000000054fe3f00000000000000000000000000000000000000000000000000cadf0b00000000000000000000000000000000000000000000000020fed8000000000000000000000000000000000000000000000000005ffec3000000000000000000000000000000000000000000000000008cfe4d00000000000000000000000000000000000000000000000039edcd080000000000000000000000000000000000000000000000007cffa500000000000000000000000000000000000000000000000000abfe5100000000000000000000000000000000000000000000000018e8d70000000000000000000000000000000000000000000000000078fe9f0000000000000000000000000000000000000000000000000097fe8e00000000000000000000000000000000000000000000000000e4fe420000000000000000000000000000000000000000000000003dfbfe420000000000000000000000000000000000000000000000008dfecd0300000000000000000000000000000000000000000000000ad7fe7900000000000000000000000000000000000000000000000005c6b00a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "3": "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c29929230000000000000000000000000000000000000000000000c81fdfdfdfaa312000000000000000000000000000000000000000085fdfdfdfdfdfde5460000000000000000000000000000000000000065fdfc91666bedfdf7800a0000000000000000000000000000000000b5fda70000003debfdfda30500000000000000000000000000000000fffd2b000000003ac1fdfda404000000000000000000000000000000bbfd20000000000037ecfdfd5600000000000000000000000000000092fd200064be57575793fdfd7b0000000000000000000000000000005efd4e28f8fdfdfdfdfdfdfddf540f000000000000000000000000000e5c0c23f0fdfdfdfdfdfdfdfdfdf4590a0000000000000000000000000000004ba1b3fdfdfdfdfdfdfdfdfdd12b000000000000000000000000000000000310102726101091f3fdfdb93000000000000000000000000000143a00000000000000003ad1fdfdb70000000000000000000000004dddf74f00000000000000000ddbfdf04800000000000000000000005af7fdfc39000000000000000035fbfdbf00000000000000000000000074fdfd3b000000000000000063fcfd910000000000000000000000000ebcfddd9e26000000006fd3f6fdfd91000000000000000000000000000cddf6fdfbf9f9f9f9fdfdfdfdc8130000000000000000000000000000005fb7e4fdfdfdfdfdfdc37c1700000000000000000000000000000000000018258a4a7e58250700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "7": "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000054b99f973c2400000000000000000000000000000000000000000000defefefefef1c6c6c6c6c6c6c6c6aa3400000000000000000000000043724872a3e3fee1fefefefae5fefe8c000000000000000000000000000000000011420e4343433b15ecfe6a00000000000000000000000000000000000000000000000053fdd112000000000000000000000000000000000000000000000016e9ff5300000000000000000000000000000000000000000000000081feee2c00000000000000000000000000000000000000000000003bf9fe3e00000000000000000000000000000000000000000000000085febb05000000000000000000000000000000000000000000000009cdf83a0000000000000000000000000000000000000000000000007efeb60000000000000000000000000000000000000000000000004bfbf039000000000000000000000000000000000000000000000013ddfea6000000000000000000000000000000000000000000000003cbfedb23000000000000000000000000000000000000000000000026fefe4d00000000000000000000000000000000000000000000001fe0fe7301000000000000000000000000000000000000000000000085fefe3400000000000000000000000000000000000000000000003df2fefe34000000000000000000000000000000000000000000000079fefedb28000000000000000000000000000000000000000000000079fecf12000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "8": "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064b0062b9b25e1300000000000000000000000000000000000f6fc3ee5e00d0f9fefe74000000000000000000000000000014326bc5f6b719000051f5fef95b0000000000000000000000001254e6fefedd560000017dfdfeb2350000000000000000000000000085fefed9760400003ecafef18308000000000000000000000000006bf4fed52d0000003ef0fedc1d00000000000000000000000000002cf6fed1310000001ff1fedd1b0000000000000000000000000000005ffefe3700000011c6feda1c000000000000000000000000000000001bdbfee990272accfecd0a00000000000000000000000000000000000073f8fefef4e9fedf1800000000000000000000000000000000000000002654a8f5fefefecf730900000000000000000000000000000000000000000eecfee6a3edf4d3500100000000000000000000000000000000000063fefe63000025e1fe8208000000000000000000000000000000000047fee50c00000002aafe33000000000000000000000000000000000060fefe120000000051fec6000000000000000000000000000000000050fefe120000000083fe77000000000000000000000000000000000005d6fe4e00000001b7f43f00000000000000000000000000000000000040fddf1800027efeb2000000000000000000000000000000000000000057eede77b1fed91b000000000000000000000000000000000000000000129ac4c4651900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
};

// Canvas and Drawing State
const canvas = document.getElementById('drawCanvas');
const ctx = canvas.getContext('2d');
const previewCanvas = document.getElementById('previewCanvas');
const prevCtx = previewCanvas.getContext('2d');

let isDrawing = false;
let hasStrokes = false;

// Initialize probability bars (0..9)
const barsContainer = document.getElementById('barsContainer');
for (let i = 0; i < 10; i++) {
  const row = document.createElement('div');
  row.className = 'bar-row';
  row.id = `barRow_${i}`;
  row.innerHTML = `
    <span class="bar-digit">${i}:</span>
    <div class="bar-track"><div class="bar-fill" id="barFill_${i}"></div></div>
    <span class="bar-val" id="barVal_${i}">0.0%</span>
  `;
  barsContainer.appendChild(row);
}

function clearCanvas() {
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  prevCtx.fillStyle = '#000000';
  prevCtx.fillRect(0, 0, previewCanvas.width, previewCanvas.height);
  hasStrokes = false;
  resetOutput();
}

function resetOutput() {
  document.getElementById('predDigit').textContent = '-';
  document.getElementById('predConf').textContent = '0.0%';
  document.getElementById('predTime').textContent = '0 \u03BCs';
  for (let i = 0; i < 10; i++) {
    const row = document.getElementById(`barRow_${i}`);
    row.classList.remove('active');
    document.getElementById(`barFill_${i}`).style.width = '0%';
    document.getElementById(`barVal_${i}`).textContent = '0.0%';
  }
}

// Drawing logic
function getCoords(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  if (e.touches && e.touches.length > 0) {
    return {
      x: (e.touches[0].clientX - rect.left) * scaleX,
      y: (e.touches[0].clientY - rect.top) * scaleY
    };
  }
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  };
}

function startDrawing(e) {
  e.preventDefault();
  isDrawing = true;
  hasStrokes = true;
  const p = getCoords(e);
  ctx.lineWidth = 22;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.strokeStyle = '#ffffff';
  ctx.beginPath();
  ctx.moveTo(p.x, p.y);
}

function draw(e) {
  if (!isDrawing) return;
  e.preventDefault();
  const p = getCoords(e);
  ctx.lineTo(p.x, p.y);
  ctx.stroke();
}

function stopDrawing(e) {
  if (!isDrawing) return;
  e.preventDefault();
  isDrawing = false;
  ctx.closePath();
  if (document.getElementById('autoPredict').checked) {
    processAndPredict();
  }
}

canvas.addEventListener('mousedown', startDrawing);
canvas.addEventListener('mousemove', draw);
window.addEventListener('mouseup', stopDrawing);

canvas.addEventListener('touchstart', startDrawing, { passive: false });
canvas.addEventListener('touchmove', draw, { passive: false });
window.addEventListener('touchend', stopDrawing, { passive: false });

document.getElementById('btnClear').addEventListener('click', clearCanvas);
document.getElementById('btnClassify').addEventListener('click', processAndPredict);

// Preprocessing: Bounding-box crop and Center-of-Mass normalization
function extractNormalized28x28() {
  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const d = imgData.data;
  const W = canvas.width;
  const H = canvas.height;

  // Find bounding box of drawn pixels
  let minX = W, minY = H, maxX = 0, maxY = 0;
  let totalIntensity = 0;
  let comX = 0, comY = 0;

  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const idx = (y * W + x) * 4;
      const val = d[idx]; // grayscale R component
      if (val > 20) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
        totalIntensity += val;
        comX += x * val;
        comY += y * val;
      }
    }
  }

  if (totalIntensity === 0 || minX > maxX || minY > maxY) {
    return null;
  }

  // Crop bounding box to an offscreen canvas
  const bboxW = Math.max(maxX - minX + 1, 1);
  const bboxH = Math.max(maxY - minY + 1, 1);
  const cropCanvas = document.createElement('canvas');
  cropCanvas.width = bboxW;
  cropCanvas.height = bboxH;
  const cropCtx = cropCanvas.getContext('2d');
  cropCtx.drawImage(canvas, minX, minY, bboxW, bboxH, 0, 0, bboxW, bboxH);

  // Scale into a 20x20 box maintaining aspect ratio
  const scale = 20 / Math.max(bboxW, bboxH);
  const targetW = Math.max(Math.round(bboxW * scale), 1);
  const targetH = Math.max(Math.round(bboxH * scale), 1);

  // Center within 28x28 canvas
  const off28 = document.createElement('canvas');
  off28.width = 28;
  off28.height = 28;
  const offCtx = off28.getContext('2d');
  offCtx.fillStyle = '#000000';
  offCtx.fillRect(0, 0, 28, 28);

  const startX = Math.round((28 - targetW) / 2);
  const startY = Math.round((28 - targetH) / 2);
  offCtx.drawImage(cropCanvas, 0, 0, bboxW, bboxH, startX, startY, targetW, targetH);

  // Render to UI preview canvas
  prevCtx.drawImage(off28, 0, 0, 28, 28);

  // Extract 784 bytes and convert to hex
  const finalData = offCtx.getImageData(0, 0, 28, 28).data;
  let hex = "";
  for (let i = 0; i < 784; i++) {
    const pixelVal = finalData[i * 4];
    hex += pixelVal.toString(16).padStart(2, '0');
  }
  return hex;
}

// Draw a preloaded hex string onto the canvas and trigger prediction
function loadHexSample(hexStr) {
  clearCanvas();
  const off28 = document.createElement('canvas');
  off28.width = 28;
  off28.height = 28;
  const offCtx = off28.getContext('2d');
  const imgData = offCtx.createImageData(28, 28);
  
  for (let i = 0; i < 784; i++) {
    const byteVal = parseInt(hexStr.substr(i * 2, 2), 16);
    imgData.data[i * 4] = byteVal;
    imgData.data[i * 4 + 1] = byteVal;
    imgData.data[i * 4 + 2] = byteVal;
    imgData.data[i * 4 + 3] = 255;
  }
  offCtx.putImageData(imgData, 0, 0);

  // Render preview
  prevCtx.drawImage(off28, 0, 0, 28, 28);

  // Scale up onto main drawing canvas
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off28, 0, 0, 28, 28, 0, 0, canvas.width, canvas.height);
  hasStrokes = true;

  sendPredictionRequest(hexStr);
}

// Preset button handlers
document.querySelectorAll('.btn-preset').forEach(btn => {
  btn.addEventListener('click', () => {
    const digitKey = btn.getAttribute('data-preset');
    if (SAMPLES[digitKey]) {
      loadHexSample(SAMPLES[digitKey]);
    }
  });
});

async function processAndPredict() {
  const hexPayload = extractNormalized28x28();
  if (!hexPayload) {
    resetOutput();
    return;
  }
  await sendPredictionRequest(hexPayload);
}

async function sendPredictionRequest(hexString) {
  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: hexString
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderResults(data);
  } catch (err) {
    console.error("Prediction error:", err);
    document.getElementById('predDigit').textContent = '!';
    document.getElementById('predConf').textContent = 'Error';
  }
}

function renderResults(data) {
  const predDigit = data.digit;
  const conf = data.confidence;
  const latency = data.latency_us;

  document.getElementById('predDigit').textContent = predDigit;
  document.getElementById('predConf').textContent = conf.toFixed(1) + '%';
  document.getElementById('predTime').textContent = latency.toLocaleString() + ' \u03BCs';

  for (let i = 0; i < 10; i++) {
    const row = document.getElementById(`barRow_${i}`);
    const fill = document.getElementById(`barFill_${i}`);
    const val = document.getElementById(`barVal_${i}`);
    const prob = (data.probabilities && data.probabilities[i]) ? data.probabilities[i] : 0;

    if (i === predDigit) {
      row.classList.add('active');
    } else {
      row.classList.remove('active');
    }
    fill.style.width = Math.min(Math.max(prob, 0), 100) + '%';
    val.textContent = prob.toFixed(1) + '%';
  }
}

// Initialize on page load
clearCanvas();
</script>

</body>
</html>
)rawliteral";

#endif // INDEX_HTML_H
