# Jupyter Dash
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/plotly/jupyter-dash/master?urlpath=lab/tree/notebooks/getting_started.ipynb)

This library makes it easy to develop Plotly Dash apps interactively from within Jupyter environments (e.g. classic Notebook, JupyterLab, Visual Studio Code notebooks, nteract, PyCharm notebooks, etc.).

![](images/jupyterlab_mode.gif)

See the [notebooks/getting_started.ipynb](https://github.com/plotly/jupyter-dash/blob/master/notebooks/getting_started.ipynb) for more information and example usage.

# Installation
You can install the JupyterDash Python package using pip...
```
$ pip install jupyter-dash
```
or conda
```
$ conda install -c plotly jupyter-dash
```

## JupyterLab support
When used in JupyterLab, JupyterDash depends on the [`jupyterlab-dash`](https://www.npmjs.com/package/jupyterlab-dash) JupyterLab extension, which requires JupyterLab version 2.0 or above.
 
This extension is included with the Python package, but in order to activate it JupyterLab must be rebuilt. JupyterLab should automatically produce a popup dialog asking for permission to rebuild, but the rebuild can also be performed manually from the command line using:
 
 ```
$ jupyter lab build
```

To check that the extension is installed properly, call `jupyter labextension list`.

# Features
To learn more about the features of JupyterDash, check out the announcement post at https://medium.com/...

# Development
To develop JupyterDash, first create and activate a virtual environment using virtualenv or conda.

Then clone the repository and change directory to the repository root:
```
$ git clone https://github.com/plotly/jupyter-dash.git
$ cd jupyter-dash
```

Then install the dependencies:
```
$ pip install -r requirements.txt -r requirements-dev.txt 
```

Then install the Python package in editable mode. Note: this will require [nodejs](https://nodejs.org/en/) to be installed.
```
$ pip install -e .
```

Then install the classic notebook extension in development mode:
```
$ jupyter nbextension install --sys-prefix --symlink --py jupyter_dash
$ jupyter nbextension enable --py jupyter_dash
```

Then install the JupyterLab extension in development mode:
```
$ jupyter labextension link extensions/jupyterlab
```
