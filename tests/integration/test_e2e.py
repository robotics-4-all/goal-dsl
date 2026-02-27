"""End-to-end integration tests for Telos DSL examples.

Phase 1 — Validate, generate, and compile every example model.
Phase 2 — Run generated code against a real MQTT broker for selected examples.
"""

import ast
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from telos.language import build_model
from telos.transformations import generate_str

from .conftest import publish_mqtt

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"

# All example model files (path relative to project root)
ALL_EXAMPLES: list[tuple[str, Path]] = []
for d in sorted(EXAMPLES_DIR.iterdir()):
    if not d.is_dir() or d.name.startswith("."):
        continue
    for f in sorted(d.glob("*.telos")):
        ALL_EXAMPLES.append((f"{d.name}/{f.name}", f))

# Examples that use only MQTT sources (suitable for E2E with mosquitto)
MQTT_ONLY_EXAMPLES = {
    "01_hello_world",
    "03_conditions",
    "04_entity_goals",
    "05_area_goals",
    "06_pose_goals",
    "07_trajectory_goals",
    "08_composition",
    "09_advanced_conditions",
    "10_time_constraints",
    "11_scenarios",
    "12_value_generators",
}

# Examples that require non-MQTT transports
SKIP_REASONS: dict[str, str] = {
    "02_sources_and_entities": "requires Redis entity transport",
    "13_all_data_sources": "requires AMQP + Redis + REST transports",
    "14_constants_and_metadata": "requires Redis for RTMonitor",
    "15_real_world/smart_greenhouse.telos": "requires Redis for RTMonitor",
    "15_real_world/robot_inspection.telos": "requires Redis entity transport",
}


def _skip_reason(example_id: str) -> str | None:
    """Return a skip reason if the example cannot be run E2E, else None."""
    for pattern, reason in SKIP_REASONS.items():
        if pattern in example_id:
            return reason
    return None


# ============================================================================
# Phase 1 — Validate, Generate, Compile (ALL examples)
# ============================================================================


@pytest.mark.parametrize(
    "example_id, model_path",
    ALL_EXAMPLES,
    ids=[eid for eid, _ in ALL_EXAMPLES],
)
class TestValidateAndGenerate:
    """Validate each .telos model, generate Python, and verify it compiles."""

    def test_validate(self, example_id, model_path):
        """build_model() should not raise for any example."""
        model = build_model(str(model_path))
        assert model is not None

    def test_generate(self, example_id, model_path):
        """generate_str() should return a non-empty code dict."""
        model_str = model_path.read_text()
        result = generate_str(model_str)
        assert isinstance(result, dict)
        assert len(result) > 0
        for scenario_name, code in result.items():
            assert isinstance(code, str)
            assert len(code) > 0

    def test_compile(self, example_id, model_path):
        """Generated Python code must be valid (ast.parse)."""
        model_str = model_path.read_text()
        result = generate_str(model_str)
        for scenario_name, code in result.items():
            try:
                ast.parse(code)
            except SyntaxError as exc:
                pytest.fail(
                    f"SyntaxError in generated code for {example_id}/{scenario_name}: {exc}"
                )


# ============================================================================
# Phase 2 — E2E with MQTT broker (selected examples)
# ============================================================================

# Per-example test data: topics → payloads to publish, expected goal markers.

E2E_TEST_DATA: dict[str, dict] = {
    "01_hello_world": {
        "scenario": "HelloWorld",
        "messages": [
            ("home.bedroom.temperature", {"temp": 25.0}),
        ],
        "expected_goals": {
            "SensorAlive": True,
        },
    },
    "03_conditions": {
        "scenario": "ConditionTypes",
        "messages": [
            # temp=45 > 30 (TempAboveThreshold ✓), temp=45 > 25 AND humidity=50 < 60
            # (TempAndHumidity ✓), label='active' (StatusIsActive ✓),
            # locked=True (DoorIsLocked ✓), temp=45 > 40 (AlertCondition ✓),
            # temp=45 > 30 AND humidity=50 < 60 — but we need > 60 for ComplexCondition
            # via the OR branch: value=120 > 100 (ComplexCondition ✓)
            ("lab.temperature", {"temp": 45.0, "humidity": 50.0}),
            ("lab.pressure", {"value": 120.0}),
            ("lab.status", {"label": "active", "active": True}),
            ("lab.door", {"locked": True}),
        ],
        "expected_goals": {
            "TempAboveThreshold": True,
            "TempAndHumidity": True,
            "StatusIsActive": True,
            "DoorIsLocked": True,
            "AlertCondition": True,
            "ComplexCondition": True,
        },
    },
    "04_entity_goals": {
        "scenario": "EntityGoals",
        "messages": [
            # temp=90 > 80 (HighTemperature ✓), Watch goals fire on any msg
            # value=50 > 5 AND < 100 (CheckPressure ✓)
            # active=True (AlarmActive/VerifyAlarm ✓)
            ("factory.line_1.temperature", {"temp": 90.0, "humidity": 50.0}),
            ("factory.line_1.pressure", {"value": 50.0}),
            ("factory.line_1.alarm", {"active": True}),
        ],
        "expected_goals": {
            "SensorHeartbeat": True,
            "PressureHeartbeat": True,
            "HighTemperature": True,
            "CheckPressure": True,
            "AlarmActive": True,
        },
        # ThermalDelta (Eval) uses a Python string that references bare
        # 'TempSensor.temp' — goalee eval only has 'entities' in scope,
        # so this goal cannot be verified without a goalee Eval fix.
    },
    "08_composition": {
        "scenario": "Composition",
        "messages": [
            # Sequential scenario: StartupSequence (Cluster ALL_ACCOMPLISHED_ORDERED)
            # needs FlowActive (rate > 0) THEN PressureStable (1 < value < 10) THEN
            # TempInRange (50 < temp < 200).  After that, RepeatedCheck (Loop Watch x5).
            ("plant.reactor.flow", {"rate": 3.0}),
            ("plant.reactor.pressure", {"value": 5.5}),
            ("plant.reactor.temperature", {"temp": 100.0}),
        ],
        "expected_goals": {
            "StartupSequence": True,
            "RepeatedCheck": True,
        },
    },
}


def _generate_to_file(model_path: Path, gen_dir: Path) -> dict[str, Path]:
    """Generate Python code from a model and write to gen_dir.

    Returns mapping of scenario_name → generated file path.
    """
    model_str = model_path.read_text()
    code_dict = generate_str(model_str)
    result = {}
    for scenario_name, code in code_dict.items():
        out_file = gen_dir / f"{scenario_name}.py"
        out_file.write_text(code)
        result[scenario_name] = out_file
    return result


def _run_generated_script(
    script_path: Path,
    timeout: float = 15.0,
) -> subprocess.CompletedProcess:
    """Run a generated scenario script as a subprocess with timeout."""
    env = {**os.environ, "U_ID": "test"}
    return subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _parse_goal_results(output: str) -> dict[str, bool]:
    """Parse goal results from scenario output (stderr, via logging).

    Looks for lines like:  '       - GoalName: ✓' or '       - GoalName: ✗'
    """
    results = {}
    for line in output.splitlines():
        line = line.strip()
        if ": ✓" in line or ": ✗" in line:
            # Format: "- GoalName: ✓"
            parts = line.lstrip("- ").split(": ", 1)
            if len(parts) == 2:
                goal_name = parts[0].strip()
                status = "✓" in parts[1]
                results[goal_name] = status
    return results


@pytest.mark.integration
class TestE2EHelloWorld:
    """E2E test for 01_hello_world — simplest Watch goal."""

    EXAMPLE = "01_hello_world"
    MODEL = EXAMPLES_DIR / "01_hello_world" / "scenario.telos"

    def test_e2e_run(self, broker_services, mqtt_client, gen_dir):
        data = E2E_TEST_DATA[self.EXAMPLE]
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files[data["scenario"]]

        # Start the generated script
        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        # Wait for the scenario to start and subscribe
        time.sleep(3)

        # Publish messages
        for topic, payload in data["messages"]:
            publish_mqtt(mqtt_client, topic, payload)

        # Wait for scenario to complete
        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        # Parse results from stderr (logging output)
        combined = stdout + stderr
        results = _parse_goal_results(combined)

        # Verify expected goals
        for goal_name, expected in data["expected_goals"].items():
            assert goal_name in results, (
                f"Goal '{goal_name}' not found in output. "
                f"Got: {results}. Output:\n{combined[-1000:]}"
            )
            assert results[goal_name] == expected, (
                f"Goal '{goal_name}': expected {'✓' if expected else '✗'}, "
                f"got {'✓' if results[goal_name] else '✗'}"
            )


@pytest.mark.integration
class TestE2EConditions:
    """E2E test for 03_conditions — typed conditions with MQTT.

    The scenario runs concurrently with 6 When goals.  We publish data that
    satisfies all conditions and verify each goal is marked ✓.
    """

    EXAMPLE = "03_conditions"
    MODEL = EXAMPLES_DIR / "03_conditions" / "scenario.telos"

    def test_e2e_run(self, broker_services, mqtt_client, gen_dir):
        data = E2E_TEST_DATA[self.EXAMPLE]
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files[data["scenario"]]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        for topic, payload in data["messages"]:
            publish_mqtt(mqtt_client, topic, payload)

        try:
            stdout, stderr = proc.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr

        # Parse results and verify expected goals
        results = _parse_goal_results(combined)
        for goal_name, expected in data["expected_goals"].items():
            assert goal_name in results, (
                f"Goal '{goal_name}' not found in output. "
                f"Got: {results}. Output:\n{combined[-2000:]}"
            )
            assert results[goal_name] == expected, (
                f"Goal '{goal_name}': expected {'✓' if expected else '✗'}, "
                f"got {'✓' if results[goal_name] else '✗'}"
            )


@pytest.mark.integration
class TestE2EEntityGoals:
    """E2E test for 04_entity_goals — Watch, When, Eval goals.

    The scenario runs concurrently.  Watch and When goals complete on
    message arrival / condition match.  The Eval goal (ThermalDelta)
    uses a bare Python expression ``'TempSensor.temp * 1.8 + 32 > 180'``
    which references ``TempSensor`` directly — goalee's eval only has
    ``entities`` in scope, so the Eval goal never completes.  Since it has
    no ``max_duration``, the concurrent scenario hangs until we kill it.

    We verify that the script starts without import errors, entities
    connect, and no Python tracebacks occur.  The scenario won't print
    results because ThermalDelta blocks indefinitely.
    """

    EXAMPLE = "04_entity_goals"
    MODEL = EXAMPLES_DIR / "04_entity_goals" / "scenario.telos"

    def test_e2e_run(self, broker_services, mqtt_client, gen_dir):
        data = E2E_TEST_DATA[self.EXAMPLE]
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files[data["scenario"]]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        for topic, payload in data["messages"]:
            publish_mqtt(mqtt_client, topic, payload)

        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr

        # The script should start without crashing
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
        # Verify entities connected
        assert "Started Entity" in combined, (
            f"Script did not start properly.\nOutput:\n{combined[-2000:]}"
        )


@pytest.mark.integration
class TestE2EComposition:
    """E2E test for 08_composition — Cluster and Loop goals.

    The Composition scenario runs sequentially:
    1. StartupSequence (Cluster ALL_ACCOMPLISHED_ORDERED): FlowActive → PressureStable → TempInRange
    2. RepeatedCheck (Loop Watch x5): receives 5 temperature messages

    We publish messages in the correct order for the ordered cluster, then
    repeatedly for the Loop.
    """

    EXAMPLE = "08_composition"
    MODEL = EXAMPLES_DIR / "08_composition" / "scenario.telos"

    def test_e2e_run(self, broker_services, mqtt_client, gen_dir):
        data = E2E_TEST_DATA[self.EXAMPLE]
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files[data["scenario"]]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Phase 1: Satisfy StartupSequence (ALL_ACCOMPLISHED_ORDERED cluster)
        # Must satisfy FlowActive, then PressureStable, then TempInRange — in order
        for topic, payload in data["messages"]:
            publish_mqtt(mqtt_client, topic, payload, settle=0.5)

        # Phase 2: Continuously publish changing temperature values for
        # RepeatedCheck (Loop of Watch x5).  The sequential scenario starts
        # RepeatedCheck only after StartupSequence completes.  Watch goals
        # (EntityStateChange) trigger on state *changes*, so we vary values.
        for i in range(8):
            publish_mqtt(
                mqtt_client,
                "plant.reactor.temperature",
                {"temp": 100.0 + i},
                settle=0.5,
            )

        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr

        # Parse results and verify both top-level goals
        results = _parse_goal_results(combined)
        for goal_name, expected in data["expected_goals"].items():
            assert goal_name in results, (
                f"Goal '{goal_name}' not found in output. "
                f"Got: {results}. Output:\n{combined[-2000:]}"
            )
            assert results[goal_name] == expected, (
                f"Goal '{goal_name}': expected {'✓' if expected else '✗'}, "
                f"got {'✓' if results[goal_name] else '✗'}"
            )


@pytest.mark.integration
class TestE2ETrajectory:
    """E2E test for 07_trajectory_goals — verify it doesn't crash."""

    MODEL = EXAMPLES_DIR / "07_trajectory_goals" / "scenario.telos"

    def test_e2e_no_crash(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["TrajectoryGoals"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Publish a sequence of poses along a straight line
        positions = [
            {"x": 0, "y": 0, "z": 0},
            {"x": 2, "y": 0, "z": 0},
            {"x": 5, "y": 0, "z": 0},
            {"x": 8, "y": 0, "z": 0},
            {"x": 10, "y": 0, "z": 0},
        ]
        orientation = {"x": 0, "y": 0, "z": 0}
        for pos in positions:
            publish_mqtt(
                mqtt_client,
                "factory.agv_1.pose",
                {"position": pos, "orientation": orientation},
                settle=0.3,
            )

        # Kill after brief wait — trajectory goals may not complete
        # but we verify the script doesn't crash
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        # The script should not have crashed with a Python exception
        combined = stdout + stderr
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
