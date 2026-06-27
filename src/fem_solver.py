import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import splu

GAUSS_PTS = [-1/np.sqrt(3), 1/np.sqrt(3)]

def shape_functions(xi, eta):
    N = 0.25 * np.array([
        (1 - xi) * (1 - eta),
        (1 + xi) * (1 - eta),
        (1 + xi) * (1 + eta),
        (1 - xi) * (1 + eta)
    ])
    dN_dxi = 0.25 * np.array([-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)])
    dN_deta = 0.25 * np.array([-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)])
    return N, dN_dxi, dN_deta

def element_matrices(coords, k, rho_c):
    Ke = np.zeros((4, 4))
    Me = np.zeros((4, 4))

    for xi in GAUSS_PTS:
        for eta in GAUSS_PTS:
            N, dN_dxi, dN_deta = shape_functions(xi, eta)

            J = np.array([
                [np.dot(dN_dxi, coords[:, 0]), np.dot(dN_dxi, coords[:, 1])],
                [np.dot(dN_deta, coords[:, 0]), np.dot(dN_deta, coords[:, 1])]
            ])
            detJ = np.linalg.det(J)
            invJ = np.linalg.inv(J)

            dN = np.vstack((dN_dxi, dN_deta))
            dN_xy = invJ @ dN

            Ke += k * (dN_xy.T @ dN_xy) * detJ
            Me += rho_c * np.outer(N, N) * detJ

    return Ke, Me

def assemble_global(nodes, elements, k, rho_c):
    n_nodes = nodes.shape[0]
    K = lil_matrix((n_nodes, n_nodes))
    M = lil_matrix((n_nodes, n_nodes))

    for elem in elements:
        coords = nodes[elem]
        Ke, Me = element_matrices(coords, k, rho_c)
        for a in range(4):
            for b in range(4):
                K[elem[a], elem[b]] += Ke[a, b]
                M[elem[a], elem[b]] += Me[a, b]

    return K.tocsc(), M.tocsc()

def run_fem_simulation(nodes, elements, config):
    k = config.get("conductivity", 148)
    rho_c = config.get("rho_c", 1.0)
    dt = config.get("dt", 0.5)
    steps = config["iterations"]
    ambient = config["ambient_temp"]

    # Convective heat loss coefficient (how fast chip loses heat to surrounding air)
    cooling_rate = config.get("cooling_rate", 0.3)

    print("Assembling global stiffness and mass matrices...")
    K, M = assemble_global(nodes, elements, k, rho_c)

    n_nodes = nodes.shape[0]
    T = np.full(n_nodes, ambient, dtype=float)

    source_node_groups = []
    for src in config["heat_sources"]:
        x0, x1 = src["x_range"]
        y0, y1 = src["y_range"]
        mask = (
            (nodes[:, 0] >= x0) & (nodes[:, 0] <= x1) &
            (nodes[:, 1] >= y0) & (nodes[:, 1] <= y1)
        )
        ids = np.where(mask)[0]
        source_node_groups.append((ids, src["power_temp"]))
        T[ids] = src["power_temp"]

    # mask of which nodes are "free" (not fixed heat sources) — cooling applies only here
    is_source = np.zeros(n_nodes, dtype=bool)
    for ids, _ in source_node_groups:
        is_source[ids] = True
    free_mask = ~is_source

    A = (M + dt * K).tocsc()
    solver = splu(A)

    history = []
    for step in range(steps):
        b = M.dot(T)
        T_new = solver.solve(b)

        # Convective cooling: free nodes lose heat toward ambient every step
        T_new[free_mask] -= cooling_rate * (T_new[free_mask] - ambient)

        # Re-apply fixed heat source temperatures
        for ids, temp in source_node_groups:
            T_new[ids] = temp

        T = T_new
        history.append(np.max(T))

        if step % 50 == 0:
            print(f"FEM Iteration {step}/{steps} | Max Temp: {np.max(T):.2f}°C")

    print("FEM Simulation Completed.")
    return T, history