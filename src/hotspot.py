import numpy as np

def detect_hotspots(T, threshold=80):
    coords = np.where(T > threshold)
    locations = list(coords[0]) if len(coords) == 1 else list(zip(*coords))
    return {
        "threshold": threshold,
        "hotspot_count": len(locations),
        "max_temp": float(np.max(T)),
        "avg_temp": float(np.mean(T)),
        "variance": float(np.var(T))
    }