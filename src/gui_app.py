import sys
import os
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
matplotlib.rcParams['axes.facecolor'] = '#1e1e2e'
matplotlib.rcParams['figure.facecolor'] = '#1e1e2e'
matplotlib.rcParams['text.color'] = 'white'
matplotlib.rcParams['axes.labelcolor'] = 'white'
matplotlib.rcParams['xtick.color'] = 'white'
matplotlib.rcParams['ytick.color'] = 'white'
matplotlib.rcParams['axes.edgecolor'] = 'white'

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox, QScrollArea,
    QGridLayout, QComboBox
)
from PySide6.QtGui import QIcon

from fem_mesh import generate_mesh
from fem_solver import run_fem_simulation
from hotspot import detect_hotspots
from heatmap import reshape_to_grid
from report_generator import generate_pdf_report

MATERIALS = {
    "Silicon": 148,
    "Copper": 401,
    "Aluminum": 237,
    "Diamond": 2200
}


def resource_path(relative_path):
    """ Get absolute path to bundled resource (works in dev AND in .exe) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")
    return os.path.join(base_path, relative_path)


def get_output_dir():
    """ Output folder next to the .exe (or next to script when running in dev) """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath("..")
    output_dir = os.path.join(base_path, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #181825;
    color: #f0f0f0;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 10px;
    font-weight: bold;
    color: #89b4fa;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QComboBox {
    background-color: #313244;
    color: #f0f0f0;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 4px;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 6px;
    padding: 10px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #74c7ec;
}
QLabel {
    color: #f0f0f0;
}
"""


class ThermalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Digital Twin — ASIC FEM Simulator")
        self.setGeometry(100, 100, 1350, 780)
        self.setStyleSheet(DARK_STYLESHEET)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_panel = QWidget()
        left_panel.setFixedWidth(320)
        left_layout = QVBoxLayout(left_panel)

        header = QLabel("MAH QUANTUM\nThermal Digital Twin")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa; padding: 8px;")
        left_layout.addWidget(header)

        config_box = QGroupBox("Chip Configuration")
        form = QFormLayout()

        self.width_input = QLineEdit("20.0")
        self.height_input = QLineEdit("20.0")
        self.nx_input = QLineEdit("40")
        self.ny_input = QLineEdit("40")
        self.ambient_input = QLineEdit("25.0")
        self.iterations_input = QLineEdit("100")

        self.material_dropdown = QComboBox()
        self.material_dropdown.addItems(list(MATERIALS.keys()))

        form.addRow("Width (mm):", self.width_input)
        form.addRow("Height (mm):", self.height_input)
        form.addRow("Mesh Nx:", self.nx_input)
        form.addRow("Mesh Ny:", self.ny_input)
        form.addRow("Ambient Temp (°C):", self.ambient_input)
        form.addRow("Iterations:", self.iterations_input)
        form.addRow("Material:", self.material_dropdown)
        config_box.setLayout(form)
        left_layout.addWidget(config_box)

        sources_box = QGroupBox("Heat Sources (CPU, Memory, IO)")
        sources_form = QFormLayout()
        self.source_inputs = []
        defaults = [
            ("CPU_Core", "8,12", "8,12", "120"),
            ("Memory_Block", "2,5", "14,17", "70"),
            ("IO_Block", "15,18", "2,5", "50"),
        ]
        for name, xr, yr, pt in defaults:
            name_in = QLineEdit(name)
            xr_in = QLineEdit(xr)
            yr_in = QLineEdit(yr)
            pt_in = QLineEdit(pt)
            sources_form.addRow(f"{name} X-range:", xr_in)
            sources_form.addRow(f"{name} Y-range:", yr_in)
            sources_form.addRow(f"{name} Power (°C):", pt_in)
            self.source_inputs.append((name_in, xr_in, yr_in, pt_in))
        sources_box.setLayout(sources_form)
        left_layout.addWidget(sources_box)

        self.run_btn = QPushButton("▶  Run FEM Simulation")
        self.run_btn.clicked.connect(self.run_simulation)
        left_layout.addWidget(self.run_btn)

        self.report_btn = QPushButton("📄 Generate PDF Report")
        self.report_btn.clicked.connect(self.export_report)
        left_layout.addWidget(self.report_btn)

        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #a6e3a1; padding: 6px;")
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(left_panel)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(340)
        main_layout.addWidget(scroll)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        plots_layout = QHBoxLayout()
        self.heatmap_fig = Figure(figsize=(5, 4))
        self.heatmap_canvas = FigureCanvasQTAgg(self.heatmap_fig)
        plots_layout.addWidget(self.heatmap_canvas)

        self.history_fig = Figure(figsize=(5, 4))
        self.history_canvas = FigureCanvasQTAgg(self.history_fig)
        plots_layout.addWidget(self.history_canvas)

        right_layout.addLayout(plots_layout)

        metrics_box = QGroupBox("Hotspot Report")
        metrics_grid = QGridLayout()
        self.max_label = QLabel("Max Temp: --")
        self.avg_label = QLabel("Avg Temp: --")
        self.var_label = QLabel("Variance: --")
        self.count_label = QLabel("Hotspot Cells: --")
        for i, lbl in enumerate([self.max_label, self.avg_label, self.var_label, self.count_label]):
            lbl.setStyleSheet("font-size: 14px; padding: 5px; color: #f9e2af;")
            metrics_grid.addWidget(lbl, 0, i)
        metrics_box.setLayout(metrics_grid)
        right_layout.addWidget(metrics_box)

        main_layout.addWidget(right_panel)

    def run_simulation(self):
        try:
            self.status_label.setText("Running FEM simulation...")
            QApplication.processEvents()

            selected_material = self.material_dropdown.currentText()

            config = {
                "width": float(self.width_input.text()),
                "height": float(self.height_input.text()),
                "nx": int(self.nx_input.text()),
                "ny": int(self.ny_input.text()),
                "ambient_temp": float(self.ambient_input.text()),
                "iterations": int(self.iterations_input.text()),
                "conductivity": MATERIALS[selected_material],
                "rho_c": 1.0,
                "dt": 0.5,
                "heat_sources": []
            }

            for name_in, xr_in, yr_in, pt_in in self.source_inputs:
                x0, x1 = map(float, xr_in.text().split(","))
                y0, y1 = map(float, yr_in.text().split(","))
                config["heat_sources"].append({
                    "name": name_in.text(),
                    "x_range": [x0, x1],
                    "y_range": [y0, y1],
                    "power_temp": float(pt_in.text())
                })

            nodes, elements = generate_mesh(config["width"], config["height"], config["nx"], config["ny"])
            T, history = run_fem_simulation(nodes, elements, config)
            report = detect_hotspots(T, threshold=80)

            grid = reshape_to_grid(T, config["nx"], config["ny"])

            self.heatmap_fig.clear()
            ax1 = self.heatmap_fig.add_subplot(111)

            x = np.linspace(0, config["width"], grid.shape[1])
            y = np.linspace(0, config["height"], grid.shape[0])

            contour = ax1.contourf(x, y, grid, levels=40, cmap="turbo")
            cbar = self.heatmap_fig.colorbar(contour, ax=ax1, label="Temperature (°C)")
            cbar.ax.yaxis.label.set_color('white')
            cbar.ax.tick_params(colors='white')

            ax1.plot(
                [0, config["width"], config["width"], 0, 0],
                [0, 0, config["height"], config["height"], 0],
                color="white", linewidth=1.2
            )

            ax1.set_title(f"FEM Thermal Distribution — {selected_material}", color="white", fontsize=12, fontweight="bold")
            ax1.set_xlabel("Width (mm)")
            ax1.set_ylabel("Height (mm)")
            self.heatmap_canvas.draw()

            # Save heatmap image to output folder (next to .exe)
            heatmap_path = os.path.join(get_output_dir(), "current_heatmap.png")
            self.heatmap_fig.savefig(heatmap_path, dpi=150, facecolor=self.heatmap_fig.get_facecolor())
            self.last_heatmap_path = heatmap_path

            self.history_fig.clear()
            ax2 = self.history_fig.add_subplot(111)
            ax2.plot(history, color="#f38ba8", linewidth=2)
            ax2.set_xlabel("Time Step")
            ax2.set_ylabel("Max Temp (°C)")
            ax2.set_title("Peak Temperature Over Time", color="white", fontsize=12, fontweight="bold")
            ax2.grid(True, color="#45475a", linestyle="--", linewidth=0.5)
            self.history_canvas.draw()

            self.max_label.setText(f"Max Temp: {report['max_temp']:.2f} °C")
            self.avg_label.setText(f"Avg Temp: {report['avg_temp']:.2f} °C")
            self.var_label.setText(f"Variance: {report['variance']:.2f}")
            self.count_label.setText(f"Hotspot Cells: {report['hotspot_count']}")

            self.status_label.setText(f"Simulation Completed ({selected_material}).")

            # Store for PDF report
            self.last_report = report
            self.last_material = selected_material
            self.last_config = config

        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def export_report(self):
        try:
            if not hasattr(self, 'last_report'):
                self.status_label.setText("Run a simulation first!")
                return
            report_path = os.path.join(get_output_dir(), "thermal_report.pdf")
            path = generate_pdf_report(
                self.last_report, self.last_material, self.last_config,
                self.last_heatmap_path, save_path=report_path
            )
            self.status_label.setText(f"Report saved: {path}")
        except Exception as e:
            self.status_label.setText(f"Report Error: {e}")


def main():
    app = QApplication(sys.argv)
    window = ThermalApp()
    window.setWindowIcon(QIcon(resource_path("assets/logo.ico")))
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()