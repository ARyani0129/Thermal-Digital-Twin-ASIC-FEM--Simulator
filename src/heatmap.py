import numpy as np

def reshape_to_grid(T_flat, nx, ny):
    return T_flat.reshape((ny + 1, nx + 1))