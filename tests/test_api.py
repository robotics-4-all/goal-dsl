"""Tests for REST API endpoints."""

from fastapi.testclient import TestClient

from telos.api.api import api

from .conftest import BROKER_MQTT

client = TestClient(api)
HEADERS = {"X-API-Key": "API_KEY"}


def _valid_model():
    return (
        BROKER_MQTT
        + """
Entity S1
    type: sensor
    topic: 'test'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Watch> G1
    entity: S1
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
    )


def test_validate_success():
    resp = client.post(
        "/validate",
        json={"name": "test", "model": _valid_model()},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200


def test_validate_empty_model():
    resp = client.post(
        "/validate",
        json={"name": "test", "model": ""},
        headers=HEADERS,
    )
    # Returns 404 for empty
    assert resp.json() == 404


def test_validate_invalid_model():
    resp = client.post(
        "/validate",
        json={"name": "test", "model": "not a valid model!!!"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_api_key_missing():
    resp = client.post(
        "/validate",
        json={"name": "test", "model": _valid_model()},
    )
    assert resp.status_code in (401, 403)


def test_api_key_invalid():
    resp = client.post(
        "/validate",
        json={"name": "test", "model": _valid_model()},
        headers={"X-API-Key": "WRONG_KEY"},
    )
    assert resp.status_code in (401, 403)


def test_generate_success():
    resp = client.post(
        "/generate",
        json={"name": "test", "model": _valid_model()},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/")


def test_generate_invalid_model():
    resp = client.post(
        "/generate",
        json={"name": "test", "model": "not a valid model!!!"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_validate_file_success():
    import io

    content = _valid_model().encode("utf-8")
    resp = client.post(
        "/validate/file",
        files={"file": ("test.telos", io.BytesIO(content), "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200


def test_validate_file_invalid():
    import io

    content = b"not valid at all!!!"
    resp = client.post(
        "/validate/file",
        files={"file": ("bad.telos", io.BytesIO(content), "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 404


def test_validate_base64_success():
    import base64

    encoded = base64.b64encode(_valid_model().encode("utf-8")).decode("utf-8")
    resp = client.get(
        "/validate/base64",
        params={"fenc": encoded},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 200


def test_validate_base64_empty():
    resp = client.get(
        "/validate/base64",
        params={"fenc": ""},
        headers=HEADERS,
    )
    assert resp.json() == 404


def test_validate_base64_invalid():
    import base64

    encoded = base64.b64encode(b"not valid model!!!").decode("utf-8")
    resp = client.get(
        "/validate/base64",
        params={"fenc": encoded},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 404


def test_generate_file_success():
    import io

    content = _valid_model().encode("utf-8")
    resp = client.post(
        "/generate/file",
        files={"model_file": ("test.telos", io.BytesIO(content), "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/")


def test_generate_file_invalid():
    import io

    content = b"not valid at all!!!"
    resp = client.post(
        "/generate/file",
        files={"model_file": ("bad.telos", io.BytesIO(content), "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == 404
