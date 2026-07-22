import json
import os
import re

class LayoutLoader:
    @staticmethod
    def load_layout(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            return LayoutLoader._parse_json_layout(file_path)
        elif ext == ".def":
            return LayoutLoader._parse_def_layout(file_path)
        else:
            raise ValueError(f"Unsupported layout file format: {ext}")

    @staticmethod
    def _parse_json_layout(file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
        chip_dim = data.get("die_dimensions", {"width_mm": 20.0, "height_mm": 20.0})
        heat_sources = []
        for block in data.get("blocks", []):
            heat_sources.append({
                "name": block.get("name", "Unnamed_Block"),
                "x_range": [block["x_min"], block["x_max"]],
                "y_range": [block["y_min"], block["y_max"]],
                "power_temp": block.get("power_watts", 5.0)
            })
        return {
            "chip_size": (chip_dim["width_mm"], chip_dim["height_mm"]),
            "heat_sources": heat_sources,
            "materials": data.get("materials", ["Silicon"])
        }

    @staticmethod
    def _parse_def_layout(file_path):
        heat_sources = []
        die_width, die_height = 20.0, 20.0
        dbu_per_micron = 1000.0
        with open(file_path, "r") as f:
            lines = f.readlines()
        in_components = False
        for raw_line in lines:
            line = raw_line.strip()
            if line.startswith("UNITS DISTANCE MICRONS"):
                match = re.search(r"MICRONS\s+(\d+)", line)
                if match:
                    dbu_per_micron = float(match.group(1))
            if line.startswith("DIEAREA"):
                coords = re.findall(r"-?\d+", line)
                if len(coords) >= 4:
                    x_vals = [float(coords[i]) for i in range(0, len(coords), 2)]
                    y_vals = [float(coords[i]) for i in range(1, len(coords), 2)]
                    die_width = (max(x_vals) - min(x_vals)) / dbu_per_micron / 1000.0
                    die_height = (max(y_vals) - min(y_vals)) / dbu_per_micron / 1000.0
            if line.startswith("COMPONENTS"):
                in_components = True
                continue
            if line.startswith("END COMPONENTS"):
                in_components = False
                continue
            if in_components and line.startswith("-"):
                parts = line.split()
                if len(parts) < 2:
                    continue
                comp_name = parts[1]
                placed_match = re.search(r"\(\s*(-?\d+)\s+(-?\d+)\s*\)", line)
                if not placed_match:
                    continue
                x_dbu, y_dbu = float(placed_match.group(1)), float(placed_match.group(2))
                x_mm = (x_dbu / dbu_per_micron) / 1000.0
                y_mm = (y_dbu / dbu_per_micron) / 1000.0
                default_half_size_mm = 0.5
                heat_sources.append({
                    "name": comp_name,
                    "x_range": [max(0, x_mm - default_half_size_mm), min(die_width, x_mm + default_half_size_mm)],
                    "y_range": [max(0, y_mm - default_half_size_mm), min(die_height, y_mm + default_half_size_mm)],
                    "power_temp": 5.0
                })
        return {
            "chip_size": (die_width, die_height),
            "heat_sources": heat_sources,
            "materials": ["Silicon"]
        }