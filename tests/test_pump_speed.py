"""Tests for Aquascape pump speed conversion."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_const_module():
    path = (
        Path(__file__).parents[1]
        / "custom_components"
        / "aquascape"
        / "const.py"
    )
    spec = spec_from_file_location("aquascape_const", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_percentage_to_speed_uses_ten_steps() -> None:
    const = _load_const_module()
    assert const.pump_percentage_to_speed(1) == 1
    assert const.pump_percentage_to_speed(10) == 1
    assert const.pump_percentage_to_speed(50) == 5
    assert const.pump_percentage_to_speed(25) == 3
    assert const.pump_percentage_to_speed(100) == 10


def test_percentage_to_speed_clamps_values() -> None:
    const = _load_const_module()
    assert const.pump_percentage_to_speed(-20) == 1
    assert const.pump_percentage_to_speed(250) == 10


def test_speed_to_percentage_uses_ten_percent_increments() -> None:
    const = _load_const_module()
    assert const.pump_speed_to_percentage(1) == 10
    assert const.pump_speed_to_percentage(5) == 50
    assert const.pump_speed_to_percentage(10) == 100
