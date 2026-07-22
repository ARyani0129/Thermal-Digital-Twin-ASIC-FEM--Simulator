import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import splu
from fem_mesh_3d import get_top_surface_mask, get_bottom_surface_mask

GAUSS_PTS = [-1 / np.sqrt(3), 1 / np.sqrt(3)]
HEX_LOCAL_COORDS = np.array([
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],
])

def trilinear_shape_functions(xi, eta, zeta):
    N = np.zeros(8)
    dN_dxi = np.zeros(8)
    dN_deta = np.zeros(8)
    dN_dzeta = np.zeros(8)
    for i, (xi_i, eta_i, zeta_i) in enumerate(HEX_LOCAL_COORDS):
        N[i] = 0.125 * (1 + xi * xi_i) * (1 + eta * eta_i) * (1 + zeta * zeta_i)
        dN_dxi[i] = 0.125 * xi_i * (1 + eta * eta_i) * (1 + zeta * zeta_i)
        dN_deta[i] = 0.125 * eta_i * (1 + xi * xi_i) * (1 + zeta * zeta_i)
        dN_dzeta[i] = 0.125 * zeta_i * (1 + xi * xi_i) * (1 + eta * eta_i)
    return N, dN_dxi, dN_deta, dN_dzeta

def element_matrices_3d(coords, k, rho_c):
    Ke = np.zeros((8, 8))
    Me = np.zeros((8, 8))
    for xi in GAUSS_PTS:
        for eta in GAUSS_PTS:
            for zeta in GAUSS_PTS:
                N, dN_dxi, dN_deta, dN_dzeta = trilinear_shape_functions(xi, eta, zeta)
                dN_local = np.vstack((dN_dxi, dN_deta, dN_dzeta))
                J = dN_local @ coords
                detJ = np.linalg.det(J)
                if detJ <= 0:
                    raise ValueError("Non-positive Jacobian determinant.")
                invJ = np.linalg.inv(J)
                dN_xyz = invJ @ dN_local
                Ke += k * (dN_xyz.T @ dN_xyz) * detJ
                Me += rho_c * np.outer(N, N) * detJ
    return Ke, Me

def assemble_global_3d(nodes, elements, element_material, materials):
    n_nodes = nodes.shape[0]
    K = lil_matrix((n_nodes, n_nodes))
    M = lil_matrix((n_nodes, n_nodes))
    for e_idx, elem in enumerate(elements):
        coords = nodes[elem]
        mat = materials[element_material[e_idx]]
        Ke, Me = element_matrices_3d(coords, mat["conductivity"], mat["rho_c"])
        for a in range(8):
            for b in range(8):
                K[elem[a], elem[b]] += Ke[a, b]
                M[elem[a], elem[b]] += Me[a, b]
    return K.tocsc(), M.tocsc()

def run_fem_simulation_3d(nodes, elements, element_material, layers, config):
    ambient = config["ambient_temp"]
    dt = config.get("dt", 0.1)
    steps = config["iterations"]
    cooling_rate = config.get("cooling_rate", 0.3)
    
    K, M = assemble_global_3d(nodes, elements, element_material, layers)
    n_nodes = nodes.shape[0]
    T = np.full(n_nodes, ambient, dtype=float)
    
    bottom_mask = get_bottom_surface_mask(nodes)
    Q = np.zeros(n_nodes)
    for src in config["heat_sources"]:
        x0, x1 = src["x_range"][0] / 1000.0, src["x_range"][1] / 1000.0
        y0, y1 = src["y_range"][0] / 1000.0, src["y_range"][1] / 1000.0
        region_mask = (
            bottom_mask &
            (nodes[:, 0] >= x0) & (nodes[:, 0] <= x1) &
            (nodes[:, 1] >= y0) & (nodes[:, 1] <= y1)
        )
        ids = np.where(region_mask)[0]
        if len(ids) > 0:
            Q[ids] += src["power_temp"] / len(ids)
            
    z_max = nodes[:, 2].max()
    top_mask = get_top_surface_mask(nodes, z_max)
    A = (M + dt * K).tocsc()
    solver = splu(A)
    
    history = []
    for step in range(steps):
        b = M.dot(T) + dt * Q
        T_new = solver.solve(b)
        T_new[top_mask] -= cooling_rate * (T_new[top_mask] - ambient)
        T = T_new
        history.append(np.max(T))
    return T, history