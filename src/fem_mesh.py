import numpy as np

def generate_mesh(width, height, nx, ny):
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