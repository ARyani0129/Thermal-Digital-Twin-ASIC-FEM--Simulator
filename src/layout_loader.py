import json
import os


class LayoutLoader:
    """
    Parses chip floorplan JSON files and converts block geometries
    & power values into heat source data usable by the FEM solver.
    """

    @staticmethod
    def load_layout(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            return LayoutLoader._parse_json_layout(file_path)
        else:
            raise ValueError(f"Unsupported layout file format: {ext}. Use .json")

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