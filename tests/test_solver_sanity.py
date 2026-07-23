"""
Sanity / regression tests for the FEM thermal solver.

These are NOT full analytical validation against a closed-form solution --
that requires the solver's units and boundary conditions to be tightened
up first (see assessment doc, Section 6). What these tests DO catch:
physically impossible behavior, like the bug found on 2026-07-21 where
heat sources were clamped to their wattage value as a fixed temperature,
making them act as cooling sinks instead of heat sources.

Run with: pytest test_solver_sanity.py -v
"""
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
    """With zero heat sources, the chip should NOT heat up or cool
    below ambient in any meaningful way -- it should stay at ambient."""
    config = make_config(heat_sources=[])
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
    T, history = run_fem_simulation(nodes, elements, config)

    assert abs(np.max(T) - config["ambient_temp"]) < 1.0, (
        f"With no heat sources, max temp drifted to {np.max(T):.2f} C "
        f"from ambient {config['ambient_temp']} C -- solver has a leak/sink bug."
    )


def test_heat_source_raises_temperature_above_ambient():
    """This is the exact case that was broken: a single heat source
    MUST push max temperature above ambient, not below it."""
    heat_sources = [{
        "name": "TestBlock",
        "x_range": [4.0, 8.0],
        "y_range": [4.0, 8.0],
        "power_temp": 15.0,  # Watts
    }]
    config = make_config(heat_sources=heat_sources)
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
    T, history = run_fem_simulation(nodes, elements, config)

    assert np.max(T) > config["ambient_temp"], (
        f"Heat source did not raise temperature above ambient "
        f"({np.max(T):.2f} C vs ambient {config['ambient_temp']} C). "
        f"This is the exact bug pattern found on 2026-07-21 -- "
        f"check if power_temp is being used as a source term or a clamp."
    )


def test_higher_power_gives_higher_temperature():
    """Monotonicity check: doubling the power of the same source, in the
    same location, must not produce a lower peak temperature."""
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
        f"than a 5W source ({low_power_temp:.2f} C) at the same location. "
        f"Power-to-temperature relationship is inverted or broken."
    )


def test_hotspot_location_matches_source_location():
    """The reported max-temp node should fall within (or very near) the
    heat source's spatial region, not somewhere unrelated on the die."""
    heat_sources = [{
        "name": "CornerBlock",
        "x_range": [9.0, 11.0],
        "y_range": [9.0, 11.0],
        "power_temp": 25.0,
    }]
    config = make_config(heat_sources=heat_sources)
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
    T, _ = run_fem_simulation(nodes, elements, config)

    hottest_node_idx = np.argmax(T)
    hx, hy = nodes[hottest_node_idx]
    hx_mm, hy_mm = hx * 1000.0, hy * 1000.0  # nodes are in meters, source region is in mm

    assert 8.0 <= hx_mm <= 12.0 and 8.0 <= hy_mm <= 12.0, (
        f"Hottest node at ({hx_mm:.2f}, {hy_mm:.2f}) mm is not near the heat "
        f"source region [9-11, 9-11] mm. Source may be misplaced or mesh "
        f"coordinate mapping may be wrong."
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
