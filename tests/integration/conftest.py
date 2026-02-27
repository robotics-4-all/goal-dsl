"""Integration test fixtures: Docker lifecycle, MQTT client, temp dirs."""

import json
import socket
import subprocess
import time

import paho.mqtt.client as mqtt
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: end-to-end tests requiring Docker services")


PROJECT_ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()

COMPOSE_FILE = f"{PROJECT_ROOT}/docker-compose.test.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    """Block until a TCP port is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"{host}:{port} not reachable after {timeout}s")


def publish_mqtt(
    client: mqtt.Client,
    topic: str,
    payload: dict,
    qos: int = 1,
    settle: float = 0.3,
) -> None:
    """Publish a JSON message to an MQTT topic and wait briefly.

    The topic uses dot notation (matching Telos entity topics).
    commlib-py converts dots to slashes internally, so we do the same
    here for paho-mqtt compatibility.
    """
    mqtt_topic = topic.replace(".", "/")
    info = client.publish(mqtt_topic, json.dumps(payload), qos=qos)
    info.wait_for_publish(timeout=5)
    time.sleep(settle)


# ---------------------------------------------------------------------------
# Session-scoped: Docker services
# ---------------------------------------------------------------------------


def _port_is_open(host: str, port: int) -> bool:
    """Check if a TCP port is currently accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def broker_services():
    """Start mosquitto + redis via docker-compose, tear down at session end.

    If docker compose fails but the required ports are already reachable
    (e.g. services from another compose project), the fixture proceeds
    without owning the lifecycle.  If ports are unreachable, the test is skipped.
    """
    owns_compose = False
    result = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "--wait"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode == 0:
        owns_compose = True
    else:
        # docker compose failed — check if ports are already available
        if not (_port_is_open("localhost", 1883) and _port_is_open("localhost", 6379)):
            # Clean up partial start
            subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"],
                capture_output=True,
                timeout=60,
            )
            pytest.skip(f"docker compose failed and ports not available: {result.stderr.strip()}")

    try:
        _wait_for_port("localhost", 1883, timeout=30)
        _wait_for_port("localhost", 6379, timeout=30)
    except TimeoutError as exc:
        if owns_compose:
            subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"],
                capture_output=True,
                timeout=60,
            )
        pytest.skip(f"Broker services not ready: {exc}")

    yield

    if owns_compose:
        subprocess.run(
            ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"],
            capture_output=True,
            timeout=60,
        )


# ---------------------------------------------------------------------------
# Function-scoped: MQTT client
# ---------------------------------------------------------------------------


@pytest.fixture()
def mqtt_client(broker_services):
    """Connected paho MQTT client, cleaned up after each test."""
    client = mqtt.Client(
        client_id=f"telos-test-{time.monotonic_ns()}",
        protocol=mqtt.MQTTv311,
    )
    client.connect("localhost", 1883, keepalive=60)
    client.loop_start()
    yield client
    client.loop_stop()
    client.disconnect()


# ---------------------------------------------------------------------------
# Function-scoped: temp directory for generated code
# ---------------------------------------------------------------------------


@pytest.fixture()
def gen_dir(tmp_path):
    """Temporary directory for generated Python files."""
    d = tmp_path / "gen"
    d.mkdir()
    return d
