"""Test IO capturing functionality"""

import io

import zmq

from jupyter_client.session import Session
from ipykernel.iostream import IOPubThread, OutStream

import nose.tools as nt

def test_io_api():
    """Test that wrapped stdout has the same API as a normal TextIO object"""
    session = Session()
    ctx = zmq.Context()
    pub = ctx.socket(zmq.PUB)
    thread = IOPubThread(pub)
    thread.start()

    stream = OutStream(session, thread, 'stdout')

    # cleanup unused zmq objects before we start testing
    thread.stop()
    thread.close()
    ctx.term()

    assert stream.errors is None
    assert not stream.isatty()
    with nt.assert_raises(io.UnsupportedOperation):
        stream.detach()
    with nt.assert_raises(io.UnsupportedOperation):
        next(stream)
    with nt.assert_raises(io.UnsupportedOperation):
        stream.read()
    with nt.assert_raises(io.UnsupportedOperation):
        stream.readline()
    with nt.assert_raises(io.UnsupportedOperation):
        stream.seek()
    with nt.assert_raises(io.UnsupportedOperation):
        stream.tell()

    