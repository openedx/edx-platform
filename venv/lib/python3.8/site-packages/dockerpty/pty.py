# dockerpty: pty.py
#
# Copyright 2014 Chris Corbyn <chris@w3style.co.uk>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import signal
import warnings
from ssl import SSLError

import dockerpty.io as io
import dockerpty.tty as tty


class WINCHHandler(object):
    """
    WINCH Signal handler to keep the PTY correctly sized.
    """

    def __init__(self, pty):
        """
        Initialize a new WINCH handler for the given PTY.

        Initializing a handler has no immediate side-effects. The `start()`
        method must be invoked for the signals to be trapped.
        """

        self.pty = pty
        self.original_handler = None

    def __enter__(self):
        """
        Invoked on entering a `with` block.
        """

        self.start()
        return self

    def __exit__(self, *_):
        """
        Invoked on exiting a `with` block.
        """

        self.stop()

    def start(self):
        """
        Start trapping WINCH signals and resizing the PTY.

        This method saves the previous WINCH handler so it can be restored on
        `stop()`.
        """

        def handle(signum, frame):
            if signum == signal.SIGWINCH:
                self.pty.resize()

        self.original_handler = signal.signal(signal.SIGWINCH, handle)

    def stop(self):
        """
        Stop trapping WINCH signals and restore the previous WINCH handler.
        """

        if self.original_handler is not None:
            signal.signal(signal.SIGWINCH, self.original_handler)


class Operation(object):

    def israw(self, **kwargs):
        """
        are we dealing with a tty or not?
        """
        raise NotImplementedError()

    def start(self, **kwargs):
        """
        start execution
        """
        raise NotImplementedError()

    def resize(self, height, width, **kwargs):
        """
        if we have terminal, resize it
        """
        raise NotImplementedError()

    def sockets(self):
        """Return sockets for streams."""
        raise NotImplementedError()


class RunOperation(Operation):
    """
    class for handling `docker run`-like command
    """

    def __init__(self, client, container, interactive=True, stdout=None, stderr=None, stdin=None, logs=None):
        """
        Initialize the PTY using the docker.Client instance and container dict.
        """

        if logs is None:
            warnings.warn("The default behaviour of dockerpty is changing. Please add logs=1 to your dockerpty.start call to maintain existing behaviour. See https://github.com/d11wtq/dockerpty/issues/51 for details.", DeprecationWarning)
            logs = 1

        self.client = client
        self.container = container
        self.raw = None
        self.interactive = interactive
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.stdin = stdin or sys.stdin
        self.logs = logs

    def start(self, sockets=None, **kwargs):
        """
        Present the PTY of the container inside the current process.

        This will take over the current process' TTY until the container's PTY
        is closed.
        """

        pty_stdin, pty_stdout, pty_stderr = sockets or self.sockets()
        pumps = []

        if pty_stdin and self.interactive:
            pumps.append(io.Pump(io.Stream(self.stdin), pty_stdin, wait_for_output=False))

        if pty_stdout:
            pumps.append(io.Pump(pty_stdout, io.Stream(self.stdout), propagate_close=False))

        if pty_stderr:
            pumps.append(io.Pump(pty_stderr, io.Stream(self.stderr), propagate_close=False))

        if not self._container_info()['State']['Running']:
            self.client.start(self.container, **kwargs)

        return pumps

    def israw(self, **kwargs):
        """
        Returns True if the PTY should operate in raw mode.

        If the container was not started with tty=True, this will return False.
        """

        if self.raw is None:
            info = self._container_info()
            self.raw = self.stdout.isatty() and info['Config']['Tty']

        return self.raw

    def sockets(self):
        """
        Returns a tuple of sockets connected to the pty (stdin,stdout,stderr).

        If any of the sockets are not attached in the container, `None` is
        returned in the tuple.
        """

        info = self._container_info()

        def attach_socket(key):
            if info['Config']['Attach{0}'.format(key.capitalize())]:
                socket = self.client.attach_socket(
                    self.container,
                    {key: 1, 'stream': 1, 'logs': self.logs},
                )
                stream = io.Stream(socket)

                if info['Config']['Tty']:
                    return stream
                else:
                    return io.Demuxer(stream)
            else:
                return None

        return map(attach_socket, ('stdin', 'stdout', 'stderr'))

    def resize(self, height, width, **kwargs):
        """
        resize pty within container
        """
        self.client.resize(self.container, height=height, width=width)

    def _container_info(self):
        """
        Thin wrapper around client.inspect_container().
        """

        return self.client.inspect_container(self.container)


def exec_create(client, container, command, interactive=True):
    exec_id = client.exec_create(container, command, tty=interactive, stdin=interactive)
    return exec_id


class ExecOperation(Operation):
    """
    class for handling `docker exec`-like command
    """

    def __init__(self, client, exec_id, interactive=True, stdout=None, stderr=None, stdin=None):
        self.exec_id = exec_id
        self.client = client
        self.raw = None
        self.interactive = interactive
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.stdin = stdin or sys.stdin
        self._info = None

    def start(self, sockets=None, **kwargs):
        """
        start execution
        """
        stream = sockets or self.sockets()
        pumps = []

        if self.interactive:
            pumps.append(io.Pump(io.Stream(self.stdin), stream, wait_for_output=False))

        pumps.append(io.Pump(stream, io.Stream(self.stdout), propagate_close=False))
        # FIXME: since exec_start returns a single socket, how do we
        #        distinguish between stdout and stderr?
        # pumps.append(io.Pump(stream, io.Stream(self.stderr), propagate_close=False))

        return pumps

    def israw(self, **kwargs):
        """
        Returns True if the PTY should operate in raw mode.

        If the exec was not started with tty=True, this will return False.
        """

        if self.raw is None:
            self.raw = self.stdout.isatty() and self.is_process_tty()

        return self.raw

    def sockets(self):
        """
        Return a single socket which is processing all I/O to exec
        """
        socket = self.client.exec_start(self.exec_id, socket=True, tty=self.interactive)
        stream = io.Stream(socket)
        if self.is_process_tty():
            return stream
        else:
            return io.Demuxer(stream)

    def resize(self, height, width, **kwargs):
        """
        resize pty of an execed process
        """
        self.client.exec_resize(self.exec_id, height=height, width=width)

    def is_process_tty(self):
        """
        does execed process have allocated tty?
        """
        return self._exec_info()["ProcessConfig"]["tty"]

    def _exec_info(self):
        """
        Caching wrapper around client.exec_inspect
        """
        if self._info is None:
            self._info = self.client.exec_inspect(self.exec_id)
        return self._info


class PseudoTerminal(object):
    """
    Wraps the pseudo-TTY (PTY) allocated to a docker container.

    The PTY is managed via the current process' TTY until it is closed.

    Example:

        import docker
        from dockerpty import PseudoTerminal

        client = docker.Client()
        container = client.create_container(
            image='busybox:latest',
            stdin_open=True,
            tty=True,
            command='/bin/sh',
        )

        # hijacks the current tty until the pty is closed
        PseudoTerminal(client, container).start()

    Care is taken to ensure all file descriptors are restored on exit. For
    example, you can attach to a running container from within a Python REPL
    and when the container exits, the user will be returned to the Python REPL
    without adverse effects.
    """

    def __init__(self, client, operation):
        """
        Initialize the PTY using the docker.Client instance and container dict.
        """

        self.client = client
        self.operation = operation

    def sockets(self):
        return self.operation.sockets()

    def start(self, sockets=None):
        pumps = self.operation.start(sockets=sockets)

        flags = [p.set_blocking(False) for p in pumps]

        try:
            with WINCHHandler(self):
                self._hijack_tty(pumps)
        finally:
            if flags:
                for (pump, flag) in zip(pumps, flags):
                    io.set_blocking(pump, flag)

    def resize(self, size=None):
        """
        Resize the container's PTY.

        If `size` is not None, it must be a tuple of (height,width), otherwise
        it will be determined by the size of the current TTY.
        """

        if not self.operation.israw():
            return

        size = size or tty.size(self.operation.stdout)

        if size is not None:
            rows, cols = size
            try:
                self.operation.resize(height=rows, width=cols)
            except IOError:  # Container already exited
                pass

    def _hijack_tty(self, pumps):
        with tty.Terminal(self.operation.stdin, raw=self.operation.israw()):
            self.resize()
            while True:
                read_pumps = [p for p in pumps if not p.eof]
                write_streams = [p.to_stream for p in pumps if p.to_stream.needs_write()]

                read_ready, write_ready = io.select(read_pumps, write_streams, timeout=60)
                try:
                    for write_stream in write_ready:
                        write_stream.do_write()

                    for pump in read_ready:
                        pump.flush()

                    if all([p.is_done() for p in pumps]):
                        break

                except SSLError as e:
                    if 'The operation did not complete' not in e.strerror:
                        raise e
