from setuptools import setup

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
            "jupyter_dash/nbextension/static/main.js",
        ]),
         # like `jupyter nbextension enable --sys-prefix`
        ("etc/jupyter/nbconfig/notebook.d", [
            "jupyter_dash/nbextension/jupyter_dash.json"
        ]),
    ]
)
