"""test IPython.embed_kernel()"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import sys
import time

from contextlib import contextmanager
from subprocess import Popen, PIPE

from jupyter_client import BlockingKernelClient
from jupyter_core import paths
from ipython_genutils import py3compat
from ipython_genutils.py3compat import unicode_type


SETUP_TIMEOUT = 60
TIMEOUT = 15


@contextmanager
def setup_kernel(cmd):
    """start an embedded kernel in a subprocess, and wait for it to be ready

    Returns
    -------
    kernel_manager: connected KernelManager instance
    """
    kernel = Popen([sys.executable, '-c', cmd], stdout=PIPE, stderr=PIPE)
    connection_file = os.path.join(
        paths.jupyter_runtime_dir(),
        'kernel-%i.json' % kernel.pid,
    )
    # wait for connection file to exist, timeout after 5s
    tic = time.time()
    while not os.path.exists(connection_file) \
        and kernel.poll() is None \
        and time.time() < tic + SETUP_TIMEOUT:
        time.sleep(0.1)

    if kernel.poll() is not None:
        o,e = kernel.communicate()
        e = py3compat.cast_unicode(e)
        raise IOError("Kernel failed to start:\n%s" % e)

    if not os.path.exists(connection_file):
        if kernel.poll() is None:
            kernel.terminate()
        raise IOError("Connection file %r never arrived" % connection_file)

    client = BlockingKernelClient(connection_file=connection_file)
    client.load_connection_file()
    client.start_channels()
    client.wait_for_ready()

    try:
        yield client
    finally:
        client.stop_channels()
        kernel.terminate()

def test_embed_kernel_basic():
    """IPython.embed_kernel() is basically functional"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'def go():',
        '    a=5',
        '    b="hi there"',
        '    embed_kernel()',
        'go()',
        '',
    ])

    with setup_kernel(cmd) as client:
        # oinfo a (int)
        msg_id = client.inspect('a')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['found']

        msg_id = client.execute("c=a*2")
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['status'] == u'ok'

        # oinfo c (should be 10)
        msg_id = client.inspect('c')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['found']
        text = content['data']['text/plain']
        assert '10' in text

def test_embed_kernel_namespace():
    """IPython.embed_kernel() inherits calling namespace"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'def go():',
        '    a=5',
        '    b="hi there"',
        '    embed_kernel()',
        'go()',
        '',
    ])

    with setup_kernel(cmd) as client:
        # oinfo a (int)
        msg_id = client.inspect('a')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['found']
        text = content['data']['text/plain']
        assert u'5' in text

        # oinfo b (str)
        msg_id = client.inspect('b')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert content['found']
        text = content['data']['text/plain']
        assert u'hi there' in text

        # oinfo c (undefined)
        msg_id = client.inspect('c')
        msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
        content = msg['content']
        assert not content['found']

def test_embed_kernel_reentrant():
    """IPython.embed_kernel() can be called multiple times"""
    cmd = '\n'.join([
        'from IPython import embed_kernel',
        'count = 0',
        'def go():',
        '    global count',
        '    embed_kernel()',
        '    count = count + 1',
        '',
        'while True:'
        '    go()',
        '',
    ])

    with setup_kernel(cmd) as client:
        for i in range(5):
            msg_id = client.inspect('count')
            msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
            content = msg['content']
            assert content['found']
            text = content['data']['text/plain']
            assert unicode_type(i) in text

            # exit from embed_kernel
            client.execute("get_ipython().exit_now = True")
            msg = client.get_shell_msg(block=True, timeout=TIMEOUT)
            time.sleep(0.2)
