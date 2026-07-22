import numpy as np

def generate_layered_mesh(width_mm, height_mm, layers, nx, ny):
    width_m = width_mm / 1000.0
    height_m = height_mm / 1000.0
    x = np.linspace(0, width_m, nx)
    y = np.linspace(0, height_m, ny)
    z_levels = [0.0]
    for layer in layers:
        z_levels.append(z_levels[-1] + layer["thickness_mm"] / 1000.0)
    z_levels = np.array(z_levels)
    nodes = []
    node_index = {}
    idx = 0
    for zi, z in enumerate(z_levels):
        for yi, yy in enumerate(y):
            for xi, xx in enumerate(x):
                nodes.append([xx, yy, z])
                node_index[(xi, yi, zi)] = idx
                idx += 1
    nodes = np.array(nodes)
    elements = []
    element_material = []
    for layer_i, layer in enumerate(layers):
        z0, z1 = layer_i, layer_i + 1
        for yi in range(ny - 1):
            for xi in range(nx - 1):
                n0 = node_index[(xi, yi, z0)]
                n1 = node_index[(xi + 1, yi, z0)]
                n2 = node_index[(xi + 1, yi + 1, z0)]
                n3 = node_index[(xi, yi + 1, z0)]
                n4 = node_index[(xi, yi, z1)]
                n5 = node_index[(xi + 1, yi, z1)]
                n6 = node_index[(xi + 1, yi + 1, z1)]
                n7 = node_index[(xi, yi + 1, z1)]
                elements.append([n0, n1, n2, n3, n4, n5, n6, n7])
                element_material.append(layer_i)
    return nodes, np.array(elements), np.array(element_material), layers

def get_top_surface_mask(nodes, z_levels_max):
    return np.isclose(nodes[:, 2], z_levels_max)

def get_bottom_surface_mask(nodes):
    return np.isclose(nodes[:, 2], 0.0)