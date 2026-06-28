import numpy as np


def generate_mesh(width_mm, height_mm, nx, ny):
    """
    width_mm, height_mm: die dimensions in millimeters (as entered in GUI)
    Internally converts to meters so it matches thermal conductivity units (W/m·K).
    """
    width = width_mm / 1000.0
    height = height_mm / 1000.0

    x = np.linspace(0, width, nx + 1)
    y = np.linspace(0, height, ny + 1)
    nodes = np.array([[xi, yi] for yi in y for xi in x])

    elements = []
    for j in range(ny):
        for i in range(nx):
            n0 = j * (nx + 1) + i
            n1 = n0 + 1
            n2 = n0 + (nx + 1) + 1
            n3 = n0 + (nx + 1)
            elements.append([n0, n1, n2, n3])

    return nodes, np.array(elements)


def get_boundary_mask(nodes, width_mm, height_mm, tol=1e-9):
    """
    Returns a boolean mask marking nodes that lie on the die's outer edge
    (the only nodes physically exposed to convective air cooling).
    """
    width = width_mm / 1000.0
    height = height_mm / 1000.0
    x, y = nodes[:, 0], nodes[:, 1]
    return (
        (np.abs(x - 0.0) < tol) | (np.abs(x - width) < tol) |
        (np.abs(y - 0.0) < tol) | (np.abs(y - height) < tol)
    )