import asyncio
import IPython
from ipykernel.comm import Comm
import nest_asyncio
import time
import sys

_jupyter_config = {}

_dash_comm = Comm(target_name='jupyter_dash')

_caller = {}


def _send_jupyter_config_comm_request():
    # If running in an ipython kernel,
    # request that the front end extension send us the notebook server base URL
    if IPython.get_ipython() is not None:
        if _dash_comm.kernel is not None:
            _caller["parent"] = _dash_comm.kernel.get_parent()
            _dash_comm.send({
                'type': 'base_url_request'
            })


@_dash_comm.on_msg
def _receive_message(msg):
    prev_parent = _caller.get("parent")
    if prev_parent and prev_parent != _dash_comm.kernel.get_parent():
        _dash_comm.kernel.set_parent([prev_parent["header"]["session"]], prev_parent)
        del _caller["parent"]

    msg_data = msg.get('content').get('data')
    msg_type = msg_data.get('type', None)
    if msg_type == 'base_url_response':
        _jupyter_config.update(msg_data)


def _jupyter_comm_response_received():
    return bool(_jupyter_config)


def _request_jupyter_config(timeout=2):
    # Heavily inspired by implementation of CaptureExecution in the
    if _dash_comm.kernel is None:
        # Not in jupyter setting
        return

    _send_jupyter_config_comm_request()

    # Get shell and kernel
    shell = IPython.get_ipython()
    kernel = shell.kernel

    # Start capturing shell events to replay later
    captured_events = []

    def capture_event(stream, ident, parent):
        captured_events.append((stream, ident, parent))

    kernel.shell_handlers['execute_request'] = capture_event

    # increment execution count to avoid collision error
    shell.execution_count += 1

    # Allow kernel to execute comms until we receive the jupyter configuration comm
    # response
    t0 = time.time()
    while True:
        if (time.time() - t0) > timeout:
            # give up
            raise EnvironmentError(
                "Unable to communicate with the jupyter_dash notebook or JupyterLab \n"
                "extension required to infer Jupyter configuration."
            )
        if _jupyter_comm_response_received():
            break

        if asyncio.iscoroutinefunction(kernel.do_one_iteration):
            loop = asyncio.get_event_loop()
            nest_asyncio.apply(loop)
            loop.run_until_complete(kernel.do_one_iteration())
        else:
            kernel.do_one_iteration()

    # Stop capturing events, revert the kernel shell handler to the default
    # execute_request behavior
    kernel.shell_handlers['execute_request'] = kernel.execute_request

    # Replay captured events
    # need to flush before replaying so messages show up in current cell not
    # replay cells
    sys.stdout.flush()
    sys.stderr.flush()

    for stream, ident, parent in captured_events:
        # Using kernel.set_parent is the key to getting the output of the replayed
        # events to show up in the cells that were captured instead of the current cell
        kernel.set_parent(ident, parent)
        kernel.execute_request(stream, ident, parent)
