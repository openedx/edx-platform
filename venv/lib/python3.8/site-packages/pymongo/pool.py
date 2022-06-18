# Copyright 2011-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you
# may not use this file except in compliance with the License.  You
# may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

import contextlib
import copy
import os
import platform
import socket
import sys
import threading
import collections
import weakref

from pymongo.ssl_support import (
    SSLError as _SSLError,
    HAS_SNI as _HAVE_SNI,
    IPADDR_SAFE as _IPADDR_SAFE)

from bson import DEFAULT_CODEC_OPTIONS
from bson.py3compat import imap, itervalues, _unicode
from bson.son import SON
from pymongo import auth, helpers, thread_util, __version__
from pymongo.client_session import _validate_session_write_concern
from pymongo.common import (MAX_BSON_SIZE,
                            MAX_IDLE_TIME_SEC,
                            MAX_MESSAGE_SIZE,
                            MAX_POOL_SIZE,
                            MAX_WIRE_VERSION,
                            MAX_WRITE_BATCH_SIZE,
                            MIN_POOL_SIZE,
                            ORDERED_TYPES,
                            WAIT_QUEUE_TIMEOUT)
from pymongo.errors import (AutoReconnect,
                            CertificateError,
                            ConnectionFailure,
                            ConfigurationError,
                            InvalidOperation,
                            DocumentTooLarge,
                            NetworkTimeout,
                            NotPrimaryError,
                            OperationFailure,
                            PyMongoError)
from pymongo.hello_compat import HelloCompat
from pymongo._ipaddress import is_ip_address
from pymongo.ismaster import IsMaster
from pymongo.monotonic import time as _time
from pymongo.monitoring import (ConnectionCheckOutFailedReason,
                                ConnectionClosedReason)
from pymongo.network import (command,
                             receive_message)
from pymongo.read_preferences import ReadPreference
from pymongo.server_api import _add_to_command
from pymongo.server_type import SERVER_TYPE
from pymongo.socket_checker import SocketChecker
# Always use our backport so we always have support for IP address matching
from pymongo.ssl_match_hostname import match_hostname

try:
    from fcntl import fcntl, F_GETFD, F_SETFD, FD_CLOEXEC
    def _set_non_inheritable_non_atomic(fd):
        """Set the close-on-exec flag on the given file descriptor."""
        flags = fcntl(fd, F_GETFD)
        fcntl(fd, F_SETFD, flags | FD_CLOEXEC)
except ImportError:
    # Windows, various platforms we don't claim to support
    # (Jython, IronPython, ...), systems that don't provide
    # everything we need from fcntl, etc.
    def _set_non_inheritable_non_atomic(dummy):
        """Dummy function for platforms that don't provide fcntl."""
        pass

_MAX_TCP_KEEPIDLE = 120
_MAX_TCP_KEEPINTVL = 10
_MAX_TCP_KEEPCNT = 9

if sys.platform == 'win32':
    try:
        import _winreg as winreg
    except ImportError:
        import winreg

    def _query(key, name, default):
        try:
            value, _ = winreg.QueryValueEx(key, name)
            # Ensure the value is a number or raise ValueError.
            return int(value)
        except (OSError, ValueError):
            # QueryValueEx raises OSError when the key does not exist (i.e.
            # the system is using the Windows default value).
            return default

    try:
        with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters") as key:
            _WINDOWS_TCP_IDLE_MS = _query(key, "KeepAliveTime", 7200000)
            _WINDOWS_TCP_INTERVAL_MS = _query(key, "KeepAliveInterval", 1000)
    except OSError:
        # We could not check the default values because winreg.OpenKey failed.
        # Assume the system is using the default values.
        _WINDOWS_TCP_IDLE_MS = 7200000
        _WINDOWS_TCP_INTERVAL_MS = 1000

    def _set_keepalive_times(sock):
        idle_ms = min(_WINDOWS_TCP_IDLE_MS, _MAX_TCP_KEEPIDLE * 1000)
        interval_ms = min(_WINDOWS_TCP_INTERVAL_MS,
                          _MAX_TCP_KEEPINTVL * 1000)
        if (idle_ms < _WINDOWS_TCP_IDLE_MS or
                interval_ms < _WINDOWS_TCP_INTERVAL_MS):
            sock.ioctl(socket.SIO_KEEPALIVE_VALS,
                       (1, idle_ms, interval_ms))
else:
    def _set_tcp_option(sock, tcp_option, max_value):
        if hasattr(socket, tcp_option):
            sockopt = getattr(socket, tcp_option)
            try:
                # PYTHON-1350 - NetBSD doesn't implement getsockopt for
                # TCP_KEEPIDLE and friends. Don't attempt to set the
                # values there.
                default = sock.getsockopt(socket.IPPROTO_TCP, sockopt)
                if default > max_value:
                    sock.setsockopt(socket.IPPROTO_TCP, sockopt, max_value)
            except socket.error:
                pass

    def _set_keepalive_times(sock):
        _set_tcp_option(sock, 'TCP_KEEPIDLE', _MAX_TCP_KEEPIDLE)
        _set_tcp_option(sock, 'TCP_KEEPINTVL', _MAX_TCP_KEEPINTVL)
        _set_tcp_option(sock, 'TCP_KEEPCNT', _MAX_TCP_KEEPCNT)

_METADATA = SON([
    ('driver', SON([('name', 'PyMongo'), ('version', __version__)])),
])

if sys.platform.startswith('linux'):
    # platform.linux_distribution was deprecated in Python 3.5.
    if sys.version_info[:2] < (3, 5):
        # Distro name and version (e.g. Ubuntu 16.04 xenial)
        _name = ' '.join([part for part in
                          platform.linux_distribution() if part])
    else:
        _name = platform.system()
    _METADATA['os'] = SON([
        ('type', platform.system()),
        ('name', _name),
        ('architecture', platform.machine()),
        # Kernel version (e.g. 4.4.0-17-generic).
        ('version', platform.release())
    ])
elif sys.platform == 'darwin':
    _METADATA['os'] = SON([
        ('type', platform.system()),
        ('name', platform.system()),
        ('architecture', platform.machine()),
        # (mac|i|tv)OS(X) version (e.g. 10.11.6) instead of darwin
        # kernel version.
        ('version', platform.mac_ver()[0])
    ])
elif sys.platform == 'win32':
    _METADATA['os'] = SON([
        ('type', platform.system()),
        # "Windows XP", "Windows 7", "Windows 10", etc.
        ('name', ' '.join((platform.system(), platform.release()))),
        ('architecture', platform.machine()),
        # Windows patch level (e.g. 5.1.2600-SP3)
        ('version', '-'.join(platform.win32_ver()[1:3]))
    ])
elif sys.platform.startswith('java'):
    _name, _ver, _arch = platform.java_ver()[-1]
    _METADATA['os'] = SON([
        # Linux, Windows 7, Mac OS X, etc.
        ('type', _name),
        ('name', _name),
        # x86, x86_64, AMD64, etc.
        ('architecture', _arch),
        # Linux kernel version, OSX version, etc.
        ('version', _ver)
    ])
else:
    # Get potential alias (e.g. SunOS 5.11 becomes Solaris 2.11)
    _aliased = platform.system_alias(
        platform.system(), platform.release(), platform.version())
    _METADATA['os'] = SON([
        ('type', platform.system()),
        ('name', ' '.join([part for part in _aliased[:2] if part])),
        ('architecture', platform.machine()),
        ('version', _aliased[2])
    ])

if platform.python_implementation().startswith('PyPy'):
    _METADATA['platform'] = ' '.join(
        (platform.python_implementation(),
         '.'.join(imap(str, sys.pypy_version_info)),
         '(Python %s)' % '.'.join(imap(str, sys.version_info))))
elif sys.platform.startswith('java'):
    _METADATA['platform'] = ' '.join(
        (platform.python_implementation(),
         '.'.join(imap(str, sys.version_info)),
         '(%s)' % ' '.join((platform.system(), platform.release()))))
else:
    _METADATA['platform'] = ' '.join(
        (platform.python_implementation(),
         '.'.join(imap(str, sys.version_info))))


# If the first getaddrinfo call of this interpreter's life is on a thread,
# while the main thread holds the import lock, getaddrinfo deadlocks trying
# to import the IDNA codec. Import it here, where presumably we're on the
# main thread, to avoid the deadlock. See PYTHON-607.
u'foo'.encode('idna')

# Remove after PYTHON-2712
_MOCK_SERVICE_ID = False


def _raise_connection_failure(address, error, msg_prefix=None):
    """Convert a socket.error to ConnectionFailure and raise it."""
    host, port = address
    # If connecting to a Unix socket, port will be None.
    if port is not None:
        msg = '%s:%d: %s' % (host, port, error)
    else:
        msg = '%s: %s' % (host, error)
    if msg_prefix:
        msg = msg_prefix + msg
    if isinstance(error, socket.timeout):
        raise NetworkTimeout(msg)
    elif isinstance(error, _SSLError) and 'timed out' in str(error):
        # CPython 2.7 and PyPy 2.x do not distinguish network
        # timeouts from other SSLErrors (https://bugs.python.org/issue10272).
        # Luckily, we can work around this limitation because the phrase
        # 'timed out' appears in all the timeout related SSLErrors raised
        # on the above platforms.
        raise NetworkTimeout(msg)
    else:
        raise AutoReconnect(msg)


class PoolOptions(object):

    __slots__ = ('__max_pool_size', '__min_pool_size',
                 '__max_idle_time_seconds',
                 '__connect_timeout', '__socket_timeout',
                 '__wait_queue_timeout', '__wait_queue_multiple',
                 '__ssl_context', '__ssl_match_hostname', '__socket_keepalive',
                 '__event_listeners', '__appname', '__driver', '__metadata',
                 '__compression_settings', '__server_api', '__load_balanced')

    def __init__(self, max_pool_size=MAX_POOL_SIZE,
                 min_pool_size=MIN_POOL_SIZE,
                 max_idle_time_seconds=MAX_IDLE_TIME_SEC, connect_timeout=None,
                 socket_timeout=None, wait_queue_timeout=WAIT_QUEUE_TIMEOUT,
                 wait_queue_multiple=None, ssl_context=None,
                 ssl_match_hostname=True, socket_keepalive=True,
                 event_listeners=None, appname=None, driver=None,
                 compression_settings=None, server_api=None,
                 load_balanced=None):
        self.__max_pool_size = max_pool_size
        self.__min_pool_size = min_pool_size
        self.__max_idle_time_seconds = max_idle_time_seconds
        self.__connect_timeout = connect_timeout
        self.__socket_timeout = socket_timeout
        self.__wait_queue_timeout = wait_queue_timeout
        self.__wait_queue_multiple = wait_queue_multiple
        self.__ssl_context = ssl_context
        self.__ssl_match_hostname = ssl_match_hostname
        self.__socket_keepalive = socket_keepalive
        self.__event_listeners = event_listeners
        self.__appname = appname
        self.__driver = driver
        self.__compression_settings = compression_settings
        self.__server_api = server_api
        self.__load_balanced = load_balanced
        self.__metadata = copy.deepcopy(_METADATA)
        if appname:
            self.__metadata['application'] = {'name': appname}

        # Combine the "driver" MongoClient option with PyMongo's info, like:
        # {
        #    'driver': {
        #        'name': 'PyMongo|MyDriver',
        #        'version': '3.7.0|1.2.3',
        #    },
        #    'platform': 'CPython 3.6.0|MyPlatform'
        # }
        if driver:
            if driver.name:
                self.__metadata['driver']['name'] = "%s|%s" % (
                    _METADATA['driver']['name'], driver.name)
            if driver.version:
                self.__metadata['driver']['version'] = "%s|%s" % (
                    _METADATA['driver']['version'], driver.version)
            if driver.platform:
                self.__metadata['platform'] = "%s|%s" % (
                    _METADATA['platform'], driver.platform)

    @property
    def non_default_options(self):
        """The non-default options this pool was created with.

        Added for CMAP's :class:`PoolCreatedEvent`.
        """
        opts = {}
        if self.__max_pool_size != MAX_POOL_SIZE:
            opts['maxPoolSize'] = self.__max_pool_size
        if self.__min_pool_size != MIN_POOL_SIZE:
            opts['minPoolSize'] = self.__min_pool_size
        if self.__max_idle_time_seconds != MAX_IDLE_TIME_SEC:
            opts['maxIdleTimeMS'] = self.__max_idle_time_seconds * 1000
        if self.__wait_queue_timeout != WAIT_QUEUE_TIMEOUT:
            opts['waitQueueTimeoutMS'] = self.__wait_queue_timeout * 1000
        return opts

    @property
    def max_pool_size(self):
        """The maximum allowable number of concurrent connections to each
        connected server. Requests to a server will block if there are
        `maxPoolSize` outstanding connections to the requested server.
        Defaults to 100. Cannot be 0.

        When a server's pool has reached `max_pool_size`, operations for that
        server block waiting for a socket to be returned to the pool. If
        ``waitQueueTimeoutMS`` is set, a blocked operation will raise
        :exc:`~pymongo.errors.ConnectionFailure` after a timeout.
        By default ``waitQueueTimeoutMS`` is not set.
        """
        return self.__max_pool_size

    @property
    def min_pool_size(self):
        """The minimum required number of concurrent connections that the pool
        will maintain to each connected server. Default is 0.
        """
        return self.__min_pool_size

    @property
    def max_idle_time_seconds(self):
        """The maximum number of seconds that a connection can remain
        idle in the pool before being removed and replaced. Defaults to
        `None` (no limit).
        """
        return self.__max_idle_time_seconds

    @property
    def connect_timeout(self):
        """How long a connection can take to be opened before timing out.
        """
        return self.__connect_timeout

    @property
    def socket_timeout(self):
        """How long a send or receive on a socket can take before timing out.
        """
        return self.__socket_timeout

    @property
    def wait_queue_timeout(self):
        """How long a thread will wait for a socket from the pool if the pool
        has no free sockets.
        """
        return self.__wait_queue_timeout

    @property
    def wait_queue_multiple(self):
        """Multiplied by max_pool_size to give the number of threads allowed
        to wait for a socket at one time.
        """
        return self.__wait_queue_multiple

    @property
    def ssl_context(self):
        """An SSLContext instance or None.
        """
        return self.__ssl_context

    @property
    def ssl_match_hostname(self):
        """Call ssl.match_hostname if cert_reqs is not ssl.CERT_NONE.
        """
        return self.__ssl_match_hostname

    @property
    def socket_keepalive(self):
        """Whether to send periodic messages to determine if a connection
        is closed.
        """
        return self.__socket_keepalive

    @property
    def event_listeners(self):
        """An instance of pymongo.monitoring._EventListeners.
        """
        return self.__event_listeners

    @property
    def appname(self):
        """The application name, for sending with hello in server handshake.
        """
        return self.__appname

    @property
    def driver(self):
        """Driver name and version, for sending with hello in handshake.
        """
        return self.__driver

    @property
    def compression_settings(self):
        return self.__compression_settings

    @property
    def metadata(self):
        """A dict of metadata about the application, driver, os, and platform.
        """
        return self.__metadata.copy()

    @property
    def server_api(self):
        """A pymongo.server_api.ServerApi or None.
        """
        return self.__server_api

    @property
    def load_balanced(self):
        """True if this Pool is configured in load balanced mode.
        """
        return self.__load_balanced


def _negotiate_creds(all_credentials):
    """Return one credential that needs mechanism negotiation, if any.
    """
    if all_credentials:
        for creds in all_credentials.values():
            if creds.mechanism == 'DEFAULT' and creds.username:
                return creds
    return None


def _speculative_context(all_credentials):
    """Return the _AuthContext to use for speculative auth, if any.
    """
    if all_credentials and len(all_credentials) == 1:
        creds = next(itervalues(all_credentials))
        return auth._AuthContext.from_credentials(creds)
    return None


class _CancellationContext(object):
    def __init__(self):
        self._cancelled = False

    def cancel(self):
        """Cancel this context."""
        self._cancelled = True

    @property
    def cancelled(self):
        """Was cancel called?"""
        return self._cancelled


class SocketInfo(object):
    """Store a socket with some metadata.

    :Parameters:
      - `sock`: a raw socket object
      - `pool`: a Pool instance
      - `address`: the server's (host, port)
      - `id`: the id of this socket in it's pool
    """
    def __init__(self, sock, pool, address, id):
        self.pool_ref = weakref.ref(pool)
        self.sock = sock
        self.address = address
        self.id = id
        self.authset = set()
        self.closed = False
        self.last_checkin_time = _time()
        self.performed_handshake = False
        self.is_writable = False
        self.max_wire_version = MAX_WIRE_VERSION
        self.max_bson_size = MAX_BSON_SIZE
        self.max_message_size = MAX_MESSAGE_SIZE
        self.max_write_batch_size = MAX_WRITE_BATCH_SIZE
        self.supports_sessions = False
        self.hello_ok = None
        self.is_mongos = False
        self.op_msg_enabled = False
        self.listeners = pool.opts.event_listeners
        self.enabled_for_cmap = pool.enabled_for_cmap
        self.compression_settings = pool.opts.compression_settings
        self.compression_context = None
        self.socket_checker = SocketChecker()
        # Support for mechanism negotiation on the initial handshake.
        # Maps credential to saslSupportedMechs.
        self.negotiated_mechanisms = {}
        self.auth_ctx = {}

        # The pool's generation changes with each reset() so we can close
        # sockets created before the last reset.
        self.pool_gen = pool.gen
        self.generation = self.pool_gen.get_overall()
        self.ready = False
        self.cancel_context = None
        if not pool.handshake:
            # This is a Monitor connection.
            self.cancel_context = _CancellationContext()
        self.opts = pool.opts
        self.more_to_come = False
        # For load balancer support.
        self.service_id = None
        # When executing a transaction in load balancing mode, this flag is
        # set to true to indicate that the session now owns the connection.
        self.pinned_txn = False
        self.pinned_cursor = False
        self.active = False

    def pin_txn(self):
        self.pinned_txn = True
        assert not self.pinned_cursor

    def pin_cursor(self):
        self.pinned_cursor = True
        assert not self.pinned_txn

    def unpin(self):
        pool = self.pool_ref()
        if pool:
            pool.return_socket(self)
        else:
            self.close_socket(ConnectionClosedReason.STALE)

    def hello_cmd(self):
        if self.opts.server_api or self.hello_ok:
            return SON([(HelloCompat.CMD, 1)])
        else:
            return SON([(HelloCompat.LEGACY_CMD, 1), ('helloOk', True)])

    def hello(self, all_credentials=None):
        return self._hello(None, None, None, all_credentials)

    def _hello(self, cluster_time, topology_version,
                  heartbeat_frequency, all_credentials):
        cmd = self.hello_cmd()
        performing_handshake = not self.performed_handshake
        awaitable = False
        if performing_handshake:
            self.performed_handshake = True
            cmd['client'] = self.opts.metadata
            if self.compression_settings:
                cmd['compression'] = self.compression_settings.compressors
            if self.opts.load_balanced:
                cmd['loadBalanced'] = True
        elif topology_version is not None:
            cmd['topologyVersion'] = topology_version
            cmd['maxAwaitTimeMS'] = int(heartbeat_frequency*1000)
            awaitable = True
            # If connect_timeout is None there is no timeout.
            if self.opts.connect_timeout:
                self.sock.settimeout(
                    self.opts.connect_timeout + heartbeat_frequency)

        if self.max_wire_version >= 6 and cluster_time is not None:
            cmd['$clusterTime'] = cluster_time

        # XXX: Simplify in PyMongo 4.0 when all_credentials is always a single
        # unchangeable value per MongoClient.
        creds = _negotiate_creds(all_credentials)
        if creds:
            cmd['saslSupportedMechs'] = creds.source + '.' + creds.username
        auth_ctx = _speculative_context(all_credentials)
        if auth_ctx:
            cmd['speculativeAuthenticate'] = auth_ctx.speculate_command()

        doc = self.command('admin', cmd, publish_events=False,
                           exhaust_allowed=awaitable)
        # PYTHON-2712 will remove this topologyVersion fallback logic.
        if self.opts.load_balanced and _MOCK_SERVICE_ID:
            process_id = doc.get('topologyVersion', {}).get('processId')
            doc.setdefault('serviceId', process_id)
        if not self.opts.load_balanced:
            doc.pop('serviceId', None)
        hello = IsMaster(doc, awaitable=awaitable)
        self.is_writable = hello.is_writable
        self.max_wire_version = hello.max_wire_version
        self.max_bson_size = hello.max_bson_size
        self.max_message_size = hello.max_message_size
        self.max_write_batch_size = hello.max_write_batch_size
        self.supports_sessions = (
            hello.logical_session_timeout_minutes is not None)
        self.hello_ok = hello.hello_ok
        self.is_mongos = hello.server_type == SERVER_TYPE.Mongos
        if performing_handshake and self.compression_settings:
            ctx = self.compression_settings.get_compression_context(
                hello.compressors)
            self.compression_context = ctx

        self.op_msg_enabled = hello.max_wire_version >= 6
        if creds:
            self.negotiated_mechanisms[creds] = hello.sasl_supported_mechs
        if auth_ctx:
            auth_ctx.parse_response(hello)
            if auth_ctx.speculate_succeeded():
                self.auth_ctx[auth_ctx.credentials] = auth_ctx
        if self.opts.load_balanced:
            if not hello.service_id:
                raise ConfigurationError(
                    'Driver attempted to initialize in load balancing mode,'
                    ' but the server does not support this mode')
            self.service_id = hello.service_id
            self.generation = self.pool_gen.get(self.service_id)
        return hello

    def _next_reply(self):
        reply = self.receive_message(None)
        self.more_to_come = reply.more_to_come
        unpacked_docs = reply.unpack_response()
        response_doc = unpacked_docs[0]
        helpers._check_command_response(response_doc, self.max_wire_version)
        # Remove after PYTHON-2712.
        if not self.opts.load_balanced:
            response_doc.pop('serviceId', None)
        return response_doc

    def command(self, dbname, spec, secondary_ok=False,
                read_preference=ReadPreference.PRIMARY,
                codec_options=DEFAULT_CODEC_OPTIONS, check=True,
                allowable_errors=None, check_keys=False,
                read_concern=None,
                write_concern=None,
                parse_write_concern_error=False,
                collation=None,
                session=None,
                client=None,
                retryable_write=False,
                publish_events=True,
                user_fields=None,
                exhaust_allowed=False):
        """Execute a command or raise an error.

        :Parameters:
          - `dbname`: name of the database on which to run the command
          - `spec`: a command document as a dict, SON, or mapping object
          - `secondary_ok`: whether to set the secondaryOkay wire protocol bit
          - `read_preference`: a read preference
          - `codec_options`: a CodecOptions instance
          - `check`: raise OperationFailure if there are errors
          - `allowable_errors`: errors to ignore if `check` is True
          - `check_keys`: if True, check `spec` for invalid keys
          - `read_concern`: The read concern for this command.
          - `write_concern`: The write concern for this command.
          - `parse_write_concern_error`: Whether to parse the
            ``writeConcernError`` field in the command response.
          - `collation`: The collation for this command.
          - `session`: optional ClientSession instance.
          - `client`: optional MongoClient for gossipping $clusterTime.
          - `retryable_write`: True if this command is a retryable write.
          - `publish_events`: Should we publish events for this command?
          - `user_fields` (optional): Response fields that should be decoded
            using the TypeDecoders from codec_options, passed to
            bson._decode_all_selective.
        """
        self.validate_session(client, session)
        session = _validate_session_write_concern(session, write_concern)

        # Ensure command name remains in first place.
        if not isinstance(spec, ORDERED_TYPES):
            spec = SON(spec)

        if (read_concern and self.max_wire_version < 4
                and not read_concern.ok_for_legacy):
            raise ConfigurationError(
                'read concern level of %s is not valid '
                'with a max wire version of %d.'
                % (read_concern.level, self.max_wire_version))
        if not (write_concern is None or write_concern.acknowledged or
                collation is None):
            raise ConfigurationError(
                'Collation is unsupported for unacknowledged writes.')
        if (self.max_wire_version >= 5 and
                write_concern and
                not write_concern.is_server_default):
            spec['writeConcern'] = write_concern.document
        elif self.max_wire_version < 5 and collation is not None:
            raise ConfigurationError(
                'Must be connected to MongoDB 3.4+ to use a collation.')

        self.add_server_api(spec)
        if session:
            session._apply_to(spec, retryable_write, read_preference,
                              self)
        self.send_cluster_time(spec, session, client)
        listeners = self.listeners if publish_events else None
        unacknowledged = write_concern and not write_concern.acknowledged
        if self.op_msg_enabled:
            self._raise_if_not_writable(unacknowledged)
        try:
            return command(self, dbname, spec, secondary_ok,
                           self.is_mongos, read_preference, codec_options,
                           session, client, check, allowable_errors,
                           self.address, check_keys, listeners,
                           self.max_bson_size, read_concern,
                           parse_write_concern_error=parse_write_concern_error,
                           collation=collation,
                           compression_ctx=self.compression_context,
                           use_op_msg=self.op_msg_enabled,
                           unacknowledged=unacknowledged,
                           user_fields=user_fields,
                           exhaust_allowed=exhaust_allowed)
        except (OperationFailure, NotPrimaryError):
            raise
        # Catch socket.error, KeyboardInterrupt, etc. and close ourselves.
        except BaseException as error:
            self._raise_connection_failure(error)

    def send_message(self, message, max_doc_size):
        """Send a raw BSON message or raise ConnectionFailure.

        If a network exception is raised, the socket is closed.
        """
        if (self.max_bson_size is not None
                and max_doc_size > self.max_bson_size):
            raise DocumentTooLarge(
                "BSON document too large (%d bytes) - the connected server "
                "supports BSON document sizes up to %d bytes." %
                (max_doc_size, self.max_bson_size))

        try:
            self.sock.sendall(message)
        except BaseException as error:
            self._raise_connection_failure(error)

    def receive_message(self, request_id):
        """Receive a raw BSON message or raise ConnectionFailure.

        If any exception is raised, the socket is closed.
        """
        try:
            return receive_message(self, request_id, self.max_message_size)
        except BaseException as error:
            self._raise_connection_failure(error)

    def _raise_if_not_writable(self, unacknowledged):
        """Raise NotPrimaryError on unacknowledged write if this socket is not
        writable.
        """
        if unacknowledged and not self.is_writable:
            # Write won't succeed, bail as if we'd received a not primary error.
            raise NotPrimaryError("not primary", {
                "ok": 0, "errmsg": "not primary", "code": 10107})

    def legacy_write(self, request_id, msg, max_doc_size, with_last_error):
        """Send OP_INSERT, etc., optionally returning response as a dict.

        Can raise ConnectionFailure or OperationFailure.

        :Parameters:
          - `request_id`: an int.
          - `msg`: bytes, an OP_INSERT, OP_UPDATE, or OP_DELETE message,
            perhaps with a getlasterror command appended.
          - `max_doc_size`: size in bytes of the largest document in `msg`.
          - `with_last_error`: True if a getlasterror command is appended.
        """
        self._raise_if_not_writable(not with_last_error)

        self.send_message(msg, max_doc_size)
        if with_last_error:
            reply = self.receive_message(request_id)
            return helpers._check_gle_response(reply.command_response(),
                                               self.max_wire_version)

    def write_command(self, request_id, msg):
        """Send "insert" etc. command, returning response as a dict.

        Can raise ConnectionFailure or OperationFailure.

        :Parameters:
          - `request_id`: an int.
          - `msg`: bytes, the command message.
        """
        self.send_message(msg, 0)
        reply = self.receive_message(request_id)
        result = reply.command_response()

        # Raises NotPrimaryError or OperationFailure.
        helpers._check_command_response(result, self.max_wire_version)
        return result

    def check_auth(self, all_credentials):
        """Update this socket's authentication.

        Log in or out to bring this socket's credentials up to date with
        those provided. Can raise ConnectionFailure or OperationFailure.

        :Parameters:
          - `all_credentials`: dict, maps auth source to MongoCredential.
        """
        if all_credentials or self.authset:
            cached = set(itervalues(all_credentials))
            authset = self.authset.copy()

            # Logout any credentials that no longer exist in the cache.
            for credentials in authset - cached:
                auth.logout(credentials.source, self)
                self.authset.discard(credentials)

            for credentials in cached - authset:
                self.authenticate(credentials)

        # CMAP spec says to publish the ready event only after authenticating
        # the connection.
        if not self.ready:
            self.ready = True
            if self.enabled_for_cmap:
                self.listeners.publish_connection_ready(self.address, self.id)

    def authenticate(self, credentials):
        """Log in to the server and store these credentials in `authset`.

        Can raise ConnectionFailure or OperationFailure.

        :Parameters:
          - `credentials`: A MongoCredential.
        """
        auth.authenticate(credentials, self)
        self.authset.add(credentials)
        # negotiated_mechanisms are no longer needed.
        self.negotiated_mechanisms.pop(credentials, None)
        self.auth_ctx.pop(credentials, None)

    def validate_session(self, client, session):
        """Validate this session before use with client.

        Raises error if this session is logged in as a different user or
        the client is not the one that created the session.
        """
        if session:
            if session._client is not client:
                raise InvalidOperation(
                    'Can only use session with the MongoClient that'
                    ' started it')
            if session._authset != self.authset:
                raise InvalidOperation(
                    'Cannot use session after authenticating with different'
                    ' credentials')

    def close_socket(self, reason):
        """Close this connection with a reason."""
        if self.closed:
            return
        self._close_socket()
        if reason and self.enabled_for_cmap:
            self.listeners.publish_connection_closed(
                self.address, self.id, reason)

    def _close_socket(self):
        """Close this connection."""
        if self.closed:
            return
        self.closed = True
        if self.cancel_context:
            self.cancel_context.cancel()
        # Note: We catch exceptions to avoid spurious errors on interpreter
        # shutdown.
        try:
            self.sock.close()
        except Exception:
            pass

    def socket_closed(self):
        """Return True if we know socket has been closed, False otherwise."""
        return self.socket_checker.socket_closed(self.sock)

    def send_cluster_time(self, command, session, client):
        """Add cluster time for MongoDB >= 3.6."""
        if self.max_wire_version >= 6 and client:
            client._send_cluster_time(command, session)

    def add_server_api(self, command):
        """Add server_api parameters."""
        if self.opts.server_api:
            _add_to_command(command, self.opts.server_api)

    def update_last_checkin_time(self):
        self.last_checkin_time = _time()

    def update_is_writable(self, is_writable):
        self.is_writable = is_writable

    def idle_time_seconds(self):
        """Seconds since this socket was last checked into its pool."""
        return _time() - self.last_checkin_time

    def _raise_connection_failure(self, error):
        # Catch *all* exceptions from socket methods and close the socket. In
        # regular Python, socket operations only raise socket.error, even if
        # the underlying cause was a Ctrl-C: a signal raised during socket.recv
        # is expressed as an EINTR error from poll. See internal_select_ex() in
        # socketmodule.c. All error codes from poll become socket.error at
        # first. Eventually in PyEval_EvalFrameEx the interpreter checks for
        # signals and throws KeyboardInterrupt into the current frame on the
        # main thread.
        #
        # But in Gevent and Eventlet, the polling mechanism (epoll, kqueue,
        # ...) is called in Python code, which experiences the signal as a
        # KeyboardInterrupt from the start, rather than as an initial
        # socket.error, so we catch that, close the socket, and reraise it.
        #
        # The connection closed event will be emitted later in return_socket.
        if self.ready:
            reason = None
        else:
            reason = ConnectionClosedReason.ERROR
        self.close_socket(reason)
        # SSLError from PyOpenSSL inherits directly from Exception.
        if isinstance(error, (IOError, OSError, _SSLError)):
            _raise_connection_failure(self.address, error)
        else:
            raise

    def __eq__(self, other):
        return self.sock == other.sock

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.sock)

    def __repr__(self):
        return "SocketInfo(%s)%s at %s" % (
            repr(self.sock),
            self.closed and " CLOSED" or "",
            id(self)
        )


def _create_connection(address, options):
    """Given (host, port) and PoolOptions, connect and return a socket object.

    Can raise socket.error.

    This is a modified version of create_connection from CPython >= 2.7.
    """
    host, port = address

    # Check if dealing with a unix domain socket
    if host.endswith('.sock'):
        if not hasattr(socket, "AF_UNIX"):
            raise ConnectionFailure("UNIX-sockets are not supported "
                                    "on this system")
        sock = socket.socket(socket.AF_UNIX)
        # SOCK_CLOEXEC not supported for Unix sockets.
        _set_non_inheritable_non_atomic(sock.fileno())
        try:
            sock.connect(host)
            return sock
        except socket.error:
            sock.close()
            raise

    # Don't try IPv6 if we don't support it. Also skip it if host
    # is 'localhost' (::1 is fine). Avoids slow connect issues
    # like PYTHON-356.
    family = socket.AF_INET
    if socket.has_ipv6 and host != 'localhost':
        family = socket.AF_UNSPEC

    err = None
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
        af, socktype, proto, dummy, sa = res
        # SOCK_CLOEXEC was new in CPython 3.2, and only available on a limited
        # number of platforms (newer Linux and *BSD). Starting with CPython 3.4
        # all file descriptors are created non-inheritable. See PEP 446.
        try:
            sock = socket.socket(
                af, socktype | getattr(socket, 'SOCK_CLOEXEC', 0), proto)
        except socket.error:
            # Can SOCK_CLOEXEC be defined even if the kernel doesn't support
            # it?
            sock = socket.socket(af, socktype, proto)
        # Fallback when SOCK_CLOEXEC isn't available.
        _set_non_inheritable_non_atomic(sock.fileno())
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(options.connect_timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE,
                            options.socket_keepalive)
            if options.socket_keepalive:
                _set_keepalive_times(sock)
            sock.connect(sa)
            return sock
        except socket.error as e:
            err = e
            sock.close()

    if err is not None:
        raise err
    else:
        # This likely means we tried to connect to an IPv6 only
        # host with an OS/kernel or Python interpreter that doesn't
        # support IPv6. The test case is Jython2.5.1 which doesn't
        # support IPv6 at all.
        raise socket.error('getaddrinfo failed')


def _configured_socket(address, options):
    """Given (host, port) and PoolOptions, return a configured socket.

    Can raise socket.error, ConnectionFailure, or CertificateError.

    Sets socket's SSL and timeout options.
    """
    sock = _create_connection(address, options)
    ssl_context = options.ssl_context

    if ssl_context is not None:
        host = address[0]
        try:
            # According to RFC6066, section 3, IPv4 and IPv6 literals are
            # not permitted for SNI hostname.
            # Previous to Python 3.7 wrap_socket would blindly pass
            # IP addresses as SNI hostname.
            # https://bugs.python.org/issue32185
            # We have to pass hostname / ip address to wrap_socket
            # to use SSLContext.check_hostname.
            if _HAVE_SNI and (not is_ip_address(host) or _IPADDR_SAFE):
                sock = ssl_context.wrap_socket(sock, server_hostname=host)
            else:
                sock = ssl_context.wrap_socket(sock)
        except CertificateError:
            sock.close()
            # Raise CertificateError directly like we do after match_hostname
            # below.
            raise
        except (IOError, OSError, _SSLError) as exc:
            sock.close()
            # We raise AutoReconnect for transient and permanent SSL handshake
            # failures alike. Permanent handshake failures, like protocol
            # mismatch, will be turned into ServerSelectionTimeoutErrors later.
            _raise_connection_failure(address, exc, "SSL handshake failed: ")
        if (ssl_context.verify_mode and not
                getattr(ssl_context, "check_hostname", False) and
                options.ssl_match_hostname):
            try:
                match_hostname(sock.getpeercert(), hostname=host)
            except CertificateError:
                sock.close()
                raise

    sock.settimeout(options.socket_timeout)
    return sock


class _PoolClosedError(PyMongoError):
    """Internal error raised when a thread tries to get a connection from a
    closed pool.
    """
    pass


class _PoolGeneration(object):
    def __init__(self):
        # Maps service_id to generation.
        self._generations = collections.defaultdict(int)
        # Overall pool generation.
        self._generation = 0

    def get(self, service_id):
        """Get the generation for the given service_id."""
        if service_id is None:
            return self._generation
        return self._generations[service_id]

    def get_overall(self):
        """Get the Pool's overall generation."""
        return self._generation

    def inc(self, service_id):
        """Increment the generation for the given service_id."""
        self._generation += 1
        if service_id is None:
            for service_id in self._generations:
                self._generations[service_id] += 1
        else:
            self._generations[service_id] += 1

    def stale(self, gen, service_id):
        """Return if the given generation for a given service_id is stale."""
        return gen != self.get(service_id)


class PoolState(object):
    PAUSED = 1
    READY = 2
    CLOSED = 3


# Do *not* explicitly inherit from object or Jython won't call __del__
# http://bugs.jython.org/issue1057
class Pool:
    def __init__(self, address, options, handshake=True):
        """
        :Parameters:
          - `address`: a (hostname, port) tuple
          - `options`: a PoolOptions instance
          - `handshake`: whether to call hello for each new SocketInfo
        """
        # Check a socket's health with socket_closed() every once in a while.
        # Can override for testing: 0 to always check, None to never check.
        self._check_interval_seconds = 1
        # LIFO pool. Sockets are ordered on idle time. Sockets claimed
        # and returned to pool from the left side. Stale sockets removed
        # from the right side.
        self.sockets = collections.deque()
        self.lock = threading.Lock()
        self.active_sockets = 0
        # Monotonically increasing connection ID required for CMAP Events.
        self.next_connection_id = 1
        self.closed = False
        # Track whether the sockets in this pool are writeable or not.
        self.is_writable = None

        # Keep track of resets, so we notice sockets created before the most
        # recent reset and close them.
        # self.generation = 0
        self.gen = _PoolGeneration()
        self.pid = os.getpid()
        self.address = address
        self.opts = options
        self.handshake = handshake
        # Don't publish events in Monitor pools.
        self.enabled_for_cmap = (
                self.handshake and
                self.opts.event_listeners is not None and
                self.opts.event_listeners.enabled_for_cmap)

        if (self.opts.wait_queue_multiple is None or
                self.opts.max_pool_size is None):
            max_waiters = None
        else:
            max_waiters = (
                self.opts.max_pool_size * self.opts.wait_queue_multiple)

        self._socket_semaphore = thread_util.create_semaphore(
            self.opts.max_pool_size, max_waiters)
        if self.enabled_for_cmap:
            self.opts.event_listeners.publish_pool_created(
                self.address, self.opts.non_default_options)
        # Retain references to pinned connections to prevent the CPython GC
        # from thinking that a cursor's pinned connection can be GC'd when the
        # cursor is GC'd (see PYTHON-2751).
        self.__pinned_sockets = set()
        self.ncursors = 0
        self.ntxns = 0

    def _reset(self, close, service_id=None):
        with self.lock:
            if self.closed:
                return
            self.gen.inc(service_id)
            newpid = os.getpid()
            if self.pid != newpid:
                self.pid = newpid
                self.active_sockets = 0
            if service_id is None:
                sockets, self.sockets = self.sockets, collections.deque()
            else:
                discard = collections.deque()
                keep = collections.deque()
                for sock_info in self.sockets:
                    if sock_info.service_id == service_id:
                        discard.append(sock_info)
                    else:
                        keep.append(sock_info)
                sockets = discard
                self.sockets = keep

            if close:
                self.closed = True

        listeners = self.opts.event_listeners
        # CMAP spec says that close() MUST close sockets before publishing the
        # PoolClosedEvent but that reset() SHOULD close sockets *after*
        # publishing the PoolClearedEvent.
        if close:
            for sock_info in sockets:
                sock_info.close_socket(ConnectionClosedReason.POOL_CLOSED)
            if self.enabled_for_cmap:
                listeners.publish_pool_closed(self.address)
        else:
            if self.enabled_for_cmap:
                listeners.publish_pool_cleared(self.address,
                                               service_id=service_id)
            for sock_info in sockets:
                sock_info.close_socket(ConnectionClosedReason.STALE)

    def update_is_writable(self, is_writable):
        """Updates the is_writable attribute on all sockets currently in the
        Pool.
        """
        self.is_writable = is_writable
        with self.lock:
            for socket in self.sockets:
                socket.update_is_writable(self.is_writable)

    def reset(self, service_id=None):
        self._reset(close=False, service_id=service_id)

    def close(self):
        self._reset(close=True)

    def stale_generation(self, gen, service_id):
        return self.gen.stale(gen, service_id)

    def remove_stale_sockets(self, reference_generation, all_credentials):
        """Removes stale sockets then adds new ones if pool is too small and
        has not been reset. The `reference_generation` argument specifies the
        `generation` at the point in time this operation was requested on the
        pool.
        """
        if self.opts.max_idle_time_seconds is not None:
            with self.lock:
                while (self.sockets and
                       self.sockets[-1].idle_time_seconds() > self.opts.max_idle_time_seconds):
                    sock_info = self.sockets.pop()
                    sock_info.close_socket(ConnectionClosedReason.IDLE)

        while True:
            with self.lock:
                if (len(self.sockets) + self.active_sockets >=
                        self.opts.min_pool_size):
                    # There are enough sockets in the pool.
                    break

            # We must acquire the semaphore to respect max_pool_size.
            if not self._socket_semaphore.acquire(False):
                break
            try:
                sock_info = self.connect(all_credentials)
                with self.lock:
                    # Close connection and return if the pool was reset during
                    # socket creation or while acquiring the pool lock.
                    if self.gen.get_overall() != reference_generation:
                        sock_info.close_socket(ConnectionClosedReason.STALE)
                        break
                    self.sockets.appendleft(sock_info)
            finally:
                self._socket_semaphore.release()

    def connect(self, all_credentials=None):
        """Connect to Mongo and return a new SocketInfo.

        Can raise ConnectionFailure or CertificateError.

        Note that the pool does not keep a reference to the socket -- you
        must call return_socket() when you're done with it.
        """
        with self.lock:
            conn_id = self.next_connection_id
            self.next_connection_id += 1

        listeners = self.opts.event_listeners
        if self.enabled_for_cmap:
            listeners.publish_connection_created(self.address, conn_id)

        try:
            sock = _configured_socket(self.address, self.opts)
        except BaseException as error:
            if self.enabled_for_cmap:
                listeners.publish_connection_closed(
                    self.address, conn_id, ConnectionClosedReason.ERROR)

            if isinstance(error, (IOError, OSError, _SSLError)):
                _raise_connection_failure(self.address, error)

            raise

        sock_info = SocketInfo(sock, self, self.address, conn_id)
        try:
            if self.handshake:
                sock_info.hello(all_credentials)
                self.is_writable = sock_info.is_writable

            sock_info.check_auth(all_credentials)
        except BaseException:
            sock_info.close_socket(ConnectionClosedReason.ERROR)
            raise

        return sock_info

    @contextlib.contextmanager
    def get_socket(self, all_credentials, handler=None):
        """Get a socket from the pool. Use with a "with" statement.

        Returns a :class:`SocketInfo` object wrapping a connected
        :class:`socket.socket`.

        This method should always be used in a with-statement::

            with pool.get_socket(credentials) as socket_info:
                socket_info.send_message(msg)
                data = socket_info.receive_message(op_code, request_id)

        The socket is logged in or out as needed to match ``all_credentials``
        using the correct authentication mechanism for the server's wire
        protocol version.

        Can raise ConnectionFailure or OperationFailure.

        :Parameters:
          - `all_credentials`: dict, maps auth source to MongoCredential.
          - `handler` (optional): A _MongoClientErrorHandler.
        """
        listeners = self.opts.event_listeners
        if self.enabled_for_cmap:
            listeners.publish_connection_check_out_started(self.address)

        sock_info = self._get_socket(all_credentials)
        if self.enabled_for_cmap:
            listeners.publish_connection_checked_out(
                self.address, sock_info.id)
        try:
            yield sock_info
        except:
            # Exception in caller. Ensure the connection gets returned.
            # Note that when pinned is True, the session owns the
            # connection and it is responsible for checking the connection
            # back into the pool.
            pinned = sock_info.pinned_txn or sock_info.pinned_cursor
            if handler:
                # Perform SDAM error handling rules while the connection is
                # still checked out.
                exc_type, exc_val, _ = sys.exc_info()
                handler.handle(exc_type, exc_val)
            if not pinned and sock_info.active:
                self.return_socket(sock_info)
            raise
        if sock_info.pinned_txn:
            with self.lock:
                self.__pinned_sockets.add(sock_info)
                self.ntxns += 1
        elif sock_info.pinned_cursor:
            with self.lock:
                self.__pinned_sockets.add(sock_info)
                self.ncursors += 1
        elif sock_info.active:
            self.return_socket(sock_info)

    def _get_socket(self, all_credentials):
        """Get or create a SocketInfo. Can raise ConnectionFailure."""
        # We use the pid here to avoid issues with fork / multiprocessing.
        # See test.test_client:TestClient.test_fork for an example of
        # what could go wrong otherwise
        if self.pid != os.getpid():
            self.reset()

        if self.closed:
            if self.enabled_for_cmap:
                self.opts.event_listeners.publish_connection_check_out_failed(
                    self.address, ConnectionCheckOutFailedReason.POOL_CLOSED)
            raise _PoolClosedError(
                'Attempted to check out a connection from closed connection '
                'pool')

        # Get a free socket or create one.
        if not self._socket_semaphore.acquire(
                True, self.opts.wait_queue_timeout):
            self._raise_wait_queue_timeout()

        # We've now acquired the semaphore and must release it on error.
        sock_info = None
        incremented = False
        try:
            with self.lock:
                self.active_sockets += 1
                incremented = True

            while sock_info is None:
                try:
                    with self.lock:
                        sock_info = self.sockets.popleft()
                except IndexError:
                    # Can raise ConnectionFailure or CertificateError.
                    sock_info = self.connect(all_credentials)
                else:
                    if self._perished(sock_info):
                        sock_info = None
            sock_info.check_auth(all_credentials)
        except BaseException:
            if sock_info:
                # We checked out a socket but authentication failed.
                sock_info.close_socket(ConnectionClosedReason.ERROR)
            self._socket_semaphore.release()

            if incremented:
                with self.lock:
                    self.active_sockets -= 1

            if self.enabled_for_cmap:
                self.opts.event_listeners.publish_connection_check_out_failed(
                    self.address, ConnectionCheckOutFailedReason.CONN_ERROR)
            raise

        sock_info.active = True
        return sock_info

    def return_socket(self, sock_info):
        """Return the socket to the pool, or if it's closed discard it.

        :Parameters:
          - `sock_info`: The socket to check into the pool.
        """
        txn = sock_info.pinned_txn
        cursor = sock_info.pinned_cursor
        sock_info.active = False
        sock_info.pinned_txn = False
        sock_info.pinned_cursor = False
        self.__pinned_sockets.discard(sock_info)
        listeners = self.opts.event_listeners
        if self.enabled_for_cmap:
            listeners.publish_connection_checked_in(self.address, sock_info.id)
        if self.pid != os.getpid():
            self.reset()
        else:
            if self.closed:
                sock_info.close_socket(ConnectionClosedReason.POOL_CLOSED)
            elif sock_info.closed:
                # CMAP requires the closed event be emitted after the check in.
                if self.enabled_for_cmap:
                    listeners.publish_connection_closed(
                        self.address, sock_info.id,
                        ConnectionClosedReason.ERROR)
            else:
                with self.lock:
                    # Hold the lock to ensure this section does not race with
                    # Pool.reset().
                    if self.stale_generation(sock_info.generation,
                                             sock_info.service_id):
                        sock_info.close_socket(ConnectionClosedReason.STALE)
                    else:
                        sock_info.update_last_checkin_time()
                        sock_info.update_is_writable(self.is_writable)
                        self.sockets.appendleft(sock_info)

        self._socket_semaphore.release()
        with self.lock:
            if txn:
                self.ntxns -= 1
            elif cursor:
                self.ncursors -= 1
            self.active_sockets -= 1

    def _perished(self, sock_info):
        """Return True and close the connection if it is "perished".

        This side-effecty function checks if this socket has been idle for
        for longer than the max idle time, or if the socket has been closed by
        some external network error, or if the socket's generation is outdated.

        Checking sockets lets us avoid seeing *some*
        :class:`~pymongo.errors.AutoReconnect` exceptions on server
        hiccups, etc. We only check if the socket was closed by an external
        error if it has been > 1 second since the socket was checked into the
        pool, to keep performance reasonable - we can't avoid AutoReconnects
        completely anyway.
        """
        idle_time_seconds = sock_info.idle_time_seconds()
        # If socket is idle, open a new one.
        if (self.opts.max_idle_time_seconds is not None and
                idle_time_seconds > self.opts.max_idle_time_seconds):
            sock_info.close_socket(ConnectionClosedReason.IDLE)
            return True

        if (self._check_interval_seconds is not None and (
                0 == self._check_interval_seconds or
                idle_time_seconds > self._check_interval_seconds)):
            if sock_info.socket_closed():
                sock_info.close_socket(ConnectionClosedReason.ERROR)
                return True

        if self.stale_generation(sock_info.generation, sock_info.service_id):
            sock_info.close_socket(ConnectionClosedReason.STALE)
            return True

        return False

    def _raise_wait_queue_timeout(self):
        listeners = self.opts.event_listeners
        if self.enabled_for_cmap:
            listeners.publish_connection_check_out_failed(
                self.address, ConnectionCheckOutFailedReason.TIMEOUT)
        if self.opts.load_balanced:
            other_ops = self.active_sockets - self.ncursors - self.ntxns
            raise ConnectionFailure(
                'Timeout waiting for connection from the connection pool. '
                'maxPoolSize: %s, connections in use by cursors: %s, '
                'connections in use by transactions: %s, connections in use '
                'by other operations: %s, wait_queue_timeout: %s' % (
                    self.opts.max_pool_size, self.ncursors, self.ntxns,
                    other_ops, self.opts.wait_queue_timeout))
        raise ConnectionFailure(
            'Timed out while checking out a connection from connection pool. '
            'maxPoolSize: %s, wait_queue_timeout: %s' % (
                self.opts.max_pool_size, self.opts.wait_queue_timeout))

    def __del__(self):
        # Avoid ResourceWarnings in Python 3
        # Close all sockets without calling reset() or close() because it is
        # not safe to acquire a lock in __del__.
        for sock_info in self.sockets:
            sock_info.close_socket(None)
