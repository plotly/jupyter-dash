import jupyter_dash.comms
from .jupyter_app import JupyterDash


def _jupyter_nbextension_paths():
    return [
        {
            "section": "notebook",
            "src": "nbextension",
            "dest": "jupyter_dash",
            "require": "jupyter_dash/main",
        }
    ]


__labextension_version__ = "v0.2.0-alpha.2"
