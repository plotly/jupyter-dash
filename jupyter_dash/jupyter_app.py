import dash
import os
import requests
from flask import request
import flask.cli
from threading import Thread
from retrying import retry

import IPython
from IPython.display import HTML, IFrame, display
from ipykernel.comm import Comm

class JupyterDash(dash.Dash):
    _dash_comm = Comm(target_name='dash_viewer')
    _jupyterlab_base_url = None

    def __init__(self, base_url=None, **kwargs):
        # Infer requests_pathname_prefix
        requests_pathname_prefix = kwargs.get('requests_pathname_prefix', None)
        if requests_pathname_prefix is None:
            if JupyterDash._jupyterlab_base_url:
                # We're in a JupyterLab context and jupyter_server_proxy is installed
                kwargs['requests_pathname_prefix'] = '/proxy/{port}/'

        # Call superclass constructor
        super(JupyterDash, self).__init__(**kwargs)

        # Infer base_url
        if base_url is None:
            domain_base = os.environ.get('PLOTLY_DASH_DOMAIN_BASE', None)
            if JupyterDash._jupyterlab_base_url:
                # JupyterLab extension reported base url
                base_url = JupyterDash._jupyterlab_base_url
            elif domain_base:
                # Dash Enterprise set PLOTLY_DASH_DOMAIN_BASE environment variable
                base_url = 'https://' + domain_base

        self.base_url = base_url

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
            if JupyterDash._jupyterlab_base_url:
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
            'dev_tools_hot_reload',
            # 'dev_tools_ui',  # Stack traces don't work yet
            'dev_tools_props_check',
            'dev_tools_serve_dev_bundles',
            'dev_tools_prune_errors'
        ]:
            if k not in kwargs:
                kwargs[k] = True

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
            if not self._jupyterlab_base_url:
                raise IOError("""
Unable to communicate with the jupyterlab-dash JupyterLab extension.
Is this Python kernel running inside JupyterLab with the jupyterlab-dash
extension installed?

You can install the extension with:

$ jupyter labextension install jupyterlab-dash
""")
            # Update front-end extension
            self._dash_comm.send({
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


# Register handler to process events sent from the
# front-end JupyterLab extension to the python kernel
@JupyterDash._dash_comm.on_msg
def _receive_message(msg):
    msg_data = msg.get('content').get('data')
    msg_type = msg_data.get('type', None)
    if msg_type == 'base_url_response':
        JupyterDash._jupyterlab_base_url = msg_data['base_url']


# If running in an ipython kernel,
# request that the front end extension send us the notebook server base URL
if IPython.get_ipython() is not None:
    if JupyterDash._dash_comm.kernel is not None:
        JupyterDash._dash_comm.send({
            'type': 'base_url_request'
        })
