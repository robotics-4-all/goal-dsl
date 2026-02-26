"""Tests for utils and plantuml modules."""

import os


def test_gen_timestamp():
    from goal_dsl.utils import gen_timestamp

    ts = gen_timestamp()
    assert isinstance(ts, int)
    assert ts > 0


def test_gen_timestamp_unique():
    from goal_dsl.utils import gen_timestamp

    t1 = gen_timestamp()
    t2 = gen_timestamp()
    assert t1 != t2


def test_plantuml_generate_diagram(tmp_path, minimal_model):
    from goal_dsl.transformations.model_2_plantuml import generate_diagram

    model_file = tmp_path / "test.goal"
    model_file.write_text(minimal_model)
    orig_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        generate_diagram(str(model_file))
        generated = list(tmp_path.glob("*.puml"))
        assert len(generated) >= 1
        content = generated[0].read_text()
        assert len(content) > 0
    finally:
        os.chdir(orig_cwd)
