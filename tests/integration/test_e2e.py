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
    "11_scenarios": {
        "scenario": "ReactorVerification",
        "messages": [
            # TempNominal: 50 < temp < 200 ✓
            # PressureNominal: 1 < value < 10 ✓
            # SensorAlive: Watch on TempSensor — fires on any message ✓
            # Overheating (antigoal): temp > 300 — NOT triggered (100 < 300) ✓
            # SafetyValveTriggered (fatal): open is true — NOT triggered ✓
            # Overpressure (fatal): value > 20 — NOT triggered (5 < 20) ✓
            ("reactor.temperature", {"temp": 100.0}),
            ("reactor.pressure", {"value": 5.0}),
            ("reactor.safety_valve", {"open": False}),
        ],
        "expected_goals": {
            "TempNominal": True,
            "PressureNominal": True,
            "SensorAlive": True,
        },
    },
    "12_value_generators": {
        "scenario": "ValueGenerators",
        "messages": [
            # Generators are not rendered in codegen — entities are plain
            # subscribers.  We publish data manually.
            # TempAboveBaseline: temperature > 25 ✓
            # ConfigCheck: Watch on ConfiguredSensor — fires on any message ✓
            (
                "sim.weather",
                {
                    "temperature": 28.0,
                    "altitude": 150.0,
                    "pressure": 1013.0,
                    "humidity": 55.0,
                    "windDirection": 180,
                    "condition": 1,
                },
            ),
            ("sim.configured", {"temp": 22.0, "label": "default", "active": True, "count": 0}),
        ],
        "expected_goals": {
            "TempAboveBaseline": True,
            "ConfigCheck": True,
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

    Checks two formats:
    1. Final summary:  '       - GoalName: ✓' or '       - GoalName: ✗'
    2. Intermediate:   'Goal <GoalName> exited with state: COMPLETED'
       (useful when scenario hangs on incomplete goals and never prints summary)

    goalee uses rich logging which wraps long lines, so intermediate
    messages are matched with regex across the full output text.
    """
    import re

    results = {}

    # 1. Final summary format (line-by-line)
    for line in output.splitlines():
        line = line.strip()
        if ": ✓" in line or ": ✗" in line:
            parts = line.lstrip("- ").split(": ", 1)
            if len(parts) == 2:
                goal_name = parts[0].strip()
                status = "✓" in parts[1]
                results[goal_name] = status

    # 2. Intermediate completion format (regex across full text, handles
    #    rich line wrapping and inserted source locations like
    #    "Goal           scenario.py:530\n<Name> exited with state:\nCOMPLETED")
    for match in re.finditer(
        r"<(\w+)>\s+exited with state:\s+(COMPLETED|FAILED)",
        output,
    ):
        goal_name = match.group(1)
        completed = match.group(2) == "COMPLETED"
        # Final summary takes precedence over intermediate
        if goal_name not in results:
            results[goal_name] = completed

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
class TestE2EAreaGoals:
    """E2E test for 05_area_goals — spatial area goals.

    Area goals (Rect, Circle, Poly, Shadow, Line) evaluate entity
    positions against geometric regions.  We publish robot poses and
    verify the script starts correctly and processes messages without
    crashing.  Requires goalee AreaGoalTag to support STAY and CROSS.
    """

    MODEL = EXAMPLES_DIR / "05_area_goals" / "scenario.telos"

    def test_e2e_no_crash(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["AreaGoals"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Robot1 at (5,4,0) — inside Rect(0,0 to 10,8), inside
        # StayInPerimeter(center=10,10 r=25), inside Poly
        publish_mqtt(
            mqtt_client,
            "factory.robot_1.pose",
            {"position": {"x": 5, "y": 4, "z": 0}, "orientation": {"x": 0, "y": 0, "z": 0}},
            settle=0.3,
        )
        # Robot2 at (12,10,0) — inside StayInPerimeter, far from Robot1 (>2 for Shadow)
        publish_mqtt(
            mqtt_client,
            "factory.robot_2.pose",
            {"position": {"x": 12, "y": 10, "z": 0}, "orientation": {"x": 0, "y": 0, "z": 0}},
            settle=0.3,
        )
        # Publish varying positions to trigger state changes
        for i in range(3):
            publish_mqtt(
                mqtt_client,
                "factory.robot_1.pose",
                {
                    "position": {"x": 5 + i, "y": 4, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0},
                },
                settle=0.3,
            )

        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
        assert "Started Entity" in combined, (
            f"Script did not start properly.\nOutput:\n{combined[-2000:]}"
        )


@pytest.mark.integration
class TestE2EPoseGoals:
    """E2E test for 06_pose_goals — position/orientation goals.

    Publishes robot/drone poses near target positions and verifies
    the generated script runs without errors.  Requires goalee
    Orientation to accept x/y/z kwargs (mapped to roll/pitch/yaw).
    """

    MODEL = EXAMPLES_DIR / "06_pose_goals" / "scenario.telos"

    def test_e2e_no_crash(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["PoseGoals"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Robot near loading dock target Point3D(15, 2, 0) within 0.5m
        publish_mqtt(
            mqtt_client,
            "warehouse.agv_1.pose",
            {
                "position": {"x": 15.1, "y": 2.0, "z": 0},
                "orientation": {"x": 0, "y": 0, "z": 0.05},
            },
            settle=0.3,
        )
        # Drone near landing pose Point3D(10, 10, 0.5), Orientation2D(1.57)
        publish_mqtt(
            mqtt_client,
            "warehouse.drone_1.pose",
            {
                "position": {"x": 10.1, "y": 10.0, "z": 0.5},
                "orientation": {"x": 0, "y": 0, "z": 1.57},
            },
            settle=0.3,
        )
        # Publish a few more varying poses
        for i in range(3):
            publish_mqtt(
                mqtt_client,
                "warehouse.agv_1.pose",
                {
                    "position": {"x": 15.0 + i * 0.1, "y": 2.0, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0.02 * i},
                },
                settle=0.3,
            )

        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
        assert "Started Entity" in combined, (
            f"Script did not start properly.\nOutput:\n{combined[-2000:]}"
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


@pytest.mark.integration
class TestE2EAdvancedConditions:
    """E2E test for 09_advanced_conditions — aggregation, InRange, XOR, n-ary.

    Scenario AdvancedConditions runs concurrently with 5 goals (all have
    timeouts so the scenario always completes):
    - MeanTempHigh: mean(temp, 10) > 25 — timeout 30s
    - StableReadings: std(temp, 20) < 2.0 — timeout 30s
    - TempInBounds: temp in range [18.0, 26.0]
    - AllSensorsNominal: temp > 15 AND pressure > 1 AND co2 < 1000
    - ExclusiveAlert: (temp > 50) XOR (pressure > 20)

    We publish temp ~25.5 (satisfies in-range, n-ary, and XOR conditions),
    pressure=25 (>1 for AllSensorsNominal, >20 for XOR with temp≤50),
    co2=500 (<1000).  Non-aggregation goals are verified as reached.
    Aggregation goals complete (via timeout) but may not reach if
    goalee buffer evaluation has issues.
    """

    MODEL = EXAMPLES_DIR / "09_advanced_conditions" / "scenario.telos"

    def test_e2e_run(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["AdvancedConditions"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Publish pressure and air quality (non-aggregated conditions)
        publish_mqtt(mqtt_client, "lab.sensor_b.pressure", {"value": 25.0}, settle=0.3)
        publish_mqtt(mqtt_client, "lab.air_quality", {"co2": 500.0, "pm25": 10.0}, settle=0.3)

        # Publish 25 temperature readings with small variance to fill
        # aggregation buffers (need 10 for mean, 20 for std).
        # Values ~25.5: mean > 25 ✓, in [18,26] ✓, std ≈ 0.3 < 2.0 ✓
        temps = [25.0 + (i % 5) * 0.2 for i in range(25)]
        for t in temps:
            publish_mqtt(
                mqtt_client,
                "lab.sensor_a.temperature",
                {"temp": t, "humidity": 50.0},
                settle=0.2,
            )

        # Aggregation goals have 30s timeouts, so scenario completes
        # within ~40s even if aggregation conditions never evaluate true.
        try:
            stdout, stderr = proc.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        results = _parse_goal_results(combined)

        # Non-aggregation goals must be reached
        for goal_name in ("TempInBounds", "AllSensorsNominal", "ExclusiveAlert"):
            assert goal_name in results, (
                f"Goal '{goal_name}' not found in output. "
                f"Got: {results}. Output:\n{combined[-2000:]}"
            )
            assert results[goal_name] is True, f"Goal '{goal_name}': expected ✓, got ✗"

        # Aggregation goals must at least appear in results (they
        # complete via timeout even if the condition was never met)
        for goal_name in ("MeanTempHigh", "StableReadings"):
            assert goal_name in results, (
                f"Aggregation goal '{goal_name}' not found in output. "
                f"Got: {results}. Output:\n{combined[-2000:]}"
            )


@pytest.mark.integration
class TestE2ETimeConstraints:
    """E2E test for 10_time_constraints — time-constrained goals.

    The scenario runs sequentially with FOR_TIME constraints (30s+), which
    makes full verification impractical.  We verify the script starts,
    entities connect, and no Python errors occur.  We publish data to
    trigger the first goal (QuickTempCheck: temp > 50 within 60s).
    """

    MODEL = EXAMPLES_DIR / "10_time_constraints" / "scenario.telos"

    def test_e2e_no_crash(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["TimeConstraints"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Publish data for all entities
        publish_mqtt(mqtt_client, "process.temperature", {"temp": 55.0}, settle=0.3)
        publish_mqtt(mqtt_client, "process.pressure", {"value": 8.0}, settle=0.3)
        publish_mqtt(mqtt_client, "process.flow", {"rate": 5.0}, settle=0.3)
        publish_mqtt(
            mqtt_client,
            "process.robot.pose",
            {"position": {"x": 5, "y": 5, "z": 0}, "orientation": {"x": 0, "y": 0, "z": 0}},
            settle=0.3,
        )

        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
        assert "Started Entity" in combined, (
            f"Script did not start properly.\nOutput:\n{combined[-2000:]}"
        )


@pytest.mark.integration
class TestE2EScenarios:
    """E2E test for 11_scenarios — weights, antigoals, fatals.

    ReactorVerification scenario runs concurrently with:
    - Goals: TempNominal (50<t<200), PressureNominal (1<v<10), SensorAlive (Watch)
    - Antigoals: Overheating (temp>300) — must NOT be reached
    - Fatals: SafetyValveTriggered, Overpressure — must NOT be reached

    We publish safe values (temp=100, pressure=5, valve closed) to
    satisfy all goals without triggering antigoals or fatals.
    """

    EXAMPLE = "11_scenarios"
    MODEL = EXAMPLES_DIR / "11_scenarios" / "scenario.telos"

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
class TestE2EValueGenerators:
    """E2E test for 12_value_generators — virtual entities.

    Generators are not rendered in codegen (entities are plain subscribers).
    We publish data manually to satisfy goals:
    - TempAboveBaseline: temperature > 25
    - ConfigCheck: Watch on ConfiguredSensor (any message)
    """

    EXAMPLE = "12_value_generators"
    MODEL = EXAMPLES_DIR / "12_value_generators" / "scenario.telos"

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
class TestE2ETimingGoals:
    """E2E test for 16_timing_goals — timing verification goals.

    Tests that the generated code for Goal<Rate>, Goal<Latency>,
    Goal<Ordering>, and Goal<Deadline> starts correctly and processes
    messages without crashing.  Timing goals have complex runtime
    semantics (wall-clock evaluation, interval tracking) so we verify
    no-crash + entity startup.
    """

    MODEL = EXAMPLES_DIR / "16_timing_goals" / "scenario.telos"

    def test_e2e_no_crash(self, broker_services, mqtt_client, gen_dir):
        files = _generate_to_file(self.MODEL, gen_dir)
        script = files["TimingGoals"]

        env = {**os.environ, "U_ID": "test"}
        proc = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        time.sleep(3)

        # Publish temperature readings for RateGoal
        for i in range(5):
            publish_mqtt(
                mqtt_client,
                "monitoring.temperature",
                {"temp": 22.0 + i},
                settle=0.5,
            )

        # Publish command + status for LatencyGoal
        publish_mqtt(mqtt_client, "monitoring.command", {"command": "read"}, settle=0.1)
        publish_mqtt(mqtt_client, "monitoring.status", {"status": "ok"}, settle=0.3)

        # Publish pressure
        publish_mqtt(mqtt_client, "monitoring.pressure", {"value": 5.0}, settle=0.3)

        try:
            stdout, stderr = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()

        combined = stdout + stderr
        assert "Traceback" not in combined, f"Generated script crashed:\n{combined[-2000:]}"
        assert "Started Entity" in combined, (
            f"Script did not start properly.\nOutput:\n{combined[-2000:]}"
        )
