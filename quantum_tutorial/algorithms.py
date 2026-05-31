"""Tutorial-ready quantum algorithm definitions and simulation helpers.

The module uses Qiskit Aer when it is installed.  A small educational fallback is
kept for local development environments that have not installed Qiskit yet; the
fallback only covers the curated tutorial algorithms in ``ALGORITHMS``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .timeline import build_state_timeline, normalize_input_state


@dataclass(frozen=True)
class AlgorithmLesson:
    """Metadata and teaching content for one simulated algorithm."""

    key: str
    title: str
    summary: str
    objective: str
    steps: tuple[str, ...]
    qiskit_concepts: tuple[str, ...]
    expected_counts: dict[str, int]
    fallback_circuit: str


ALGORITHMS: dict[str, AlgorithmLesson] = {
    "bell": AlgorithmLesson(
        key="bell",
        title="Bell State: entanglement in two gates",
        summary="Create a pair of qubits whose measurement results are perfectly correlated.",
        objective="Learn how Hadamard and CNOT gates produce a simple entangled state.",
        steps=(
            "Start with two qubits initialized to |00〉.",
            "Apply H to q0 to place it in an equal superposition.",
            "Apply CX from q0 to q1 so q1 follows q0.",
            "Measure both qubits; ideal shots should be split between 00 and 11.",
        ),
        qiskit_concepts=("QuantumCircuit", "h", "cx", "measure_all", "AerSimulator"),
        expected_counts={"00": 512, "11": 512},
        fallback_circuit="q0: ┤ H ├──■──┤M├\nq1: ───────┼X─┤M├",
    ),
    "ghz": AlgorithmLesson(
        key="ghz",
        title="GHZ State: scale entanglement to three qubits",
        summary="Build a three-qubit state where every qubit agrees when measured.",
        objective="See how a chain of CNOT gates distributes one superposition across more qubits.",
        steps=(
            "Start with |000〉.",
            "Apply H to q0 to create the branch point.",
            "Apply CX q0→q1 and CX q1→q2 to copy the branch through the register.",
            "Measure; ideal shots should appear only as 000 and 111.",
        ),
        qiskit_concepts=("multi-qubit circuits", "h", "cx", "measurement histograms"),
        expected_counts={"000": 512, "111": 512},
        fallback_circuit="q0: ┤ H ├──■──────┤M├\nq1: ───────┼X──■──┤M├\nq2: ───────────┼X─┤M├",
    ),
    "deutsch-jozsa": AlgorithmLesson(
        key="deutsch-jozsa",
        title="Deutsch-Jozsa: identify a balanced oracle",
        summary="Use interference to tell whether a hidden Boolean oracle is balanced in one query.",
        objective="Practice phase kickback and the idea of querying a quantum oracle once.",
        steps=(
            "Prepare two input qubits and one output qubit.",
            "Set the output qubit to |1〉, then apply H gates to all qubits.",
            "Use a balanced oracle that flips the output for selected input patterns.",
            "Uncompute the input superposition with H gates and measure only the input qubits.",
        ),
        qiskit_concepts=("oracles", "phase kickback", "classical bits", "partial measurement"),
        expected_counts={"11": 1024},
        fallback_circuit="q0: ┤ H ├──■──┤ H ├──┤M├\nq1: ┤ H ├──■──┤ H ├──┤M├\nq2: ┤ X ├┤ H ├┤ X ├─────",
    ),
    "grover": AlgorithmLesson(
        key="grover",
        title="Grover Search: amplify one marked answer",
        summary="Use an oracle to find the marked two-bit state |11〉 with one Grover iteration.",
        objective="Observe how an oracle plus diffusion increases the probability of the target state.",
        steps=(
            "Place two search qubits into uniform superposition with H gates.",
            "Mark |11〉 using a controlled-Z oracle.",
            "Apply the two-qubit diffusion operator to reflect amplitudes around the mean.",
            "Measure; the target bitstring 11 should dominate the histogram.",
        ),
        qiskit_concepts=("controlled phase", "oracle", "diffusion", "amplitude amplification"),
        expected_counts={"11": 1024},
        fallback_circuit="q0: ┤ H ├─■─┤ H ├┤ X ├─■─┤ X ├┤ H ├┤M├\nq1: ┤ H ├─■─┤ H ├┤ X ├─■─┤ X ├┤ H ├┤M├",
    ),
}


def _validate_algorithm(algorithm: str) -> AlgorithmLesson:
    try:
        return ALGORITHMS[algorithm]
    except KeyError as exc:
        choices = ", ".join(sorted(ALGORITHMS))
        raise ValueError(f"Unknown algorithm '{algorithm}'. Choose one of: {choices}.") from exc


def _initialize_input(circuit, input_state: str) -> None:
    """Apply X gates for the requested initial computational basis state."""
    for qubit, bit in enumerate(input_state):
        if bit == "1":
            circuit.x(qubit)


def _build_qiskit_circuit(algorithm: str, input_state: str | None = None):
    """Return a measured Qiskit circuit for a tutorial algorithm."""
    normalized_input = normalize_input_state(algorithm, input_state)
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

    if algorithm == "bell":
        circuit = QuantumCircuit(2, 2)
        _initialize_input(circuit, normalized_input)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
        return circuit

    if algorithm == "ghz":
        circuit = QuantumCircuit(3, 3)
        _initialize_input(circuit, normalized_input)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.measure([0, 1, 2], [0, 1, 2])
        return circuit

    if algorithm == "deutsch-jozsa":
        qr = QuantumRegister(3, "q")
        cr = ClassicalRegister(2, "c")
        circuit = QuantumCircuit(qr, cr)
        _initialize_input(circuit, normalized_input)
        circuit.x(qr[2])
        circuit.h(qr)
        circuit.cx(qr[0], qr[2])
        circuit.cx(qr[1], qr[2])
        circuit.h(qr[0])
        circuit.h(qr[1])
        circuit.measure(qr[0], cr[0])
        circuit.measure(qr[1], cr[1])
        return circuit

    if algorithm == "grover":
        circuit = QuantumCircuit(2, 2)
        _initialize_input(circuit, normalized_input)
        circuit.h([0, 1])
        circuit.cz(0, 1)
        circuit.h([0, 1])
        circuit.x([0, 1])
        circuit.cz(0, 1)
        circuit.x([0, 1])
        circuit.h([0, 1])
        circuit.measure([0, 1], [0, 1])
        return circuit

    raise AssertionError(f"Unhandled algorithm: {algorithm}")


def _simulate_with_qiskit(algorithm: str, shots: int, input_state: str) -> dict[str, object]:
    from qiskit import transpile
    from qiskit_aer import AerSimulator

    circuit = _build_qiskit_circuit(algorithm, input_state)
    simulator = AerSimulator(seed_simulator=42)
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=shots).result()
    counts = dict(sorted(result.get_counts(compiled).items()))
    return {
        "counts": counts,
        "circuit_diagram": circuit.draw(output="text").single_string(),
        "engine": "Qiskit AerSimulator",
        "qiskit_available": True,
    }


def _scale_counts(expected_counts: dict[str, int], shots: int) -> dict[str, int]:
    total = sum(expected_counts.values())
    scaled: dict[str, int] = {}
    assigned = 0
    items = list(expected_counts.items())
    for index, (state, count) in enumerate(items):
        if index == len(items) - 1:
            scaled[state] = shots - assigned
        else:
            value = round(shots * count / total)
            scaled[state] = value
            assigned += value
    return scaled


def _simulate_with_fallback(lesson: AlgorithmLesson, shots: int, input_state: str, error: Exception) -> dict[str, object]:
    timeline = build_state_timeline(lesson.key, input_state)
    measured_width = len(next(iter(lesson.expected_counts)))
    expected_counts: dict[str, int] = {}
    for state, probability in timeline["final_probabilities"].items():
        measured_state = state[:measured_width]
        expected_counts[measured_state] = expected_counts.get(measured_state, 0) + round(probability * 1024)
    return {
        "counts": _scale_counts(expected_counts, shots),
        "circuit_diagram": lesson.fallback_circuit,
        "engine": "Educational fallback simulator (install qiskit and qiskit-aer for AerSimulator)",
        "qiskit_available": False,
        "qiskit_error": str(error),
    }


def simulate_algorithm(algorithm: str, shots: int = 1024, input_state: str | None = None) -> dict[str, object]:
    """Simulate one tutorial algorithm and return JSON-serializable data."""
    lesson = _validate_algorithm(algorithm)
    normalized_input = normalize_input_state(algorithm, input_state)
    bounded_shots = max(1, min(int(shots), 8192))
    try:
        simulation = _simulate_with_qiskit(algorithm, bounded_shots, normalized_input)
    except (ImportError, ModuleNotFoundError) as exc:
        simulation = _simulate_with_fallback(lesson, bounded_shots, normalized_input, exc)

    probabilities = {
        state: round(count / bounded_shots, 4)
        for state, count in sorted(simulation["counts"].items())
    }
    return {
        "algorithm": lesson.key,
        "shots": bounded_shots,
        "input_state": normalized_input,
        "probabilities": probabilities,
        **simulation,
    }


def build_lesson_payload(simulator: Callable[[str, int], dict[str, object]] | None = None) -> dict[str, object]:
    """Return lesson metadata plus an initial Bell-state simulation."""
    run_simulation = simulator or simulate_algorithm
    return {
        "lessons": [lesson.__dict__ for lesson in ALGORITHMS.values()],
        "initial_simulation": run_simulation("bell", 1024),
        "initial_timeline": build_state_timeline("bell", "00"),
    }
