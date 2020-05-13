import dash
import os
import requests
from flask import request
import flask.cli
from threading import Thread
from retrying import retry
import io
import re
import sys

from IPython.display import IFrame, display
from IPython.core.ultratb import FormattedTB
from ansi2html import Ansi2HTMLConverter


from werkzeug.debug.tbtools import get_current_traceback

from .comms import _dash_comm, _jupyter_config, _request_jupyter_config


class JupyterDash(dash.Dash):
    """A Dash subclass for developing Dash apps interactively in Jupyter.

    :param server_url:  The base URL that the app will be served at, from the
        perspective of the client. If not specified, will default to the host argument
        passed to the ``run_server`` method.

    See parent docstring for additional parameters
    """
    default_mode = 'external'
    default_requests_pathname_prefix = None
    default_server_url = None

    @classmethod
    def infer_jupyter_config(cls):
        """
        Infer the current Jupyter server configuration. This will detect
        the proper request_pathname_prefix and server_url values to use when
        displaying Dash apps.  When the jupyter_server_proxy Python package is
        installed, all Dash requests will be routed through the proxy.

        Requirements:

        In the classic notebook, this method requires the `jupyter_dash` nbextension
        which should be installed automatically with the installation of the
        jupyter-dash Python package. You can see what notebook extensions are installed
        by running the following command:
            $ jupyter nbextension list

        In JupyterLab, this method requires the `jupyterlab-dash` labextension. This
        extension should be installed automatically with the installation of the
        jupyter-dash Python package, but JupyterLab must be allowed to rebuild before
        the extension is activated (JupyterLab should automatically detect the
        extension and produce a popup dialog asking for permission to rebuild). You can
        see what JupyterLab extensions are installed by running the following command:
            $ jupyter labextension list
        """
        _request_jupyter_config()

    def __init__(self, name=None, server_url=None, **kwargs):
        """"""
        # See if jupyter_server_proxy is installed
        try:
            import jupyter_server_proxy
            self._server_proxy = True
        except Exception:
            self._server_proxy = False

        self._traceback = None

        if ('base_subpath' in _jupyter_config and self._server_proxy and
                JupyterDash.default_requests_pathname_prefix is None):
            JupyterDash.default_requests_pathname_prefix = (
                _jupyter_config['base_subpath'].rstrip('/') + '/proxy/{port}/'
            )

        if ('server_url' in _jupyter_config and self._server_proxy and
                JupyterDash.default_server_url is None):
            JupyterDash.default_server_url = _jupyter_config['server_url']

        self._input_pathname_prefix = kwargs.get('requests_pathname_prefix', None)

        # Call superclass constructor
        super(JupyterDash, self).__init__(name=name, **kwargs)

        # Infer server_url
        if server_url is None:
            domain_base = os.environ.get('PLOTLY_DASH_DOMAIN_BASE', None)
            if domain_base:
                # Dash Enterprise set PLOTLY_DASH_DOMAIN_BASE environment variable
                server_url = 'https://' + domain_base

        self.server_url = server_url

        # Register route to shut down server
        @self.server.route('/_shutdown', methods=['GET'])
        def shutdown():
            func = request.environ.get('werkzeug.server.shutdown')
            if func is None:
                raise RuntimeError('Not running with the Werkzeug Server')
            func()
            return 'Server shutting down...'

        # Register route that we can use to poll to see when server is running
        @self.server.route('/_alive', methods=['GET'])
        def alive():
            return 'Alive'

        self.server.logger.disabled = True

    def run_server(
            self,
            mode=None, width=800, height=650, inline_exceptions=None,
            **kwargs
    ):
        """
        Serve the app using flask in a background thread. You should not run this on a
        production server, use gunicorn/waitress instead.

        :param mode: Display mode. One of:
            ``"external"``: The URL of the app will be displayed in the notebook
                output cell. Clicking this URL will open the app in the default
                web browser.
            ``"inline"``: The app will be displayed inline in the notebook output cell
                in an iframe.
            ``"jupyterlab"``: The app will be displayed in a dedicate tab in the
                JupyterLab interface. Requires JupyterLab and the `jupyterlab-dash`
                extension.
        :param width: Width of app when displayed using mode="inline"
        :param height: Height of app when displayed using mode="inline"
        :param inline_exceptions: If True, callback exceptions are displayed inline
            in the the notebook output cell. Defaults to True if mode=="inline",
            False otherwise.
        :param kwargs: Additional keyword arguments to pass to the superclass
            ``Dash.run_server`` method.
        """
        # Get host and port
        host = kwargs.get("host", os.getenv("HOST", "127.0.0.1"))
        port = kwargs.get("port", os.getenv("PORT", "8050"))

        kwargs['host'] = host
        kwargs['port'] = port

        # Validate / infer display mode
        valid_display_values = ["jupyterlab", "inline", "external"]

        if mode is None:
            mode = JupyterDash.default_mode
        elif not isinstance(mode, str):
            raise ValueError(
                "The mode argument must be a string\n"
                "    Received value of type {typ}: {val}".format(
                    typ=type(mode), val=repr(mode)
                )
            )
        else:
            mode = mode.lower()
            if mode not in valid_display_values:
                raise ValueError(
                    "Invalid display argument {display}\n"
                    "    Valid arguments: {valid_display_values}".format(
                        display=repr(mode), valid_display_values=valid_display_values
                    )
                )

        # Infer inline_exceptions and ui
        if inline_exceptions is None:
            inline_exceptions = mode == "inline"

        # Terminate any existing server using this port
        self._terminate_server_for_port(host, port)

        # Run superclass run_server is separate thread
        super_run_server = super(JupyterDash, self).run_server

        # Configure pathname prefix
        requests_pathname_prefix = self.config.get('requests_pathname_prefix', None)
        if self._input_pathname_prefix is None:
            requests_pathname_prefix = self.default_requests_pathname_prefix

        if requests_pathname_prefix is not None:
            requests_pathname_prefix = requests_pathname_prefix.format(port=port)
        else:
            requests_pathname_prefix = '/'
        self.config.update({'requests_pathname_prefix': requests_pathname_prefix})

        # Compute server_url url
        if self.server_url is None:
            if JupyterDash.default_server_url:
                server_url = JupyterDash.default_server_url.rstrip('/')
            else:
                server_url = f'http://{host}:{port}'
        else:
            server_url = self.server_url.rstrip('/')

        dashboard_url = "{server_url}{requests_pathname_prefix}".format(
            server_url=server_url, requests_pathname_prefix=requests_pathname_prefix
        )

        # Default the global "debug" flag to True
        debug = kwargs.get('debug', True)

        # Disable debug flag when calling superclass because it doesn't work
        # in notebook
        kwargs['debug'] = False

        # Enable supported dev tools
        if debug:
            for k in [
                'dev_tools_silence_routes_logging',
                'dev_tools_props_check',
                'dev_tools_serve_dev_bundles',
                'dev_tools_prune_errors'
            ]:
                if k not in kwargs:
                    kwargs[k] = True

            # Enable dev tools by default unless app is displayed inline
            if 'dev_tools_ui' not in kwargs:
                kwargs['dev_tools_ui'] = mode != "inline"

            if 'dev_tools_hot_reload' not in kwargs:
                # Enable hot-reload by default in "external" mode. Enabling in inline or
                # in JupyterLab extension seems to cause Jupyter problems sometimes when
                # there is no active kernel.
                kwargs['dev_tools_hot_reload'] = mode == "external"

        # suppress warning banner printed to standard out
        flask.cli.show_server_banner = lambda *args, **kwargs: None

        # Set up custom callback exception handling
        self._config_callback_exception_handling(
            dev_tools_prune_errors=kwargs.get('dev_tools_prune_errors', True),
            inline_exceptions=inline_exceptions,
        )

        @retry(
            stop_max_attempt_number=15,
            wait_exponential_multiplier=100,
            wait_exponential_max=1000
        )
        def run():
            super_run_server(**kwargs)

        thread = Thread(target=run)
        thread.setDaemon(True)
        thread.start()

        # Wait for server to start up
        alive_url = "http://{host}:{port}/_alive".format(
            host=host, port=port
        )

        # Wait for app to respond to _alive endpoint
        @retry(
            stop_max_attempt_number=15,
            wait_exponential_multiplier=10,
            wait_exponential_max=1000
        )
        def wait_for_app():
            res = requests.get(alive_url)
            return res.content.decode()

        wait_for_app()

        if mode == 'inline':
            display(IFrame(dashboard_url, width, height))
        elif mode == 'external':
            # Display a hyperlink that can be clicked to open Dashboard
            print("Dash app running on {dashboard_url}".format(
                dashboard_url=dashboard_url
            ))
        elif mode == 'jupyterlab':
            if _jupyter_config.get("frontend") != "jupyterlab":
                raise IOError("""
Unable to communicate with the jupyterlab-dash JupyterLab extension.
Is this Python kernel running inside JupyterLab with the jupyterlab-dash
extension installed?

You can install the extension with:

$ jupyter labextension install jupyterlab-dash
""")
            # Update front-end extension
            _dash_comm.send({
                'type': 'show',
                'port': port,
                'url': dashboard_url,
            })

    def _config_callback_exception_handling(
            self, dev_tools_prune_errors, inline_exceptions
    ):

        @self.server.errorhandler(Exception)
        def _wrap_errors(_):
            """Install traceback handling for callbacks"""
            self._traceback = sys.exc_info()[2]

            # Compute number of stack frames to skip to get down to callback
            tb = get_current_traceback()
            skip = 0
            if dev_tools_prune_errors:
                for i, line in enumerate(tb.plaintext.splitlines()):
                    if "%% callback invoked %%" in line:
                        skip = int((i + 1) / 2)
                        break

            # Use IPython traceback formatting to build colored ANSI traceback string
            ostream = io.StringIO()
            ipytb = FormattedTB(
                tb_offset=skip,
                mode="Verbose",
                color_scheme="Linux",
                include_vars=True,
                ostream=ostream
            )
            ipytb()

            # Print colored ANSI representation if requested
            if inline_exceptions:
                print(ostream.getvalue())

            # Use ansi2html to convert the colored ANSI string to HTML
            conv = Ansi2HTMLConverter(scheme="ansi2html", dark_bg=False)
            html_str = conv.convert(ansi_stacktrace)

            html_str = html_str.replace(
                '<html>',
                '<html style="width: 80ex;">'
            )

            # Remove explicit background color so Dash dev-tools can set background
            # color
            html_str = re.sub("background-color:[^;]+;", "", html_str)

            return html_str, 500

    @classmethod
    def _terminate_server_for_port(cls, host, port):
        shutdown_url = "http://{host}:{port}/_shutdown".format(
            host=host, port=port
        )
        try:
            response = requests.get(shutdown_url)
        except Exception as e:
            pass
