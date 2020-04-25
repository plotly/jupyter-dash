import ipython_blocking
import IPython
from ipykernel.comm import Comm
import time


_jupyter_config = {}

_dash_comm = Comm(target_name='jupyter_dash')

# If running in an ipython kernel,
# request that the front end extension send us the notebook server base URL
if IPython.get_ipython() is not None:
    if _dash_comm.kernel is not None:
        _dash_comm.send({
            'type': 'base_url_request'
        })


@_dash_comm.on_msg
def _receive_message(msg):
    msg_data = msg.get('content').get('data')
    msg_type = msg_data.get('type', None)
    if msg_type == 'base_url_response':
        _jupyter_config.update(msg_data)


def _comm_response_received():
    return bool(_jupyter_config)


def _wait_for_comm_response(timeout=1):
    if _dash_comm.kernel is None:
        # Not in jupyter server setting
        return

    t0 = time.time()
    ctx = ipython_blocking.CaptureExecution(replay=True)
    with ctx:
        while True:
            if (time.time() - t0) > timeout:
                # give up
                break
            if _comm_response_received():
                break
            ctx.step()
