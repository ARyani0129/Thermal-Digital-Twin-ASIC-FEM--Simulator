import argparse
import sys
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from layout_loader import LayoutLoader
from fem_mesh import generate_mesh
from fem_solver import run_fem_simulation
from hotspot import detect_hotspots
from heatmap import reshape_to_grid
from report_generator import generate_pdf_report


def main():
    parser = argparse.ArgumentParser(
        description="Thermal Digital Twin ASIC FEM Simulator — Command Line Interface"
    )
    parser.add_argument("--layout", type=str, required=True,
                        help="Path to layout file (.json)")
    parser.add_argument("--output", type=str, default="thermal_report.pdf",
                        help="Output PDF report path")
    parser.add_argument("--nx", type=int, default=40, help="Mesh nodes in X (default 40)")
    parser.add_argument("--ny", type=int, default=40, help="Mesh nodes in Y (default 40)")
    parser.add_argument("--ambient-temp", type=float, default=25.0, help="Ambient temp in C")
    parser.add_argument("--iterations", type=int, default=100, help="Solver iterations")
    parser.add_argument("--material", type=str, default="Silicon", help="Chip material")
    parser.add_argument("--threshold", type=float, default=80.0, help="Hotspot threshold (C)")

    args = parser.parse_args()

    if not os.path.exists(args.layout):
        print(f"[ERROR] Layout file not found: {args.layout}")
        sys.exit(1)

    print("=" * 60)
    print("   ASIC FEM THERMAL SIMULATOR - CLI")
    print("=" * 60)

    # 1. Load layout
    layout_data = LayoutLoader.load_layout(args.layout)
    width, height = layout_data["chip_size"]
    heat_sources = layout_data["heat_sources"]
    print(f"[OK] Layout loaded: {width}mm x {height}mm, {len(heat_sources)} heat sources")

    # 2. Build config dict (same shape gui_app.py builds)
    config = {
        "width": width,
        "height": height,
        "nx": args.nx,
        "ny": args.ny,
        "ambient_temp": args.ambient_temp,
        "iterations": args.iterations,
        "material": args.material,
        "heat_sources": heat_sources,
    }

    # 3. Mesh
    print("[*] Generating mesh...")
    nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])

    # 4. Solve
    print("[*] Running FEM simulation...")
    T, history = run_fem_simulation(nodes, elements, config)

    # 5. Hotspots
    report = detect_hotspots(T, threshold=args.threshold)
    print(f"[OK] Max Temp: {report['max_temp']:.2f} C")

    # 6. Heatmap image
    print("[*] Rendering heatmap...")
    grid = reshape_to_grid(T, config["nx"], config["ny"])
    fig, ax = plt.subplots()
    x = np.linspace(0, config["width"], grid.shape[1])
    y = np.linspace(0, config["height"], grid.shape[0])
    contour = ax.contourf(x, y, grid, levels=40, cmap="turbo")
    fig.colorbar(contour, ax=ax, label="Temperature (C)")
    ax.set_title(f"FEM Thermal Distribution - {config['material']}")
    ax.set_xlabel("Width (mm)")
    ax.set_ylabel("Height (mm)")

    heatmap_path = os.path.join(os.path.dirname(os.path.abspath(args.output)) or ".", "cli_heatmap.png")
    fig.savefig(heatmap_path, dpi=150)
    plt.close(fig)

    # History (convergence) line graph
    print("[*] Rendering convergence history...")
    fig2, ax2 = plt.subplots()
    ax2.plot(history, color="#f38ba8", linewidth=2)
    ax2.set_xlabel("Time Step")
    ax2.set_ylabel("Max Temp (C)")
    ax2.set_title("Peak Temperature Over Time")
    ax2.grid(True, linestyle="--", linewidth=0.5)

    history_path = os.path.join(os.path.dirname(os.path.abspath(args.output)) or ".", "cli_history.png")
    fig2.savefig(history_path, dpi=150)
    plt.close(fig2)

    # 7. PDF report
    print(f"[*] Generating PDF report -> {args.output}")
    path = generate_pdf_report(
        report, config["material"], config,
        heatmap_path, history_image_path=history_path,
        save_path=args.output
    )
    print(f"[SUCCESS] Report saved: {path}")


if __name__ == "__main__":
    main()