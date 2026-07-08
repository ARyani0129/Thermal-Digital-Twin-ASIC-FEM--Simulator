"""
error_logger.py
Catches unhandled exceptions and writes them to a log file next to the .exe,
so clients can send you the log file when something breaks.
"""

import sys
import os
import logging
import traceback
from datetime import datetime


def _get_log_path():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "app_errors.log")


def setup_logging():
    logging.basicConfig(
        filename=_get_log_path(),
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logging.error(f"Unhandled exception:\n{error_msg}")

    # Optional: show a friendly popup instead of a raw crash
    try:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(
            None,
            "Unexpected Error",
            "Something went wrong. A log has been saved to app_errors.log.\n"
            "Please send this file to MAH Quantum support.",
        )
    except Exception:
        pass


def install_global_handler():
    setup_logging()
    sys.excepthook = handle_exception
    logging.info(f"--- Session started: {datetime.now()} ---")
