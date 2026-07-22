import sys
import os
import numpy as np
import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from fem_mesh import generate_mesh
from fem_solver import run_fem_simulation


def make_config(width=12.0, height=12.0, nx=15, ny=15, ambient=25.0,
                 iterations=60, heat_sources=None):
    return {
        "width": width,
        "height": height,
        "nx": nx,
        "ny": ny,
        "ambient_temp": ambient,
        "iterations": iterations,
        "material": "Silicon",
        "heat_sources": heat_sources or [],
    }


def test_no_heat_sources_stays_near_ambient():
    config = make_config(heat_sources=[])
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
    T, history = run_fem_simulation(nodes, elements, config)

    assert abs(np.max(T) - config["ambient_temp"]) < 1.0, (
        f"With no heat sources, max temp drifted to {np.max(T):.2f} C "
        f"from ambient {config['ambient_temp']} C"
    )


def test_heat_source_raises_temperature_above_ambient():
    heat_sources = [{
        "name": "TestBlock",
        "x_range": [4.0, 8.0],
        "y_range": [4.0, 8.0],
        "power_temp": 15.0,
    }]
    config = make_config(heat_sources=heat_sources)
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
    T, history = run_fem_simulation(nodes, elements, config)

    assert np.max(T) > config["ambient_temp"], (
        f"Heat source did not raise temperature above ambient "
        f"({np.max(T):.2f} C vs ambient {config['ambient_temp']} C)."
    )


def test_higher_power_gives_higher_temperature():
    def run_with_power(power_watts):
        heat_sources = [{
            "name": "TestBlock",
            "x_range": [4.0, 8.0],
            "y_range": [4.0, 8.0],
            "power_temp": power_watts,
        }]
        config = make_config(heat_sources=heat_sources)
        nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
        T, _ = run_fem_simulation(nodes, elements, config)
        return np.max(T)

    low_power_temp = run_with_power(5.0)
    high_power_temp = run_with_power(20.0)

    assert high_power_temp > low_power_temp, (
        f"20W source produced a LOWER peak temp ({high_power_temp:.2f} C) "
        f"than a 5W source ({low_power_temp:.2f} C)."
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))