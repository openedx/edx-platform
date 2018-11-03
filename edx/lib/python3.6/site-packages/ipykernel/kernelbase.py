"""Base class for a kernel that talks to frontends over 0MQ."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

from datetime import datetime
from functools import partial
import itertools
import logging
from signal import signal, default_int_handler, SIGINT
import sys
import time
import uuid

try:
    # jupyter_client >= 5, use tz-aware now
    from jupyter_client.session import utcnow as now
except ImportError:
    # jupyter_client < 5, use local now()
    now = datetime.now

from tornado import ioloop
from tornado import gen
from tornado.queues import PriorityQueue, QueueEmpty
import zmq
from zmq.eventloop.zmqstream import ZMQStream

from traitlets.config.configurable import SingletonConfigurable
from IPython.core.error import StdinNotImplementedError
from ipython_genutils import py3compat
from ipython_genutils.py3compat import unicode_type, string_types
from ipykernel.jsonutil import json_clean
from traitlets import (
    Any, Instance, Float, Dict, List, Set, Integer, Unicode, Bool,
    observe, default
)

from jupyter_client.session import Session

from ._version import kernel_protocol_version

CONTROL_PRIORITY = 1
SHELL_PRIORITY = 10
ABORT_PRIORITY = 20


class Kernel(SingletonConfigurable):

    #---------------------------------------------------------------------------
    # Kernel interface
    #---------------------------------------------------------------------------

    # attribute to override with a GUI
    eventloop = Any(None)

    @observe('eventloop')
    def _update_eventloop(self, change):
        """schedule call to eventloop from IOLoop"""
        loop = ioloop.IOLoop.current()
        if change.new is not None:
            loop.add_callback(self.enter_eventloop)

    session = Instance(Session, allow_none=True)
    profile_dir = Instance('IPython.core.profiledir.ProfileDir', allow_none=True)
    shell_streams = List()
    control_stream = Instance(ZMQStream, allow_none=True)
    iopub_socket = Any()
    iopub_thread = Any()
    stdin_socket = Any()
    log = Instance(logging.Logger, allow_none=True)

    # identities:
    int_id = Integer(-1)
    ident = Unicode()

    @default('ident')
    def _default_ident(self):
        return unicode_type(uuid.uuid4())

    # This should be overridden by wrapper kernels that implement any real
    # language.
    language_info = {}

    # any links that should go in the help menu
    help_links = List()

    # Private interface

    _darwin_app_nap = Bool(True,
        help="""Whether to use appnope for compatibility with OS X App Nap.

        Only affects OS X >= 10.9.
        """
    ).tag(config=True)

    # track associations with current request
    _allow_stdin = Bool(False)
    _parent_header = Dict()
    _parent_ident = Any(b'')
    # Time to sleep after flushing the stdout/err buffers in each execute
    # cycle.  While this introduces a hard limit on the minimal latency of the
    # execute cycle, it helps prevent output synchronization problems for
    # clients.
    # Units are in seconds.  The minimum zmq latency on local host is probably
    # ~150 microseconds, set this to 500us for now.  We may need to increase it
    # a little if it's not enough after more interactive testing.
    _execute_sleep = Float(0.0005).tag(config=True)

    # Frequency of the kernel's event loop.
    # Units are in seconds, kernel subclasses for GUI toolkits may need to
    # adapt to milliseconds.
    _poll_interval = Float(0.01).tag(config=True)

    stop_on_error_timeout = Float(
        0.1,
        config=True,
        help="""time (in seconds) to wait for messages to arrive
        when aborting queued requests after an error.

        Requests that arrive within this window after an error
        will be cancelled.

        Increase in the event of unusually slow network
        causing significant delays,
        which can manifest as e.g. "Run all" in a notebook
        aborting some, but not all, messages after an error.
        """
    )

    # If the shutdown was requested over the network, we leave here the
    # necessary reply message so it can be sent by our registered atexit
    # handler.  This ensures that the reply is only sent to clients truly at
    # the end of our shutdown process (which happens after the underlying
    # IPython shell's own shutdown).
    _shutdown_message = None

    # This is a dict of port number that the kernel is listening on. It is set
    # by record_ports and used by connect_request.
    _recorded_ports = Dict()

    # set of aborted msg_ids
    aborted = Set()

    # Track execution count here. For IPython, we override this to use the
    # execution count we store in the shell.
    execution_count = 0

    msg_types = [
        'execute_request', 'complete_request',
        'inspect_request', 'history_request',
        'comm_info_request', 'kernel_info_request',
        'connect_request', 'shutdown_request',
        'is_complete_request',
        # deprecated:
        'apply_request',
    ]
    # add deprecated ipyparallel control messages
    control_msg_types = msg_types + ['clear_request', 'abort_request']

    def __init__(self, **kwargs):
        super(Kernel, self).__init__(**kwargs)
        # Build dict of handlers for message types
        self.shell_handlers = {}
        for msg_type in self.msg_types:
            self.shell_handlers[msg_type] = getattr(self, msg_type)

        self.control_handlers = {}
        for msg_type in self.control_msg_types:
            self.control_handlers[msg_type] = getattr(self, msg_type)

    @gen.coroutine
    def dispatch_control(self, msg):
        """dispatch control requests"""
        idents, msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.deserialize(msg, content=True, copy=False)
        except:
            self.log.error("Invalid Control Message", exc_info=True)
            return

        self.log.debug("Control received: %s", msg)

        # Set the parent message for side effects.
        self.set_parent(idents, msg)
        self._publish_status(u'busy')
        if self._aborting:
            self._send_abort_reply(self.control_stream, msg, idents)
            self._publish_status(u'idle')
            return

        header = msg['header']
        msg_type = header['msg_type']

        handler = self.control_handlers.get(msg_type, None)
        if handler is None:
            self.log.error("UNKNOWN CONTROL MESSAGE TYPE: %r", msg_type)
        else:
            try:
                yield gen.maybe_future(handler(self.control_stream, idents, msg))
            except Exception:
                self.log.error("Exception in control handler:", exc_info=True)

        sys.stdout.flush()
        sys.stderr.flush()
        self._publish_status(u'idle')

    def should_handle(self, stream, msg, idents):
        """Check whether a shell-channel message should be handled

        Allows subclasses to prevent handling of certain messages (e.g. aborted requests).
        """
        msg_id = msg['header']['msg_id']
        if msg_id in self.aborted:
            msg_type = msg['header']['msg_type']
            # is it safe to assume a msg_id will not be resubmitted?
            self.aborted.remove(msg_id)
            self._send_abort_reply(stream, msg, idents)
            return False
        return True

    @gen.coroutine
    def dispatch_shell(self, stream, msg):
        """dispatch shell requests"""
        # flush control requests first
        if self.control_stream:
            self.control_stream.flush()

        idents, msg = self.session.feed_identities(msg, copy=False)
        try:
            msg = self.session.deserialize(msg, content=True, copy=False)
        except:
            self.log.error("Invalid Message", exc_info=True)
            return

        # Set the parent message for side effects.
        self.set_parent(idents, msg)
        self._publish_status(u'busy')

        if self._aborting:
            self._send_abort_reply(stream, msg, idents)
            self._publish_status(u'idle')
            return

        msg_type = msg['header']['msg_type']

        # Print some info about this message and leave a '--->' marker, so it's
        # easier to trace visually the message chain when debugging.  Each
        # handler prints its message at the end.
        self.log.debug('\n*** MESSAGE TYPE:%s***', msg_type)
        self.log.debug('   Content: %s\n   --->\n   ', msg['content'])

        if not self.should_handle(stream, msg, idents):
            return

        handler = self.shell_handlers.get(msg_type, None)
        if handler is None:
            self.log.warning("Unknown message type: %r", msg_type)
        else:
            self.log.debug("%s: %s", msg_type, msg)
            try:
                self.pre_handler_hook()
            except Exception:
                self.log.debug("Unable to signal in pre_handler_hook:", exc_info=True)
            try:
                yield gen.maybe_future(handler(stream, idents, msg))
            except Exception:
                self.log.error("Exception in message handler:", exc_info=True)
            finally:
                try:
                    self.post_handler_hook()
                except Exception:
                    self.log.debug("Unable to signal in post_handler_hook:", exc_info=True)

        sys.stdout.flush()
        sys.stderr.flush()
        self._publish_status(u'idle')

    def pre_handler_hook(self):
        """Hook to execute before calling message handler"""
        # ensure default_int_handler during handler call
        self.saved_sigint_handler = signal(SIGINT, default_int_handler)

    def post_handler_hook(self):
        """Hook to execute after calling message handler"""
        signal(SIGINT, self.saved_sigint_handler)

    def enter_eventloop(self):
        """enter eventloop"""
        self.log.info("Entering eventloop %s", self.eventloop)
        # record handle, so we can check when this changes
        eventloop = self.eventloop
        def advance_eventloop():
            # check if eventloop changed:
            if self.eventloop is not eventloop:
                self.log.info("exiting eventloop %s", eventloop)
                return
            if self.msg_queue.qsize():
                self.log.debug("Delaying eventloop due to waiting messages")
                # still messages to process, make the eventloop wait
                schedule_next()
                return
            self.log.debug("Advancing eventloop %s", eventloop)
            try:
                eventloop(self)
            except KeyboardInterrupt:
                # Ctrl-C shouldn't crash the kernel
                self.log.error("KeyboardInterrupt caught in kernel")
                pass
            if self.eventloop is eventloop:
                # schedule advance again
                schedule_next()

        def schedule_next():
            """Schedule the next advance of the eventloop"""
            # flush the eventloop every so often,
            # giving us a chance to handle messages in the meantime
            self.log.debug("Scheduling eventloop advance")
            self.io_loop.call_later(1, advance_eventloop)

        # begin polling the eventloop
        schedule_next()

    @gen.coroutine
    def do_one_iteration(self):
        """Process a single shell message

        Any pending control messages will be flushed as well

        .. versionchanged:: 5
            This is now a coroutine
        """
        # flush messages off of shell streams into the message queue
        for stream in self.shell_streams:
            stream.flush()
        # process all messages higher priority than shell (control),
        # and at most one shell message per iteration
        priority = 0
        while priority is not None and priority < SHELL_PRIORITY:
            priority = yield self.process_one(wait=False)

    @gen.coroutine
    def process_one(self, wait=True):
        """Process one request

        Returns priority of the message handled.
        Returns None if no message was handled.
        """
        if wait:
            priority, t, dispatch, args = yield self.msg_queue.get()
        else:
            try:
                priority, t, dispatch, args = self.msg_queue.get_nowait()
            except QueueEmpty:
                return None
        yield gen.maybe_future(dispatch(*args))

    @gen.coroutine
    def dispatch_queue(self):
        """Coroutine to preserve order of message handling

        Ensures that only one message is processing at a time,
        even when the handler is async
        """

        while True:
            # receive the next message and handle it
            try:
                yield self.process_one()
            except Exception:
                self.log.exception("Error in message handler")

    _message_counter = Any(
        help="""Monotonic counter of messages

        Ensures messages of the same priority are handled in arrival order.
        """,
    )
    @default('_message_counter')
    def _message_counter_default(self):
        return itertools.count()

    def schedule_dispatch(self, priority, dispatch, *args):
        """schedule a message for dispatch"""
        idx = next(self._message_counter)

        self.msg_queue.put_nowait(
            (
                priority,
                idx,
                dispatch,
                args,
            )
        )
        # ensure the eventloop wakes up
        self.io_loop.add_callback(lambda: None)

    def start(self):
        """register dispatchers for streams"""
        self.io_loop = ioloop.IOLoop.current()
        self.msg_queue = PriorityQueue()
        self.io_loop.add_callback(self.dispatch_queue)


        if self.control_stream:
            self.control_stream.on_recv(
                partial(
                    self.schedule_dispatch,
                    CONTROL_PRIORITY,
                    self.dispatch_control,
                ),
                copy=False,
            )

        for s in self.shell_streams:
            if s is self.control_stream:
                continue
            s.on_recv(
                partial(
                    self.schedule_dispatch,
                    SHELL_PRIORITY,
                    self.dispatch_shell,
                    s,
                ),
                copy=False,
            )

        # publish idle status
        self._publish_status('starting')


    def record_ports(self, ports):
        """Record the ports that this kernel is using.

        The creator of the Kernel instance must call this methods if they
        want the :meth:`connect_request` method to return the port numbers.
        """
        self._recorded_ports = ports

    #---------------------------------------------------------------------------
    # Kernel request handlers
    #---------------------------------------------------------------------------

    def _publish_execute_input(self, code, parent, execution_count):
        """Publish the code request on the iopub stream."""

        self.session.send(self.iopub_socket, u'execute_input',
                            {u'code':code, u'execution_count': execution_count},
                            parent=parent, ident=self._topic('execute_input')
        )

    def _publish_status(self, status, parent=None):
        """send status (busy/idle) on IOPub"""
        self.session.send(self.iopub_socket,
                          u'status',
                          {u'execution_state': status},
                          parent=parent or self._parent_header,
                          ident=self._topic('status'),
                          )

    def set_parent(self, ident, parent):
        """Set the current parent_header

        Side effects (IOPub messages) and replies are associated with
        the request that caused them via the parent_header.

        The parent identity is used to route input_request messages
        on the stdin channel.
        """
        self._parent_ident = ident
        self._parent_header = parent

    def send_response(self, stream, msg_or_type, content=None, ident=None,
             buffers=None, track=False, header=None, metadata=None):
        """Send a response to the message we're currently processing.

        This accepts all the parameters of :meth:`jupyter_client.session.Session.send`
        except ``parent``.

        This relies on :meth:`set_parent` having been called for the current
        message.
        """
        return self.session.send(stream, msg_or_type, content, self._parent_header,
                                 ident, buffers, track, header, metadata)

    def init_metadata(self, parent):
        """Initialize metadata.

        Run at the beginning of execution requests.
        """
        # FIXME: `started` is part of ipyparallel
        # Remove for ipykernel 5.0
        return {
            'started': now(),
        }

    def finish_metadata(self, parent, metadata, reply_content):
        """Finish populating metadata.

        Run after completing an execution request.
        """
        return metadata

    @gen.coroutine
    def execute_request(self, stream, ident, parent):
        """handle an execute_request"""

        try:
            content = parent[u'content']
            code = py3compat.cast_unicode_py2(content[u'code'])
            silent = content[u'silent']
            store_history = content.get(u'store_history', not silent)
            user_expressions = content.get('user_expressions', {})
            allow_stdin = content.get('allow_stdin', False)
        except:
            self.log.error("Got bad msg: ")
            self.log.error("%s", parent)
            return

        stop_on_error = content.get('stop_on_error', True)

        metadata = self.init_metadata(parent)

        # Re-broadcast our input for the benefit of listening clients, and
        # start computing output
        if not silent:
            self.execution_count += 1
            self._publish_execute_input(code, parent, self.execution_count)

        reply_content = yield gen.maybe_future(
            self.do_execute(
                code, silent, store_history,
                user_expressions, allow_stdin,
            )
        )

        # Flush output before sending the reply.
        sys.stdout.flush()
        sys.stderr.flush()
        # FIXME: on rare occasions, the flush doesn't seem to make it to the
        # clients... This seems to mitigate the problem, but we definitely need
        # to better understand what's going on.
        if self._execute_sleep:
            time.sleep(self._execute_sleep)

        # Send the reply.
        reply_content = json_clean(reply_content)
        metadata = self.finish_metadata(parent, metadata, reply_content)

        reply_msg = self.session.send(stream, u'execute_reply',
                                      reply_content, parent, metadata=metadata,
                                      ident=ident)

        self.log.debug("%s", reply_msg)

        if not silent and reply_msg['content']['status'] == u'error' and stop_on_error:
            yield self._abort_queues()

    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False):
        """Execute user code. Must be overridden by subclasses.
        """
        raise NotImplementedError

    @gen.coroutine
    def complete_request(self, stream, ident, parent):
        content = parent['content']
        code = content['code']
        cursor_pos = content['cursor_pos']
        
        matches = yield gen.maybe_future(self.do_complete(code, cursor_pos))
        matches = json_clean(matches)
        completion_msg = self.session.send(stream, 'complete_reply',
                                           matches, parent, ident)

    def do_complete(self, code, cursor_pos):
        """Override in subclasses to find completions.
        """
        return {'matches' : [],
                'cursor_end' : cursor_pos,
                'cursor_start' : cursor_pos,
                'metadata' : {},
                'status' : 'ok'}

    @gen.coroutine
    def inspect_request(self, stream, ident, parent):
        content = parent['content']

        reply_content = yield gen.maybe_future(
            self.do_inspect(
                content['code'], content['cursor_pos'],
                content.get('detail_level', 0),
            )
        )
        # Before we send this object over, we scrub it for JSON usage
        reply_content = json_clean(reply_content)
        msg = self.session.send(stream, 'inspect_reply',
                                reply_content, parent, ident)
        self.log.debug("%s", msg)

    def do_inspect(self, code, cursor_pos, detail_level=0):
        """Override in subclasses to allow introspection.
        """
        return {'status': 'ok', 'data': {}, 'metadata': {}, 'found': False}

    @gen.coroutine
    def history_request(self, stream, ident, parent):
        content = parent['content']

        reply_content = yield gen.maybe_future(self.do_history(**content))

        reply_content = json_clean(reply_content)
        msg = self.session.send(stream, 'history_reply',
                                reply_content, parent, ident)
        self.log.debug("%s", msg)

    def do_history(self, hist_access_type, output, raw, session=None, start=None,
                   stop=None, n=None, pattern=None, unique=False):
        """Override in subclasses to access history.
        """
        return {'status': 'ok', 'history': []}

    def connect_request(self, stream, ident, parent):
        if self._recorded_ports is not None:
            content = self._recorded_ports.copy()
        else:
            content = {}
        content['status'] = 'ok'
        msg = self.session.send(stream, 'connect_reply',
                                content, parent, ident)
        self.log.debug("%s", msg)

    @property
    def kernel_info(self):
        return {
            'protocol_version': kernel_protocol_version,
            'implementation': self.implementation,
            'implementation_version': self.implementation_version,
            'language_info': self.language_info,
            'banner': self.banner,
            'help_links': self.help_links,
        }

    def kernel_info_request(self, stream, ident, parent):
        content = {'status': 'ok'}
        content.update(self.kernel_info)
        msg = self.session.send(stream, 'kernel_info_reply',
                                content, parent, ident)
        self.log.debug("%s", msg)

    def comm_info_request(self, stream, ident, parent):
        content = parent['content']
        target_name = content.get('target_name', None)

        # Should this be moved to ipkernel?
        if hasattr(self, 'comm_manager'):
            comms = {
                k: dict(target_name=v.target_name)
                for (k, v) in self.comm_manager.comms.items()
                if v.target_name == target_name or target_name is None
            }
        else:
            comms = {}
        reply_content = dict(comms=comms, status='ok')
        msg = self.session.send(stream, 'comm_info_reply',
                                reply_content, parent, ident)
        self.log.debug("%s", msg)

    @gen.coroutine
    def shutdown_request(self, stream, ident, parent):
        content = yield gen.maybe_future(self.do_shutdown(parent['content']['restart']))
        self.session.send(stream, u'shutdown_reply', content, parent, ident=ident)
        # same content, but different msg_id for broadcasting on IOPub
        self._shutdown_message = self.session.msg(u'shutdown_reply',
                                                  content, parent
        )

        self._at_shutdown()
        # call sys.exit after a short delay
        loop = ioloop.IOLoop.current()
        loop.add_timeout(time.time()+0.1, loop.stop)

    def do_shutdown(self, restart):
        """Override in subclasses to do things when the frontend shuts down the
        kernel.
        """
        return {'status': 'ok', 'restart': restart}

    @gen.coroutine
    def is_complete_request(self, stream, ident, parent):
        content = parent['content']
        code = content['code']

        reply_content = yield gen.maybe_future(self.do_is_complete(code))
        reply_content = json_clean(reply_content)
        reply_msg = self.session.send(stream, 'is_complete_reply',
                                      reply_content, parent, ident)
        self.log.debug("%s", reply_msg)

    def do_is_complete(self, code):
        """Override in subclasses to find completions.
        """
        return {'status' : 'unknown',
                }

    #---------------------------------------------------------------------------
    # Engine methods (DEPRECATED)
    #---------------------------------------------------------------------------

    def apply_request(self, stream, ident, parent):
        self.log.warning("apply_request is deprecated in kernel_base, moving to ipyparallel.")
        try:
            content = parent[u'content']
            bufs = parent[u'buffers']
            msg_id = parent['header']['msg_id']
        except:
            self.log.error("Got bad msg: %s", parent, exc_info=True)
            return

        md = self.init_metadata(parent)

        reply_content, result_buf = self.do_apply(content, bufs, msg_id, md)

        # flush i/o
        sys.stdout.flush()
        sys.stderr.flush()

        md = self.finish_metadata(parent, md, reply_content)

        self.session.send(stream, u'apply_reply', reply_content,
                    parent=parent, ident=ident,buffers=result_buf, metadata=md)

    def do_apply(self, content, bufs, msg_id, reply_metadata):
        """DEPRECATED"""
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # Control messages (DEPRECATED)
    #---------------------------------------------------------------------------

    def abort_request(self, stream, ident, parent):
        """abort a specific msg by id"""
        self.log.warning("abort_request is deprecated in kernel_base. It is only part of IPython parallel")
        msg_ids = parent['content'].get('msg_ids', None)
        if isinstance(msg_ids, string_types):
            msg_ids = [msg_ids]
        if not msg_ids:
            self._abort_queues()
        for mid in msg_ids:
            self.aborted.add(str(mid))

        content = dict(status='ok')
        reply_msg = self.session.send(stream, 'abort_reply', content=content,
                parent=parent, ident=ident)
        self.log.debug("%s", reply_msg)

    def clear_request(self, stream, idents, parent):
        """Clear our namespace."""
        self.log.warning("clear_request is deprecated in kernel_base. It is only part of IPython parallel")
        content = self.do_clear()
        self.session.send(stream, 'clear_reply', ident=idents, parent=parent,
                content = content)

    def do_clear(self):
        """DEPRECATED since 4.0.3"""
        raise NotImplementedError

    #---------------------------------------------------------------------------
    # Protected interface
    #---------------------------------------------------------------------------

    def _topic(self, topic):
        """prefixed topic for IOPub messages"""
        base = "kernel.%s" % self.ident

        return py3compat.cast_bytes("%s.%s" % (base, topic))

    _aborting = Bool(False)

    @gen.coroutine
    def _abort_queues(self):
        for stream in self.shell_streams:
            stream.flush()
        self._aborting = True

        self.schedule_dispatch(
            ABORT_PRIORITY,
            self._dispatch_abort,
        )

    @gen.coroutine
    def _dispatch_abort(self):
        self.log.info("Finishing abort")
        yield gen.sleep(self.stop_on_error_timeout)
        self._aborting = False

    @gen.coroutine
    def _send_abort_reply(self, stream, msg, idents):
        """Send a reply to an aborted request"""
        self.log.info("Aborting:")
        self.log.info("%s", msg)
        reply_type = msg['header']['msg_type'].rsplit('_', 1)[0] + '_reply'
        status = {'status': 'aborted'}
        md = {'engine': self.ident}
        md.update(status)
        self.session.send(
            stream, reply_type, metadata=md,
            content=status, parent=msg, ident=idents,
        )

    def _no_raw_input(self):
        """Raise StdinNotImplentedError if active frontend doesn't support
        stdin."""
        raise StdinNotImplementedError("raw_input was called, but this "
                                       "frontend does not support stdin.")

    def getpass(self, prompt='', stream=None):
        """Forward getpass to frontends

        Raises
        ------
        StdinNotImplentedError if active frontend doesn't support stdin.
        """
        if not self._allow_stdin:
            raise StdinNotImplementedError(
                "getpass was called, but this frontend does not support input requests."
            )
        if stream is not None:
            import warnings
            warnings.warn("The `stream` parameter of `getpass.getpass` will have no effect when using ipykernel",
                    UserWarning, stacklevel=2)
        return self._input_request(prompt,
            self._parent_ident,
            self._parent_header,
            password=True,
        )

    def raw_input(self, prompt=''):
        """Forward raw_input to frontends

        Raises
        ------
        StdinNotImplentedError if active frontend doesn't support stdin.
        """
        if not self._allow_stdin:
            raise StdinNotImplementedError(
                "raw_input was called, but this frontend does not support input requests."
            )
        return self._input_request(str(prompt),
            self._parent_ident,
            self._parent_header,
            password=False,
        )

    def _input_request(self, prompt, ident, parent, password=False):
        # Flush output before making the request.
        sys.stderr.flush()
        sys.stdout.flush()
        # flush the stdin socket, to purge stale replies
        while True:
            try:
                self.stdin_socket.recv_multipart(zmq.NOBLOCK)
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    break
                else:
                    raise

        # Send the input request.
        content = json_clean(dict(prompt=prompt, password=password))
        self.session.send(self.stdin_socket, u'input_request', content, parent,
                          ident=ident)

        # Await a response.
        while True:
            try:
                ident, reply = self.session.recv(self.stdin_socket, 0)
            except Exception:
                self.log.warning("Invalid Message:", exc_info=True)
            except KeyboardInterrupt:
                # re-raise KeyboardInterrupt, to truncate traceback
                raise KeyboardInterrupt
            else:
                break
        try:
            value = py3compat.unicode_to_str(reply['content']['value'])
        except:
            self.log.error("Bad input_reply: %s", parent)
            value = ''
        if value == '\x04':
            # EOF
            raise EOFError
        return value

    def _at_shutdown(self):
        """Actions taken at shutdown by the kernel, called by python's atexit.
        """
        if self._shutdown_message is not None:
            self.session.send(self.iopub_socket, self._shutdown_message, ident=self._topic('shutdown'))
            self.log.debug("%s", self._shutdown_message)
        [ s.flush(zmq.POLLOUT) for s in self.shell_streams ]
