"""Tests for CLI commands."""

import os

from click.testing import CliRunner

from telos.cli.cli import cli

from .conftest import BROKER_MQTT


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


def test_validate_success(tmp_path):
    f = tmp_path / "test.telos"
    f.write_text(_valid_model())
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(f)])
    assert result.exit_code == 0
    assert "success" in result.output.lower()


def test_validate_failure(tmp_path):
    f = tmp_path / "bad.telos"
    f.write_text("this is not valid at all!!!")
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(f)])
    assert result.exit_code != 0


def test_gen_success(tmp_path):
    f = tmp_path / "test.telos"
    f.write_text(_valid_model())
    runner = CliRunner()
    result = runner.invoke(cli, ["gen", str(f)])
    # gen writes to ./gen/ or cwd
    assert result.exit_code == 0


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output
    assert "gen" in result.output


def test_validate_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    assert "MODEL_PATH" in result.output


def test_gen_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["gen", "--help"])
    assert result.exit_code == 0
    assert "MODEL_PATH" in result.output


def test_make_executable(tmp_path):
    from telos.cli.cli import make_executable

    f = tmp_path / "test.sh"
    f.write_text("#!/bin/bash\necho hello")
    make_executable(str(f))
    mode = os.stat(str(f)).st_mode
    assert mode & 0o111
