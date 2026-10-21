import importlib.util
import io
import os
import sys
from contextlib import redirect_stdout, redirect_stderr

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(TESTS_DIR)

# Priority: release_4_azure directory if running from project root
if os.path.exists(os.path.join(PARENT_DIR, "release_4_azure", "app.py")):
    APP_DIR = os.path.join(PARENT_DIR, "release_4_azure")
elif os.path.exists(os.path.join(PARENT_DIR, "constants.py")):
    APP_DIR = PARENT_DIR
else:
    APP_DIR = PARENT_DIR

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

_cached_app = None


def get_app_module():
    """Load the target dashboard app module explicitly and reliably via importlib."""
    global _cached_app
    if _cached_app is not None:
        return _cached_app

    app_path = os.path.join(APP_DIR, "app.py")
    spec = importlib.util.spec_from_file_location("release_dashboard_app", app_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["release_dashboard_app"] = module

    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        spec.loader.exec_module(module)

    _cached_app = module
    return _cached_app
