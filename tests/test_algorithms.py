from quantum_tutorial.algorithms import ALGORITHMS, build_lesson_payload, simulate_algorithm
from quantum_tutorial.timeline import build_state_timeline, normalize_input_state


def test_lessons_include_beginner_algorithm_path():
    assert list(ALGORITHMS) == ["bell", "ghz", "deutsch-jozsa", "grover"]
    assert "Hadamard" in ALGORITHMS["bell"].objective
    assert "oracle" in ALGORITHMS["grover"].summary.lower()


def test_simulation_fallback_or_qiskit_counts_are_bounded():
    result = simulate_algorithm("bell", 32)

    assert result["algorithm"] == "bell"
    assert result["shots"] == 32
    assert sum(result["counts"].values()) == 32
    assert set(result["counts"]).issubset({"00", "11"})
    assert result["circuit_diagram"]
    assert "engine" in result


def test_shots_are_clamped_for_tutorial_safety():
    result = simulate_algorithm("ghz", 999_999)

    assert result["shots"] == 8192
    assert sum(result["counts"].values()) == 8192


def test_unknown_algorithm_raises_helpful_error():
    try:
        simulate_algorithm("teleportation")
    except ValueError as exc:
        assert "Unknown algorithm" in str(exc)
        assert "bell" in str(exc)
    else:
        raise AssertionError("Expected ValueError for an unknown algorithm")


def test_build_lesson_payload_accepts_mock_simulator():
    payload = build_lesson_payload(lambda algorithm, shots: {"algorithm": algorithm, "shots": shots})

    assert len(payload["lessons"]) == 4
    assert payload["initial_simulation"] == {"algorithm": "bell", "shots": 1024}


def test_state_timeline_tracks_entanglement_for_bell_state():
    timeline = build_state_timeline("bell", "00")

    assert timeline["input_state"] == "00"
    assert [frame["index"] for frame in timeline["frames"]] == [0, 1, 2]
    assert timeline["frames"][0]["qubits"][0]["spin"] == "up"
    assert timeline["frames"][1]["qubits"][0]["spin"] == "superposition"
    assert all(qubit["spin"] == "entangled" for qubit in timeline["frames"][-1]["qubits"])
    assert timeline["final_probabilities"] == {"00": 0.5, "11": 0.5}


def test_state_timeline_accepts_custom_input_qubits():
    timeline = build_state_timeline("grover", "10")

    assert timeline["input_state"] == "10"
    assert timeline["qubit_count"] == 2
    assert len(timeline["frames"]) == 8
    assert abs(sum(timeline["final_probabilities"].values()) - 1) < 1e-9


def test_input_state_validation_mentions_expected_width():
    try:
        normalize_input_state("ghz", "10")
    except ValueError as exc:
        assert "3-bit" in str(exc)
    else:
        raise AssertionError("Expected ValueError for wrong input width")
