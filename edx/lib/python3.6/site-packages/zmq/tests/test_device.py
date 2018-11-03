# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.

import time

import zmq
from zmq import devices
from zmq.tests import BaseZMQTestCase, SkipTest, have_gevent, GreenTest, PYPY
from zmq.utils.strtypes import (bytes,unicode,basestring)

if PYPY:
    # cleanup of shared Context doesn't work on PyPy
    devices.Device.context_factory = zmq.Context

class TestDevice(BaseZMQTestCase):
    
    def test_device_types(self):
        for devtype in (zmq.STREAMER, zmq.FORWARDER, zmq.QUEUE):
            dev = devices.Device(devtype, zmq.PAIR, zmq.PAIR)
            self.assertEqual(dev.device_type, devtype)
            del dev
    
    def test_device_attributes(self):
        dev = devices.Device(zmq.QUEUE, zmq.SUB, zmq.PUB)
        self.assertEqual(dev.in_type, zmq.SUB)
        self.assertEqual(dev.out_type, zmq.PUB)
        self.assertEqual(dev.device_type, zmq.QUEUE)
        self.assertEqual(dev.daemon, True)
        del dev
    
    def test_single_socket_forwarder_connect(self):
        if zmq.zmq_version() in ('4.1.1', '4.0.6'):
            raise SkipTest("libzmq-%s broke single-socket devices" % zmq.zmq_version())
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        req = self.context.socket(zmq.REQ)
        port = req.bind_to_random_port('tcp://127.0.0.1')
        dev.connect_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello'
        req.send(msg)
        self.assertEqual(msg, self.recv(req))
        del dev
        req.close()
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        req = self.context.socket(zmq.REQ)
        port = req.bind_to_random_port('tcp://127.0.0.1')
        dev.connect_out('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello again'
        req.send(msg)
        self.assertEqual(msg, self.recv(req))
        del dev
        req.close()
        
    def test_single_socket_forwarder_bind(self):
        if zmq.zmq_version() in ('4.1.1', '4.0.6'):
            raise SkipTest("libzmq-%s broke single-socket devices" % zmq.zmq_version())
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        # select random port:
        binder = self.context.socket(zmq.REQ)
        port = binder.bind_to_random_port('tcp://127.0.0.1')
        binder.close()
        time.sleep(0.1)
        req = self.context.socket(zmq.REQ)
        req.connect('tcp://127.0.0.1:%i'%port)
        dev.bind_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello'
        req.send(msg)
        self.assertEqual(msg, self.recv(req))
        del dev
        req.close()
        dev = devices.ThreadDevice(zmq.QUEUE, zmq.REP, -1)
        # select random port:
        binder = self.context.socket(zmq.REQ)
        port = binder.bind_to_random_port('tcp://127.0.0.1')
        binder.close()
        time.sleep(0.1)
        req = self.context.socket(zmq.REQ)
        req.connect('tcp://127.0.0.1:%i'%port)
        dev.bind_in('tcp://127.0.0.1:%i'%port)
        dev.start()
        time.sleep(.25)
        msg = b'hello again'
        req.send(msg)
        self.assertEqual(msg, self.recv(req))
        del dev
        req.close()
    
    def test_proxy(self):
        if zmq.zmq_version_info() < (3,2):
            raise SkipTest("Proxies only in libzmq >= 3")
        dev = devices.ThreadProxy(zmq.PULL, zmq.PUSH, zmq.PUSH)
        binder = self.context.socket(zmq.REQ)
        iface = 'tcp://127.0.0.1'
        port = binder.bind_to_random_port(iface)
        port2 = binder.bind_to_random_port(iface)
        port3 = binder.bind_to_random_port(iface)
        binder.close()
        time.sleep(0.1)
        dev.bind_in("%s:%i" % (iface, port))
        dev.bind_out("%s:%i" % (iface, port2))
        dev.bind_mon("%s:%i" % (iface, port3))
        dev.start()
        time.sleep(0.25)
        msg = b'hello'
        push = self.context.socket(zmq.PUSH)
        push.connect("%s:%i" % (iface, port))
        pull = self.context.socket(zmq.PULL)
        pull.connect("%s:%i" % (iface, port2))
        mon = self.context.socket(zmq.PULL)
        mon.connect("%s:%i" % (iface, port3))
        push.send(msg)
        self.sockets.extend([push, pull, mon])
        self.assertEqual(msg, self.recv(pull))
        self.assertEqual(msg, self.recv(mon))

if have_gevent:
    import gevent
    import zmq.green
    
    class TestDeviceGreen(GreenTest, BaseZMQTestCase):
        
        def test_green_device(self):
            rep = self.context.socket(zmq.REP)
            req = self.context.socket(zmq.REQ)
            self.sockets.extend([req, rep])
            port = rep.bind_to_random_port('tcp://127.0.0.1')
            g = gevent.spawn(zmq.green.device, zmq.QUEUE, rep, rep)
            req.connect('tcp://127.0.0.1:%i' % port)
            req.send(b'hi')
            timeout = gevent.Timeout(3)
            timeout.start()
            receiver = gevent.spawn(req.recv)
            self.assertEqual(receiver.get(2), b'hi')
            timeout.cancel()
            g.kill(block=True)
            
