import jupyter_dash.comms
from .jupyter_app import JupyterDash


def _jupyter_nbextension_paths():
    return [
        {
            "section": "notebook",
            "src": "nbextension/static",
            "dest": "jupyter_dash",
            "require": "jupyter_dash/main",
        }
    ]
