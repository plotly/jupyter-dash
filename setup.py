from setuptools import setup

from jupyter_dash import __labextension_version__

setup(
    name='jupyter-dash',
    version='0.0.1a1',
    description="Dash support for the Jupyter notebook interface",
    author='Plotly',
    packages=['jupyter_dash'],
    install_requires=['dash', 'requests', 'flask', 'retrying', 'ipython'],
    include_package_data=True,
    data_files=[
        # like `jupyter nbextension install --sys-prefix`
        ("share/jupyter/nbextensions/jupyter_dash", [
            "jupyter_dash/nbextension/main.js",
        ]),
        # like `jupyter nbextension enable --sys-prefix`
        ("etc/jupyter/nbconfig/notebook.d", [
            "jupyter_dash/nbextension/jupyter_dash.json"
        ]),
        # Place jupyterlab extension in extension directory
        ("share/jupyter/lab/extensions", [
            "extensions/jupyterlab/jupyterlab-dash-{ver}.tgz".format(
                ver=__labextension_version__
            )
        ]),
    ]
)
