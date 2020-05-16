import jupyter_dash.comms
from .jupyter_app import JupyterDash
from .version import __version__

def _jupyter_nbextension_paths():
    return [
        {
            "section": "notebook",
            "src": "nbextension",
            "dest": "jupyter_dash",
            "require": "jupyter_dash/main",
        }
    ]
