#!/usr/bin/python
from __future__ import unicode_literals

import logging
import re
import socket
import threading
import time
from timeit import default_timer

from .. import core

# Roughly, have to keep to what works as a file name.
# We also remove periods, so labels can be distinguished.
_INVALID_GRAPHITE_CHARS = re.compile(r"[^a-zA-Z0-9_-]")


def _sanitize(s):
    return _INVALID_GRAPHITE_CHARS.sub('_', s)


class _RegularPush(threading.Thread):
    def __init__(self, pusher, interval, prefix):
        super(_RegularPush, self).__init__()
        self._pusher = pusher
        self._interval = interval
        self._prefix = prefix

    def run(self):
        wait_until = default_timer()
        while True:
            while True:
                now = default_timer()
                if now >= wait_until:
                    # May need to skip some pushes.
                    while wait_until < now:
                        wait_until += self._interval
                    break
                # time.sleep can return early.
                time.sleep(wait_until - now)
            try:
                self._pusher.push(prefix=self._prefix)
            except IOError:
                logging.exception("Push failed")


class GraphiteBridge(object):
    def __init__(self, address, registry=core.REGISTRY, timeout_seconds=30, _timer=time.time):
        self._address = address
        self._registry = registry
        self._timeout = timeout_seconds
        self._timer = _timer

    def push(self, prefix=''):
        now = int(self._timer())
        output = []

        prefixstr = ''
        if prefix:
            prefixstr = prefix + '.'

        for metric in self._registry.collect():
            for s in metric.samples:
                if s.labels:
                    labelstr = '.' + '.'.join(
                        ['{0}.{1}'.format(
                            _sanitize(k), _sanitize(v))
                            for k, v in sorted(s.labels.items())])
                else:
                    labelstr = ''
                output.append('{0}{1}{2} {3} {4}\n'.format(
                    prefixstr, _sanitize(s.name), labelstr, float(s.value), now))

        conn = socket.create_connection(self._address, self._timeout)
        conn.sendall(''.join(output).encode('ascii'))
        conn.close()

    def start(self, interval=60.0, prefix=''):
        t = _RegularPush(self, interval, prefix)
        t.daemon = True
        t.start()
