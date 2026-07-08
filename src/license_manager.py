"""
license_manager.py
Machine-bound licensing system for Thermal Digital Twin (MAH Quantum)

Usage:
    - generate_key.py (internal, run by Mahi) creates license.json for each client
    - gui_app.py calls validate_license() at startup before showing the main window
"""

import hashlib
import uuid
import json
import os
import sys
from datetime import datetime, timedelta

# Keep this secret. Do NOT commit this file with the real salt to a public GitHub repo.
# For the public repo, replace SECRET_SALT with a placeholder and store the real one
# separately (e.g. in a private config not tracked by git).
SECRET_SALT = "MAHQUANTUM_TDT_2026_CHANGE_THIS_BEFORE_SHIPPING"

LICENSE_FILENAME = "license.json"


def get_machine_id():
    """Returns a stable hardware-based identifier for this machine."""
    return str(uuid.getnode())


def _compute_key(machine_id, client_name, expiry_str):
    raw = f"{machine_id}-{client_name}-{expiry_str}-{SECRET_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def generate_license(machine_id, client_name, valid_days=365):
    """
    Call this ONLY from your internal generate_key.py tool, never ship this
    function inside the client-facing .exe.
    """
    expiry = (datetime.now() + timedelta(days=valid_days)).strftime("%Y-%m-%d")
    key = _compute_key(machine_id, client_name, expiry)
    return {
        "key": key,
        "client": client_name,
        "expiry": expiry,
        "machine_id": machine_id,
        "issued_on": datetime.now().strftime("%Y-%m-%d"),
    }


def _get_license_path():
    """
    Resolves license.json path next to the running .exe (or script when
    running from source). Uses the same resource_path pattern you already
    use elsewhere in the project.
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, LICENSE_FILENAME)


def validate_license():
    """
    Returns (is_valid: bool, message: str)
    """
    license_path = _get_license_path()

    if not os.path.exists(license_path):
        return False, "No license file found. Please contact MAH Quantum to activate this installation."

    try:
        with open(license_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False, "License file is corrupted. Please contact MAH Quantum for a new license."

    required_fields = {"key", "client", "expiry", "machine_id"}
    if not required_fields.issubset(data.keys()):
        return False, "License file is invalid (missing fields)."

    current_machine = get_machine_id()
    if data["machine_id"] != current_machine:
        return False, "This license is not valid for this machine. Please request a new license."

    try:
        expiry_date = datetime.strptime(data["expiry"], "%Y-%m-%d")
    except ValueError:
        return False, "License expiry date is invalid."

    if datetime.now() > expiry_date:
        return False, f"License expired on {data['expiry']}. Please renew your license."

    expected_key = _compute_key(data["machine_id"], data["client"], data["expiry"])
    if data["key"] != expected_key:
        return False, "License key is invalid or has been tampered with."

    days_left = (expiry_date - datetime.now()).days
    warning = f" (expires in {days_left} days)" if days_left <= 30 else ""

    return True, f"Licensed to {data['client']} until {data['expiry']}{warning}."


if __name__ == "__main__":
    # Quick manual test: run this file directly to check machine ID
    print(f"Machine ID for this computer: {get_machine_id()}")
    valid, msg = validate_license()
    print(f"License valid: {valid}")
    print(f"Message: {msg}")
