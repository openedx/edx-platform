"""Test async/await integration"""

from distutils.version import LooseVersion as V
import sys

import pytest
import IPython


from .utils import execute, flush_channels, start_new_kernel, TIMEOUT
from .test_message_spec import validate_message


KC = KM = None


def setup():
    """start the global kernel (if it isn't running) and return its client"""
    global KM, KC
    KM, KC = start_new_kernel()
    flush_channels(KC)


def teardown():
    KC.stop_channels()
    KM.shutdown_kernel(now=True)


skip_without_async = pytest.mark.skipif(
    sys.version_info < (3, 5) or V(IPython.__version__) < V("7.0"),
    reason="IPython >=7 with async/await required",
)


@skip_without_async
def test_async_await():
    flush_channels(KC)
    msg_id, content = execute("import asyncio; await asyncio.sleep(0.1)", KC)
    assert content["status"] == "ok", content


@pytest.mark.parametrize("asynclib", ["asyncio", "trio", "curio"])
@skip_without_async
def test_async_interrupt(asynclib, request):
    try:
        __import__(asynclib)
    except ImportError:
        pytest.skip("Requires %s" % asynclib)
    request.addfinalizer(lambda: execute("%autoawait asyncio", KC))

    flush_channels(KC)
    msg_id, content = execute("%autoawait " + asynclib, KC)
    assert content["status"] == "ok", content

    flush_channels(KC)
    msg_id = KC.execute(
        "print('begin'); import {0}; await {0}.sleep(5)".format(asynclib)
    )
    busy = KC.get_iopub_msg(timeout=TIMEOUT)
    validate_message(busy, "status", msg_id)
    assert busy["content"]["execution_state"] == "busy"
    echo = KC.get_iopub_msg(timeout=TIMEOUT)
    validate_message(echo, "execute_input")
    stream = KC.get_iopub_msg(timeout=TIMEOUT)
    # wait for the stream output to be sure kernel is in the async block
    validate_message(stream, "stream")
    assert stream["content"]["text"] == "begin\n"

    KM.interrupt_kernel()
    reply = KC.get_shell_msg()["content"]
    assert reply["status"] == "error", reply
    assert reply["ename"] in {"CancelledError", "KeyboardInterrupt"}

    flush_channels(KC)
