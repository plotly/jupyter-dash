# Change Log for JupyterDash
All notable changes to `jupyter-dash` will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## 0.4.1 - 2022-02-16
### Fixed
 - Support Dash 2.1, fix `AttributeError: Read-only... requests_pathname_prefix`

## 0.4.0 - 2021-01-22
### Added
 - JuypterLab 3.0 support

## 0.3.0 - 2020-07-21
### Added
 - Added suport for using JupyterDash in Google Colab ([#27](https://github.com/plotly/jupyter-dash/pull/27))
 - Added support for installing JupyterDash from git using pip: (e.g. `pip install git+https://github.com/plotly/jupyter-dash.git@master`)

### Changed
 - The default display width in `mode='inline'` is now `100%` to fill the screen width.

## 0.2.1 - 2020-05-19
### Added
 - Remove f-strings to support Python 3.5

## 0.2.0 - 2020-05-19
Initial Release
