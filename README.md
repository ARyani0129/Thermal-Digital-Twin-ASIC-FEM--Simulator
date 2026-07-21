# Thermal Digital Twin — ASIC FEM Simulator

A desktop engineering tool for thermal analysis and hotspot detection in semiconductor chip (ASIC) designs, developed during AI System Engineering R&D Internship at MAH Quantum.

## Overview
This software simulates heat distribution across a semiconductor chip using the Finite Element Method (FEM), allowing engineers to visualize thermal hotspots, compare materials, and analyze peak temperatures under different configurations.

## Features
- Finite Element Method (FEM) based heat diffusion solver
- Configurable chip dimensions and mesh resolution
- Multiple independent heat sources (CPU, Memory, I/O blocks)
- Material selection (Silicon, Copper, Aluminum, Diamond)
- Real-time thermal heatmap visualization
- Hotspot detection and statistical analysis
- PDF report generation
- Packaged as a standalone Windows desktop application (.exe)

## Tech Stack
- Python 3.8
- NumPy, SciPy (FEM matrix assembly and sparse solving)
- Matplotlib (visualization)
- PySide6 (desktop GUI)
- ReportLab (PDF report generation)
- PyInstaller (executable packaging)

## How It Works
1. User defines chip geometry, mesh resolution, ambient temperature, and material
2. User specifies heat source locations and power levels
3. Software generates a finite element mesh and assembles global stiffness/mass matrices
4. Transient heat equation is solved using implicit time-stepping
5. Results are visualized as a thermal heatmap with hotspot statistics
6. A PDF report can be generated summarizing the analysis

## Project Structure
Thermal_Digital_Twin/

├── assets/          # Branding assets (logo, icon)

├── data/            # Configuration files

├── outputs/         # Generated heatmaps, reports

├── src/             # Source code

│   ├── fem_mesh.py

│   ├── fem_solver.py

│   ├── hotspot.py

│   ├── heatmap.py

│   ├── report_generator.py

│   └── gui_app.py

└── project_evidence/ # Screenshots, demo materials
## Author
Aryani Yadav — AI System Engineering R&D Intern, MAH Quantum (June–September 2026)
