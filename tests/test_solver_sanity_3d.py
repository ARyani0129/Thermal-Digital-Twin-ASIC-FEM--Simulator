"""
Sanity / regression tests for the 3D transient FEM thermal solver
(layered stack: die -> TIM -> heat spreader), run against the actual
repo's fem_mesh_3d.py / fem_solver_3d.py.
"""
import numpy as np
import pytest

from fem_mesh_3d import generate_layered_mesh, get_top_surface_mask, get_bottom_surface_mask
from fem_solver_3d import run_fem_simulation_3d


DEFAULT_LAYERS = [
    {"name": "Silicon_Die", "thickness_mm": 0.5, "conductivity": 150.0, "rho_c": 1.66e6},
    {"name": "TIM", "thickness_mm": 0.1, "conductivity": 5.0, "rho_c": 2.0e6},
    {"name": "Copper_Spreader", "thickness_mm": 1.0, "conductivity": 385.0, "rho_c": 3.45e6},
]


def build_mesh(width_mm=12.0, height_mm=12.0, layers=None, nx=9, ny=9):
    layers = layers or DEFAULT_LAYERS
    return generate_layered_mesh(width_mm, height_mm, layers, nx, ny)


def make_config(ambient=25.0, dt=0.05, iterations=40, cooling_rate=0.3, heat_sources=None):
    return {"ambient_temp": ambient, "dt": dt, "iterations": iterations,
            "cooling_rate": cooling_rate, "heat_sources": heat_sources or []}


def test_mesh_node_and_element_counts():
    nx, ny = 9, 9
    nodes, elements, element_material, layer_info = build_mesh(nx=nx, ny=ny)
    expected_nodes = nx * ny * (len(DEFAULT_LAYERS) + 1)
    expected_elements = (nx - 1) * (ny - 1) * len(DEFAULT_LAYERS)
    assert nodes.shape == (expected_nodes, 3)
    assert elements.shape == (expected_elements, 8)
    assert len(element_material) == expected_elements
    assert set(np.unique(element_material)).issubset(set(range(len(DEFAULT_LAYERS))))


def test_no_heat_sources_stays_near_ambient():
    nodes, elements, element_material, layers = build_mesh()
    config = make_config(heat_sources=[])
    T, history = run_fem_simulation_3d(nodes, elements, element_material, layers, config)
    assert abs(np.max(T) - config["ambient_temp"]) < 1.0
    assert abs(np.min(T) - config["ambient_temp"]) < 1.0


def test_heat_source_raises_temperature_above_ambient():
    nodes, elements, element_material, layers = build_mesh()
    heat_sources = [{"name": "Core", "x_range": [4.0, 8.0], "y_range": [4.0, 8.0], "power_temp": 15.0}]
    config = make_config(heat_sources=heat_sources)
    T, history = run_fem_simulation_3d(nodes, elements, element_material, layers, config)
    assert np.max(T) > config["ambient_temp"]


def test_higher_power_gives_higher_temperature():
    def run_with_power(power_watts):
        nodes, elements, element_material, layers = build_mesh()
        heat_sources = [{"name": "Core", "x_range": [4.0, 8.0], "y_range": [4.0, 8.0], "power_temp": power_watts}]
        config = make_config(heat_sources=heat_sources)
        T, _ = run_fem_simulation_3d(nodes, elements, element_material, layers, config)
        return np.max(T)
    assert run_with_power(20.0) > run_with_power(5.0)


def test_hotspot_is_on_die_face_not_spreader_face():
    nodes, elements, element_material, layers = build_mesh()
    heat_sources = [{"name": "Core", "x_range": [4.0, 8.0], "y_range": [4.0, 8.0], "power_temp": 20.0}]
    config = make_config(heat_sources=heat_sources, iterations=60)
    T, _ = run_fem_simulation_3d(nodes, elements, element_material, layers, config)
    bottom_mask = get_bottom_surface_mask(nodes)
    z_max = nodes[:, 2].max()
    top_mask = get_top_surface_mask(nodes, z_max)
    hottest_idx = np.argmax(T)
    assert bottom_mask[hottest_idx] or not top_mask[hottest_idx]
    assert T[bottom_mask].mean() > T[top_mask].mean()


def test_hotspot_location_matches_source_xy_region():
    nodes, elements, element_material, layers = build_mesh()
    heat_sources = [{"name": "CornerCore", "x_range": [8.0, 10.5], "y_range": [8.0, 10.5], "power_temp": 25.0}]
    config = make_config(heat_sources=heat_sources, iterations=60)
    T, _ = run_fem_simulation_3d(nodes, elements, element_material, layers, config)
    bottom_mask = get_bottom_surface_mask(nodes)
    bottom_T = np.where(bottom_mask, T, -np.inf)
    hottest_idx = np.argmax(bottom_T)
    hx, hy, _ = nodes[hottest_idx]
    hx_mm, hy_mm = hx * 1000.0, hy * 1000.0
    assert 7.0 <= hx_mm <= 11.5 and 7.0 <= hy_mm <= 11.5


def test_more_layers_increase_node_count_predictably():
    nx, ny = 7, 7
    two_layer = DEFAULT_LAYERS[:2]
    three_layer = DEFAULT_LAYERS
    nodes2, elems2, _, _ = build_mesh(layers=two_layer, nx=nx, ny=ny)
    nodes3, elems3, _, _ = build_mesh(layers=three_layer, nx=nx, ny=ny)
    assert nodes3.shape[0] - nodes2.shape[0] == nx * ny
    assert elems3.shape[0] - elems2.shape[0] == (nx - 1) * (ny - 1)


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
