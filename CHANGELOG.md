# Change Log for JupyterDash
All notable changes to `jupyter-dash` will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [UNRELEASED]
### Fixed
- Propagate start error message. [#94](https://github.com/plotly/jupyter-dash/pull/94)
- Fix rerun server with newer flask/werkzeug. [#105](https://github.com/plotly/jupyter-dash/pull/105)

### Added

- Support for `Dash.run` method added in Dash 2.4.0

## 0.4.2 - 2022-03-31
### Fixed
  - Fixed `werkzeug` 2.1.0 import and `skip` calculation, shutdown deprecation warning.
  - Work around a partial import of `orjson` when it's installed and you use `mode="jupyterlab"`
  - Fix `infer_jupyter_proxy_config` for newer jupyterlab versions

## 0.4.1 - 2022-02-16
### Fixed
 - Support Dash 2.1, fix `AttributeError: Read-only... requests_pathname_prefix`

## 0.4.0 - 2021-01-22
### Added
 - JuypterLab 3.0 support

## 0.3.0 - 2020-07-21
### Added
 - Added support for using JupyterDash in Google Colab ([#27](https://github.com/plotly/jupyter-dash/pull/27))
 - Added support for installing JupyterDash from git using pip: (e.g. `pip install git+https://github.com/plotly/jupyter-dash.git@master`)

### Changed
 - The default display width in `mode='inline'` is now `100%` to fill the screen width.

## 0.2.1 - 2020-05-19
### Added
 - Remove f-strings to support Python 3.5

## 0.2.0 - 2020-05-19
Initial Release
