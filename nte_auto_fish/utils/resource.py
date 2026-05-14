import os
import sys

def project_root():
    return os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def bundled_root():
    """Return the read-only resource root for source and PyInstaller runs."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return project_root()


def app_root():
    """Return the writable app root for local config/log files."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return project_root()


def resource_path(relative_path):
    """Get absolute path to a bundled resource."""
    return os.path.join(bundled_root(), relative_path)
