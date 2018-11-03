"""Test eventloop integration"""

import sys

import pytest
import tornado

from .utils import flush_channels, start_new_kernel, execute

KC = KM = None


def setup():
    """start the global kernel (if it isn't running) and return its client"""
    global KM, KC
    KM, KC = start_new_kernel()
    flush_channels(KC)


def teardown():
    KC.stop_channels()
    KM.shutdown_kernel(now=True)


async_code = """
from ipykernel.tests._asyncio import async_func
async_func()
"""


@pytest.mark.skipif(sys.version_info < (3, 5), reason="async/await syntax required")
@pytest.mark.skipif(tornado.version_info < (5,), reason="only relevant on tornado 5")
def test_asyncio_interrupt():
    flush_channels(KC)
    msg_id, content = execute('%gui asyncio', KC)
    assert content['status'] == 'ok', content

    flush_channels(KC)
    msg_id, content = execute(async_code, KC)
    assert content['status'] == 'ok', content

    KM.interrupt_kernel()

    flush_channels(KC)
    msg_id, content = execute(async_code, KC)
    assert content['status'] == 'ok'
