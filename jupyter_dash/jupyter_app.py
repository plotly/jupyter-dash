import dash
import os
import requests
from flask import request
import flask.cli
from threading import Thread
from retrying import retry


from IPython.display import IFrame, display
from .comms import _dash_comm, _jupyter_config, _request_jupyter_config


class JupyterDash(dash.Dash):

    @classmethod
    def infer_jupyter_config(cls):
        _request_jupyter_config()

    def __init__(self, server_url=None, **kwargs):
        requests_pathname_prefix = kwargs.get('requests_pathname_prefix', None)
        if requests_pathname_prefix is None:
            if _jupyter_config.get('base_subpath', None):
                # We're in a Jupyter notebook/lab context, and jupyter_server_proxy is
                # installed
                kwargs['requests_pathname_prefix'] = (
                        _jupyter_config.get('base_subpath', None).rstrip('/') +
                        '/proxy/{port}/'
                )
        # Call superclass constructor
        super(JupyterDash, self).__init__(**kwargs)

        # Infer base_url
        if server_url is None:
            domain_base = os.environ.get('PLOTLY_DASH_DOMAIN_BASE', None)
            if _jupyter_config.get('server_url', None):
                server_url = _jupyter_config.get('server_url', None)
            elif domain_base:
                # Dash Enterprise set PLOTLY_DASH_DOMAIN_BASE environment variable
                server_url = 'https://' + domain_base

        self.base_url = server_url

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
            mode=None, width=800, height=650,
            host=os.getenv("HOST", "127.0.0.1"),
            port=os.getenv("PORT", "8050"),
            **kwargs
    ):
        # Validate / infer display
        valid_display_values = ["jupyterlab", "inline", "external"]

        if mode is None:
            # Infer default display argument
            if _jupyter_config.get('frontend', None) == "jupyterlab":
                # There is an active JupyterLab extension
                mode = "jupyterlab"
            else:
                mode = "external"
        elif not isinstance(mode, str):
            raise ValueError(
                "The display argument must be a string\n"
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

        # Terminate any existing server using this port
        self._terminate_server_for_port(host, port)

        # Run superclass run_server is separate thread
        super_run_server = super(JupyterDash, self).run_server

        # Configure urls
        requests_pathname_prefix = self.config.get('requests_pathname_prefix', None)
        if requests_pathname_prefix is not None:
            requests_pathname_prefix = requests_pathname_prefix.format(port=port)
            self.config.update({'requests_pathname_prefix': requests_pathname_prefix})
        else:
            requests_pathname_prefix = '/'

        # Compute base url
        if self.base_url is None:
            base = f'http://{host}:{port}'
        else:
            base = self.base_url.rstrip('/')

        dashboard_url = "{base}{requests_pathname_prefix}".format(
            base=base, requests_pathname_prefix=requests_pathname_prefix
        )

        # Enable supported dev tools by default
        for k in [
            'dev_tools_silence_routes_logging',
            # 'dev_tools_ui',  # Stack traces don't work yet
            'dev_tools_props_check',
            'dev_tools_serve_dev_bundles',
            'dev_tools_prune_errors'
        ]:
            if k not in kwargs:
                kwargs[k] = True

        if 'dev_tools_hot_reload' not in kwargs:
            # Enable hot-reload by default in "external" mode. Enabling in inline or
            # in JupyterLab extension seems to cause Jupyter problems sometimes when
            # there is no active kernel.
            kwargs['dev_tools_hot_reload'] = mode == "external"

        # Disable debug because it doesn't work in notebook
        kwargs['debug'] = False

        # suppress warning banner printed to standard out
        flask.cli.show_server_banner = lambda *args, **kwargs: None

        @retry(
            stop_max_attempt_number=15,
            wait_exponential_multiplier=100,
            wait_exponential_max=1000
        )
        def run():
            super_run_server(host=host, port=port, **kwargs)

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
                'port': port
            })

    @classmethod
    def _terminate_server_for_port(cls, host, port):
        shutdown_url = "http://{host}:{port}/_shutdown".format(
            host=host, port=port
        )
        try:
            response = requests.get(shutdown_url)
        except Exception as e:
            pass
