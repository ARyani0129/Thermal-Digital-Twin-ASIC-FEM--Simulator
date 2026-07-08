"""
update_checker.py
Lightweight, non-blocking version check against your GitHub repo's releases.
Does NOT auto-download anything - just notifies the user if a newer version
exists. Fails silently if there's no internet (does not block the app).
"""

import json
import os
import sys

CURRENT_VERSION = "1.0.0"  # bump this manually with every release
GITHUB_API_URL = "https://api.github.com/repos/ARyani0129/Thermal-Digital-Twin-ASIC-FEM--Simulator/releases/latest"


def check_for_update(timeout_seconds=3):
    """
    Returns (update_available: bool, latest_version: str or None, message: str)
    Never raises - always safe to call even with no internet.
    """
    try:
        import urllib.request
        req = urllib.request.Request(GITHUB_API_URL, headers={"User-Agent": "TDT-UpdateChecker"})
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode())
            latest_tag = data.get("tag_name", "").lstrip("v")

            if latest_tag and latest_tag != CURRENT_VERSION:
                return True, latest_tag, f"A new version ({latest_tag}) is available. You have {CURRENT_VERSION}."
            return False, latest_tag, "You are using the latest version."
    except Exception:
        # No internet, rate-limited, or repo not reachable - fail silently
        return False, None, "Could not check for updates (offline)."
