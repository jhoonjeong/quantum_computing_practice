"""Minimal Python web UI for the Qiskit quantum algorithm tutorial."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from quantum_tutorial import ALGORITHMS, build_lesson_payload, build_state_timeline, simulate_algorithm

HOST = "127.0.0.1"
PORT = 8000


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Quantum Algorithm Tutorial Simulator</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <header class="hero">
    <p class="eyebrow">Python + Qiskit simulation first</p>
    <h1>Quantum Computing Algorithm Tutorial</h1>
    <p class="lede">Learn beginner quantum algorithms by reading the circuit recipe, running a simulator, and comparing measurement histograms.</p>
  </header>

  <main class="layout">
    <section class="panel lesson-panel">
      <div class="section-title">
        <span>1</span>
        <div>
          <h2>Choose a tutorial</h2>
          <p>Start with entanglement, then move into oracle-based algorithms.</p>
        </div>
      </div>
      <div id="lessonCards" class="lesson-grid"></div>
    </section>

    <section class="panel simulator-panel">
      <div class="section-title">
        <span>2</span>
        <div>
          <h2>Run the simulator</h2>
          <p>Qiskit Aer is used when installed; otherwise the app shows an educational fallback for the same lesson.</p>
        </div>
      </div>

      <div class="controls">
        <label for="shots">Shots</label>
        <input id="shots" type="number" min="1" max="8192" value="1024" />
        <label for="inputState">Input qubits</label>
        <input id="inputState" class="bit-input" type="text" pattern="[01]+" value="00" aria-describedby="inputHelp" />
        <button id="runButton">Run simulation</button>
        <small id="inputHelp">Use a bitstring like 00 or 101, ordered q0→qn.</small>
      </div>

      <div id="status" class="status">Loading lessons…</div>

      <article id="lessonDetail" class="lesson-detail"></article>

      <div class="results">
        <div>
          <h3>Measurement histogram</h3>
          <div id="histogram" class="histogram"></div>
        </div>
        <div>
          <h3>Circuit diagram</h3>
          <pre id="circuitDiagram" class="circuit"></pre>
        </div>
      </div>

      <section class="timeline-section">
        <h3>Expected spin status by timeframe</h3>
        <p>Each frame shows the expected qubit status after a gate group, before measurement collapse.</p>
        <div id="timeline" class="timeline"></div>
      </section>
    </section>
  </main>

  <script src="/static/app.js"></script>
</body>
</html>
"""

STYLES_CSS = """:root {
  color-scheme: dark;
  --bg: #0b1020;
  --panel: rgba(22, 30, 58, 0.86);
  --panel-strong: #18213f;
  --text: #edf2ff;
  --muted: #aab6df;
  --accent: #7dd3fc;
  --accent-2: #c084fc;
  --good: #86efac;
  --border: rgba(255, 255, 255, 0.14);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  min-height: 100vh;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(125, 211, 252, 0.24), transparent 34rem),
    radial-gradient(circle at top right, rgba(192, 132, 252, 0.22), transparent 30rem),
    var(--bg);
  color: var(--text);
}

.hero {
  max-width: 1120px;
  margin: 0 auto;
  padding: 4rem 1.25rem 2rem;
}

.eyebrow {
  color: var(--accent);
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1 {
  max-width: 780px;
  margin: 0;
  font-size: clamp(2.5rem, 8vw, 5.5rem);
  line-height: 0.92;
}

.lede {
  max-width: 720px;
  color: var(--muted);
  font-size: 1.2rem;
  line-height: 1.7;
}

.layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(360px, 1.4fr);
  gap: 1.25rem;
  max-width: 1120px;
  margin: 0 auto 4rem;
  padding: 0 1.25rem;
}

.panel {
  border: 1px solid var(--border);
  border-radius: 28px;
  background: var(--panel);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(18px);
  padding: 1.25rem;
}

.section-title {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.section-title span {
  display: grid;
  width: 2.5rem;
  height: 2.5rem;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #07111f;
  font-weight: 900;
}

.section-title h2, .section-title p { margin: 0; }
.section-title p { color: var(--muted); margin-top: 0.25rem; }

.lesson-grid {
  display: grid;
  gap: 0.8rem;
}

.lesson-card {
  width: 100%;
  text-align: left;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.045);
  color: var(--text);
  padding: 1rem;
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}

.lesson-card:hover,
.lesson-card.active {
  transform: translateY(-2px);
  border-color: var(--accent);
  background: rgba(125, 211, 252, 0.11);
}

.lesson-card strong { display: block; margin-bottom: 0.35rem; }
.lesson-card small { color: var(--muted); line-height: 1.5; }

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
}

.controls input,
.controls button {
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 0.8rem 1rem;
  font: inherit;
}

.controls input {
  width: 8rem;
  background: #0d1530;
  color: var(--text);
}

.controls .bit-input {
  width: 9rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.controls small {
  flex-basis: 100%;
  color: var(--muted);
}

.controls button {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #07111f;
  font-weight: 900;
  cursor: pointer;
}

.status {
  border-radius: 16px;
  background: rgba(134, 239, 172, 0.09);
  color: var(--good);
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
}

.lesson-detail {
  display: grid;
  gap: 1rem;
  border-radius: 22px;
  background: var(--panel-strong);
  padding: 1rem;
  margin-bottom: 1rem;
}

.lesson-detail h3,
.lesson-detail p { margin: 0; }
.lesson-detail p, li { color: var(--muted); line-height: 1.55; }

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  color: var(--accent);
  background: rgba(125, 211, 252, 0.08);
  font-size: 0.85rem;
}

.results {
  display: grid;
  grid-template-columns: minmax(240px, 0.9fr) minmax(280px, 1.1fr);
  gap: 1rem;
}

.histogram {
  display: grid;
  gap: 0.75rem;
}

.bar-row {
  display: grid;
  grid-template-columns: 3.5rem 1fr 4rem;
  gap: 0.75rem;
  align-items: center;
}

.bar-track {
  height: 1.15rem;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}

.circuit {
  min-height: 14rem;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: #060914;
  color: #dbeafe;
  padding: 1rem;
}

.timeline-section {
  margin-top: 1.25rem;
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}

.timeline-section p { color: var(--muted); }

.timeline {
  display: grid;
  gap: 1rem;
}

.timeline-frame {
  border: 1px solid var(--border);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.045);
  padding: 1rem;
}

.timeline-frame h4 {
  margin: 0 0 0.75rem;
}

.qubit-row {
  display: grid;
  grid-template-columns: 4rem minmax(9rem, 1fr) 5rem 5rem;
  gap: 0.6rem;
  align-items: center;
  padding: 0.5rem 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.spin-pill {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  font-weight: 800;
}

.spin-up { background: rgba(125, 211, 252, 0.16); color: var(--accent); }
.spin-down { background: rgba(248, 113, 113, 0.16); color: #fca5a5; }
.spin-superposition { background: rgba(192, 132, 252, 0.16); color: #d8b4fe; }
.spin-entangled { background: rgba(134, 239, 172, 0.16); color: var(--good); }

.basis-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.basis-term {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #060914;
  color: #dbeafe;
  padding: 0.35rem 0.5rem;
}

@media (max-width: 860px) {
  .layout,
  .results { grid-template-columns: 1fr; }
}
"""

APP_JS = """let lessons = [];
let selectedAlgorithm = 'bell';

const lessonCards = document.querySelector('#lessonCards');
const lessonDetail = document.querySelector('#lessonDetail');
const histogram = document.querySelector('#histogram');
const circuitDiagram = document.querySelector('#circuitDiagram');
const statusBox = document.querySelector('#status');
const shotsInput = document.querySelector('#shots');
const inputState = document.querySelector('#inputState');
const timeline = document.querySelector('#timeline');
const runButton = document.querySelector('#runButton');

function setStatus(message, isWarning = false) {
  statusBox.textContent = message;
  statusBox.style.color = isWarning ? '#fde68a' : '#86efac';
  statusBox.style.background = isWarning ? 'rgba(253, 230, 138, 0.1)' : 'rgba(134, 239, 172, 0.09)';
}

function renderCards() {
  lessonCards.innerHTML = lessons.map((lesson) => `
    <button class="lesson-card ${lesson.key === selectedAlgorithm ? 'active' : ''}" data-algorithm="${lesson.key}">
      <strong>${lesson.title}</strong>
      <small>${lesson.summary}</small>
    </button>
  `).join('');

  document.querySelectorAll('.lesson-card').forEach((card) => {
    card.addEventListener('click', async () => {
      selectedAlgorithm = card.dataset.algorithm;
      updateInputPlaceholder();
      renderCards();
      await runSimulation();
    });
  });
}


function updateInputPlaceholder() {
  const lesson = lessons.find((item) => item.key === selectedAlgorithm);
  const size = lesson.key === 'ghz' || lesson.key === 'deutsch-jozsa' ? 3 : 2;
  inputState.maxLength = size;
  inputState.placeholder = '0'.repeat(size);
  if (!new RegExp(`^[01]{${size}}$`).test(inputState.value)) {
    inputState.value = '0'.repeat(size);
  }
}

function renderTimeline(stateTimeline) {
  timeline.innerHTML = stateTimeline.frames.map((frame) => `
    <article class="timeline-frame">
      <h4>t${frame.index}: ${frame.label}</h4>
      ${frame.qubits.map((qubit) => `
        <div class="qubit-row">
          <strong>${qubit.qubit}</strong>
          <span class="spin-pill spin-${qubit.spin}">${qubit.label}</span>
          <span>P(|0〉) ${Math.round(qubit.p0 * 100)}%</span>
          <span>P(|1〉) ${Math.round(qubit.p1 * 100)}%</span>
        </div>
      `).join('')}
      <div class="basis-list">
        ${frame.basis_states.map((term) => `<code class="basis-term">${term.amplitude}|${term.state}〉 · ${Math.round(term.probability * 100)}%</code>`).join('')}
      </div>
    </article>
  `).join('');
}

function renderLesson() {
  const lesson = lessons.find((item) => item.key === selectedAlgorithm);
  lessonDetail.innerHTML = `
    <div>
      <h3>${lesson.title}</h3>
      <p>${lesson.objective}</p>
    </div>
    <div>
      <strong>Algorithm recipe</strong>
      <ol>${lesson.steps.map((step) => `<li>${step}</li>`).join('')}</ol>
    </div>
    <div class="chips">
      ${lesson.qiskit_concepts.map((concept) => `<span class="chip">${concept}</span>`).join('')}
    </div>
  `;
}

function renderSimulation(simulation) {
  renderTimeline(simulation.timeline);
  const entries = Object.entries(simulation.counts).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(...entries.map(([, count]) => count), 1);
  histogram.innerHTML = entries.map(([state, count]) => {
    const width = (count / maxCount) * 100;
    const probability = simulation.probabilities[state];
    return `
      <div class="bar-row">
        <code>${state}</code>
        <div class="bar-track"><div class="bar-fill" style="width: ${width}%"></div></div>
        <span>${count} (${Math.round(probability * 100)}%)</span>
      </div>
    `;
  }).join('');
  circuitDiagram.textContent = simulation.circuit_diagram;

  const warning = !simulation.qiskit_available;
  setStatus(`${simulation.engine} · ${simulation.shots} shots`, warning);
}

async function runSimulation() {
  renderLesson();
  setStatus('Running simulation…');
  const response = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      algorithm: selectedAlgorithm,
      input_state: inputState.value,
      shots: Number(shotsInput.value) || 1024,
    }),
  });
  if (!response.ok) {
    setStatus('Simulation request failed. Check the server logs.', true);
    return;
  }
  renderSimulation(await response.json());
}

async function bootstrap() {
  const response = await fetch('/api/lessons');
  const payload = await response.json();
  lessons = payload.lessons;
  selectedAlgorithm = payload.initial_simulation.algorithm;
  updateInputPlaceholder();
  renderCards();
  renderLesson();
  renderSimulation({ ...payload.initial_simulation, timeline: payload.initial_timeline });
}

runButton.addEventListener('click', runSimulation);
bootstrap().catch((error) => setStatus(`Could not load tutorial: ${error.message}`, true));
"""


class TutorialHandler(BaseHTTPRequestHandler):
    """HTTP handler for static assets and JSON simulation endpoints."""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path
        if path == "/":
            self._send_text(INDEX_HTML, "text/html; charset=utf-8")
        elif path == "/static/styles.css":
            self._send_text(STYLES_CSS, "text/css; charset=utf-8")
        elif path == "/static/app.js":
            self._send_text(APP_JS, "text/javascript; charset=utf-8")
        elif path == "/api/lessons":
            self._send_json(build_lesson_payload())
        else:
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlparse(self.path).path
        if path != "/api/simulate":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body or "{}")
            algorithm = str(payload.get("algorithm", "bell"))
            raw_input_state = payload.get("input_state")
            input_state = None if raw_input_state is None else str(raw_input_state)
            shots = int(payload.get("shots", 1024))
            simulation = simulate_algorithm(algorithm, shots, input_state)
            simulation["timeline"] = build_state_timeline(algorithm, simulation["input_state"])
            self._send_json(simulation)
        except ValueError as exc:
            self._send_json({"error": str(exc), "choices": sorted(ALGORITHMS)}, HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON request body."}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: object) -> None:
        """Keep tutorial server logs concise."""
        print(f"{self.address_string()} - {format % args}")

    def _send_text(self, content: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run(host: str = HOST, port: int = PORT) -> None:
    """Run the local tutorial web server."""
    server = ThreadingHTTPServer((host, port), TutorialHandler)
    print(f"Quantum tutorial running at http://{host}:{port}")
    print("Install qiskit and qiskit-aer to use the Qiskit Aer simulator backend.")
    server.serve_forever()


if __name__ == "__main__":
    run()
