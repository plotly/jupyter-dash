import os
import shutil
from subprocess import check_call
import json
import time

from setuptools import setup, Command
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info

here = os.path.dirname(os.path.abspath(__file__))
is_repo = os.path.exists(os.path.join(here, ".git"))


def get_labextension_version():
    if is_repo:
        labextension_dir = os.path.join(here, "extensions", "jupyterlab")
    else:
        labextension_dir = os.path.join(here, "jupyter_dash", "labextension")

    package_json = os.path.join(labextension_dir, 'package.json')
    with open(package_json, 'rt') as f:
        package_data = json.load(f)

    labextension_version = package_data['version']
    return labextension_version


def js_prerelease(command):
    """decorator for building JavaScript extensions before command"""
    class DecoratedCommand(command):
        def run(self):
            self.run_command("build_js")
            command.run(self)
    return DecoratedCommand


class BuildLabextension(Command):
    description = "Build JupyterLab extension"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not is_repo:
            # Nothing to do
            return

        # Load labextension version from package.json
        out_labextension_dir = os.path.join(here, "jupyter_dash", "labextension")
        os.makedirs(out_labextension_dir, exist_ok=True)

        # Copy package.json to labextension directory
        shutil.copy(
            os.path.join(here, "extensions", "jupyterlab", "package.json"),
            out_labextension_dir
        )
        time.sleep(0.5)
        in_labextension_dir = os.path.join(here, "extensions", "jupyterlab")

        # Build filename
        labextension_version = get_labextension_version()
        filename = "jupyterlab-dash-v{ver}.tgz".format(
            ver=labextension_version
        )

        # Build and pack extension
        dist_path = os.path.join(out_labextension_dir, "dist")
        shutil.rmtree(dist_path, ignore_errors=True)
        os.makedirs(dist_path, exist_ok=True)

        check_call(
            ['jlpm', "install"],
            cwd=in_labextension_dir,
        )
        check_call(
            ['jlpm', "build"],
            cwd=in_labextension_dir,
        )
        check_call(
            ['jlpm', "pack", "--filename", dist_path + "/" + filename],
            cwd=in_labextension_dir,
        )


setup(
    name='jupyter-dash',
    version='0.0.1a2',
    description="Dash support for the Jupyter notebook interface",
    author='Plotly',
    packages=['jupyter_dash'],
    install_requires=['dash', 'requests', 'flask', 'retrying', 'ipython'],
    include_package_data=True,
    package_data={
        "jupyter_dash": [
            "labextension/package.json",
        ],
    },
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
            "jupyter_dash/labextension/dist/jupyterlab-dash-v{ver}.tgz".format(
                ver=get_labextension_version()
            )
        ]),
    ],
    cmdclass=dict(
        build_js=BuildLabextension,
        build_py=js_prerelease(build_py),
        egg_info=js_prerelease(egg_info),
        sdist=js_prerelease(sdist),
    )
)
