"""State-timeline helpers for explaining qubit spin/status over an algorithm."""

from __future__ import annotations

import math
from dataclasses import dataclass


EPSILON = 1e-9
SQRT2 = math.sqrt(2)


@dataclass(frozen=True)
class GateOperation:
    """One educational algorithm operation applied at a visible timeframe."""

    gate: str
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()
    label: str = ""


def _algorithm_qubit_count(algorithm: str) -> int:
    if algorithm == "ghz" or algorithm == "deutsch-jozsa":
        return 3
    return 2


def _default_input_state(algorithm: str) -> str:
    return "0" * _algorithm_qubit_count(algorithm)


def normalize_input_state(algorithm: str, input_state: str | None = None) -> str:
    """Validate and normalize the requested starting computational basis state."""
    qubit_count = _algorithm_qubit_count(algorithm)
    candidate = _default_input_state(algorithm) if input_state is None else input_state.strip()
    if len(candidate) != qubit_count or any(bit not in "01" for bit in candidate):
        raise ValueError(
            f"Input state for {algorithm} must be a {qubit_count}-bit string such as "
            f"{_default_input_state(algorithm)}."
        )
    return candidate


def _operations_for_algorithm(algorithm: str) -> tuple[GateOperation, ...]:
    if algorithm == "bell":
        return (
            GateOperation("H", (0,), label="Create superposition on q0"),
            GateOperation("CX", (1,), controls=(0,), label="Entangle q1 with q0"),
        )

    if algorithm == "ghz":
        return (
            GateOperation("H", (0,), label="Create superposition on q0"),
            GateOperation("CX", (1,), controls=(0,), label="Copy branch from q0 to q1"),
            GateOperation("CX", (2,), controls=(1,), label="Copy branch from q1 to q2"),
        )

    if algorithm == "deutsch-jozsa":
        return (
            GateOperation("X", (2,), label="Prepare oracle output qubit q2 as |1〉"),
            GateOperation("H", (0, 1, 2), label="Create input superposition and |−〉 output"),
            GateOperation("CX", (2,), controls=(0,), label="Balanced oracle: q0 controls q2"),
            GateOperation("CX", (2,), controls=(1,), label="Balanced oracle: q1 controls q2"),
            GateOperation("H", (0, 1), label="Interfere input qubits before measurement"),
        )

    if algorithm == "grover":
        return (
            GateOperation("H", (0, 1), label="Create uniform search superposition"),
            GateOperation("CZ", (1,), controls=(0,), label="Oracle phase-marks |11〉"),
            GateOperation("H", (0, 1), label="Start diffusion transform"),
            GateOperation("X", (0, 1), label="Reflect around |00〉"),
            GateOperation("CZ", (1,), controls=(0,), label="Diffusion phase reflection"),
            GateOperation("X", (0, 1), label="Undo reflection bit flips"),
            GateOperation("H", (0, 1), label="Finish diffusion transform"),
        )

    choices = ", ".join(("bell", "ghz", "deutsch-jozsa", "grover"))
    raise ValueError(f"Unknown algorithm '{algorithm}'. Choose one of: {choices}.")


def _initial_statevector(input_state: str) -> dict[str, complex]:
    return {input_state: 1 + 0j}


def _apply_x(state: dict[str, complex], qubit: int) -> dict[str, complex]:
    next_state: dict[str, complex] = {}
    for bitstring, amplitude in state.items():
        bits = list(bitstring)
        bits[qubit] = "1" if bits[qubit] == "0" else "0"
        updated = "".join(bits)
        next_state[updated] = next_state.get(updated, 0j) + amplitude
    return _prune(next_state)


def _apply_h(state: dict[str, complex], qubit: int) -> dict[str, complex]:
    next_state: dict[str, complex] = {}
    for bitstring, amplitude in state.items():
        bits = list(bitstring)
        current = bits[qubit]
        zero_bits = bits.copy()
        one_bits = bits.copy()
        zero_bits[qubit] = "0"
        one_bits[qubit] = "1"
        if current == "0":
            contributions = (("".join(zero_bits), amplitude / SQRT2), ("".join(one_bits), amplitude / SQRT2))
        else:
            contributions = (("".join(zero_bits), amplitude / SQRT2), ("".join(one_bits), -amplitude / SQRT2))
        for target, value in contributions:
            next_state[target] = next_state.get(target, 0j) + value
    return _prune(next_state)


def _apply_cx(state: dict[str, complex], control: int, target: int) -> dict[str, complex]:
    next_state: dict[str, complex] = {}
    for bitstring, amplitude in state.items():
        bits = list(bitstring)
        if bits[control] == "1":
            bits[target] = "1" if bits[target] == "0" else "0"
        updated = "".join(bits)
        next_state[updated] = next_state.get(updated, 0j) + amplitude
    return _prune(next_state)


def _apply_cz(state: dict[str, complex], control: int, target: int) -> dict[str, complex]:
    next_state: dict[str, complex] = {}
    for bitstring, amplitude in state.items():
        phase = -1 if bitstring[control] == "1" and bitstring[target] == "1" else 1
        next_state[bitstring] = next_state.get(bitstring, 0j) + phase * amplitude
    return _prune(next_state)


def _apply_operation(state: dict[str, complex], operation: GateOperation) -> dict[str, complex]:
    updated = state
    if operation.gate == "H":
        for target in operation.targets:
            updated = _apply_h(updated, target)
    elif operation.gate == "X":
        for target in operation.targets:
            updated = _apply_x(updated, target)
    elif operation.gate == "CX":
        updated = _apply_cx(updated, operation.controls[0], operation.targets[0])
    elif operation.gate == "CZ":
        updated = _apply_cz(updated, operation.controls[0], operation.targets[0])
    else:
        raise ValueError(f"Unsupported gate '{operation.gate}'.")
    return updated


def _prune(state: dict[str, complex]) -> dict[str, complex]:
    return {bitstring: amplitude for bitstring, amplitude in sorted(state.items()) if abs(amplitude) > EPSILON}


def _format_complex(value: complex) -> str:
    real = 0.0 if abs(value.real) < EPSILON else value.real
    imag = 0.0 if abs(value.imag) < EPSILON else value.imag
    if imag == 0:
        return f"{real:.3f}"
    if real == 0:
        return f"{imag:.3f}i"
    sign = "+" if imag > 0 else "-"
    return f"{real:.3f}{sign}{abs(imag):.3f}i"


def _state_terms(state: dict[str, complex]) -> list[dict[str, object]]:
    return [
        {
            "state": bitstring,
            "amplitude": _format_complex(amplitude),
            "probability": round(abs(amplitude) ** 2, 4),
        }
        for bitstring, amplitude in state.items()
    ]


def _probabilities(state: dict[str, complex]) -> dict[str, float]:
    return {bitstring: round(abs(amplitude) ** 2, 4) for bitstring, amplitude in state.items()}


def _qubit_probabilities(state: dict[str, complex], qubit: int) -> tuple[float, float]:
    p0 = sum(abs(amplitude) ** 2 for bitstring, amplitude in state.items() if bitstring[qubit] == "0")
    p1 = sum(abs(amplitude) ** 2 for bitstring, amplitude in state.items() if bitstring[qubit] == "1")
    return p0, p1


def _is_entangled(state: dict[str, complex], qubit: int) -> bool:
    groups: dict[str, dict[str, complex]] = {"0": {}, "1": {}}
    for bitstring, amplitude in state.items():
        rest = bitstring[:qubit] + bitstring[qubit + 1 :]
        groups[bitstring[qubit]][rest] = groups[bitstring[qubit]].get(rest, 0j) + amplitude

    off_diagonal = sum(groups["0"].get(rest, 0j) * groups["1"].get(rest, 0j).conjugate() for rest in set(groups["0"]) | set(groups["1"]))
    p0, p1 = _qubit_probabilities(state, qubit)
    purity = p0**2 + p1**2 + 2 * abs(off_diagonal) ** 2
    return p0 > EPSILON and p1 > EPSILON and purity < 1 - 1e-6


def _qubit_statuses(state: dict[str, complex]) -> list[dict[str, object]]:
    qubit_count = len(next(iter(state)))
    statuses = []
    for qubit in range(qubit_count):
        p0, p1 = _qubit_probabilities(state, qubit)
        entangled = _is_entangled(state, qubit)
        if entangled:
            spin = "entangled"
            label = "Entangled / correlated"
        elif p0 > 1 - EPSILON:
            spin = "up"
            label = "Spin up |0〉"
        elif p1 > 1 - EPSILON:
            spin = "down"
            label = "Spin down |1〉"
        else:
            spin = "superposition"
            label = "Superposition"
        statuses.append(
            {
                "qubit": f"q{qubit}",
                "spin": spin,
                "label": label,
                "p0": round(p0, 4),
                "p1": round(p1, 4),
                "entangled": entangled,
            }
        )
    return statuses


def _timeline_entry(index: int, label: str, state: dict[str, complex]) -> dict[str, object]:
    return {
        "index": index,
        "label": label,
        "qubits": _qubit_statuses(state),
        "basis_states": _state_terms(state),
        "probabilities": _probabilities(state),
    }


def build_state_timeline(algorithm: str, input_state: str | None = None) -> dict[str, object]:
    """Return the expected qubit spin/status timeline for an algorithm and input state."""
    choices_tuple = ("bell", "ghz", "deutsch-jozsa", "grover")
    if algorithm not in choices_tuple:
        choices = ", ".join(choices_tuple)
        raise ValueError(f"Unknown algorithm '{algorithm}'. Choose one of: {choices}.")

    normalized_input = normalize_input_state(algorithm, input_state)
    state = _initial_statevector(normalized_input)
    frames = [_timeline_entry(0, f"Input |{normalized_input}〉", state)]
    for index, operation in enumerate(_operations_for_algorithm(algorithm), start=1):
        state = _apply_operation(state, operation)
        target_text = ", ".join(f"q{target}" for target in operation.targets)
        control_text = "" if not operation.controls else " controlled by " + ", ".join(f"q{control}" for control in operation.controls)
        label = f"{operation.gate} on {target_text}{control_text}: {operation.label}"
        frames.append(_timeline_entry(index, label, state))

    return {
        "algorithm": algorithm,
        "input_state": normalized_input,
        "qubit_count": len(normalized_input),
        "frames": frames,
        "final_probabilities": frames[-1]["probabilities"],
    }
