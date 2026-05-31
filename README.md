# Quantum Computing Practice

A simulation-first quantum computing algorithm tutorial built with Python and designed for Qiskit Aer. The web UI walks through beginner-friendly algorithms, explains the circuit recipe, lets learners run shot-based simulations, and visualizes the expected spin/status of every qubit at each algorithm timeframe before moving on to hardware.

## Tutorial modules

- **Bell state**: create two-qubit entanglement with `H` and `CX`.
- **GHZ state**: scale entanglement to three qubits.
- **Deutsch-Jozsa**: use an oracle and interference to identify a balanced function.
- **Grover search**: amplify a marked two-bit answer with one Grover iteration.

## Spin timeline

Every simulation response includes a state timeline for the selected algorithm and input qubits. A timeframe is recorded after each meaningful gate group, showing per-qubit probabilities for `|0〉` and `|1〉`, whether the qubit is in superposition, and whether it is entangled with the rest of the register.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python app.py
```

Open <http://127.0.0.1:8000>, choose a lesson, and enter an input bitstring such as `00`, `101`, or the default shown by the UI. The app renders each timeframe with qubit spin labels (`|0〉` up, `|1〉` down, superposition, or entangled), basis-state amplitudes, and measurement probabilities. The app will use `qiskit-aer` when it is installed. If Qiskit is not installed yet, the tutorial still loads with a deterministic educational fallback so the UI and lesson flow can be explored immediately.

## Run tests

```bash
pip install -e '.[dev]'
pytest
```

## Project layout

```text
app.py                         # Small standard-library web server and UI assets
quantum_tutorial/algorithms.py # Lesson metadata, Qiskit circuits, and simulations
tests/test_algorithms.py       # Unit tests for lessons and simulator behavior
```
