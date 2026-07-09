"""
get_machine_id.py
Send this tiny script (or its compiled .exe) to a new client BEFORE licensing them.
They run it once, and send you the printed ID. This file contains no license
logic or secrets, so it is safe to share.

Uses the same stable ID method as license_manager.py (Windows BIOS UUID,
with a uuid.getnode() fallback) so the ID always matches what validate_license()
computes.
"""

from license_manager import get_machine_id

if __name__ == "__main__":
    machine_id = get_machine_id()
    print("Your Machine ID (send this to MAH Quantum for license activation):")
    print(machine_id)
    input("\nPress Enter to close...")
