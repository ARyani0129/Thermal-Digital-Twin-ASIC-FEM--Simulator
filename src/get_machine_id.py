"""
get_machine_id.py
Send this tiny script (or its compiled .exe) to a new client BEFORE licensing them.
They run it once, and send you the printed ID. This file contains no license
logic or secrets, so it is safe to share.
"""

import uuid

if __name__ == "__main__":
    machine_id = str(uuid.getnode())
    print("Your Machine ID (send this to MAH Quantum for license activation):")
    print(machine_id)
    input("\nPress Enter to close...")
