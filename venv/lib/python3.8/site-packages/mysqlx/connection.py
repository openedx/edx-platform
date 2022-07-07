# Copyright (c) 2016, 2022, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is also distributed with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation.  The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have included with
# MySQL.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Implementation of communication for MySQL X servers."""

try:
    import ssl
    SSL_AVAILABLE = True
    TLS_VERSIONS = {
        "TLSv1": ssl.PROTOCOL_TLSv1,
        "TLSv1.1": ssl.PROTOCOL_TLSv1_1,
        "TLSv1.2": ssl.PROTOCOL_TLSv1_2}
    # TLSv1.3 included in PROTOCOL_TLS, but PROTOCOL_TLS is not included on 3.4
    if hasattr(ssl, "PROTOCOL_TLS"):
        TLS_VERSIONS["TLSv1.3"] = ssl.PROTOCOL_TLS  # pylint: disable=E1101
    else:
        TLS_VERSIONS["TLSv1.3"] = ssl.PROTOCOL_SSLv23  # Alias of PROTOCOL_TLS
    if hasattr(ssl, "HAS_TLSv1_3") and ssl.HAS_TLSv1_3:
        TLS_V1_3_SUPPORTED = True
    else:
        TLS_V1_3_SUPPORTED = False
except:
    SSL_AVAILABLE = False
    TLS_V1_3_SUPPORTED = False

import sys
import socket
import logging
import uuid
import platform
import queue
import os
import random
import re
import threading
import warnings

try:
    import dns.resolver
    import dns.exception
except ImportError:
    HAVE_DNSPYTHON = False
else:
    HAVE_DNSPYTHON = True

from datetime import datetime, timedelta
from functools import wraps

from .authentication import (MySQL41AuthPlugin, PlainAuthPlugin,
                             Sha256MemoryAuthPlugin)
# pylint: disable=W0622
from .errors import (InterfaceError, NotSupportedError, OperationalError,
                     PoolError, ProgrammingError, TimeoutError)
from .crud import Schema
from .constants import SSLMode, Auth, COMPRESSION_ALGORITHMS
from .helpers import escape, get_item_or_attr, iani_to_openssl_cs_name
from .protocol import (Protocol, MessageReader, MessageWriter, HAVE_LZ4,
                       HAVE_ZSTD)
from .result import BaseResult, Result, RowResult, SqlResult, DocResult
from .statement import SqlStatement, AddStatement, quote_identifier
from .protobuf import Protobuf

# pylint: disable=C0411,C0413
sys.path.append("..")
from mysql.connector.utils import linux_distribution
from mysql.connector.version import VERSION, LICENSE


_CONNECT_TIMEOUT = 10000  # Default connect timeout in milliseconds
_DROP_DATABASE_QUERY = "DROP DATABASE IF EXISTS {0}"
_CREATE_DATABASE_QUERY = "CREATE DATABASE IF NOT EXISTS {0}"
_SELECT_SCHEMA_NAME_QUERY = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA."
                             "SCHEMATA WHERE SCHEMA_NAME = '{}'")
_SELECT_VERSION_QUERY = "SELECT @@version"

_CNX_POOL_MAXSIZE = 99
_CNX_POOL_MAX_NAME_SIZE = 120
_CNX_POOL_NAME_REGEX = re.compile(r'[^a-zA-Z0-9._:\-*$#]')
_CNX_POOL_MAX_IDLE_TIME = 2147483
_CNX_POOL_QUEUE_TIMEOUT = 2147483

# Time is on seconds
_PENALTY_SERVER_OFFLINE = 1000000
_PENALTY_MAXED_OUT = 60
_PENALTY_NO_ADD_INFO = 60 * 60
_PENALTY_CONN_TIMEOUT = 60 * 60
_PENALTY_WRONG_PASSW = 60 * 60 * 24
_PENALTY_RESTARTING = 60
_TIMEOUT_PENALTIES = {
    # Server denays service e.g Max connections reached
    "[WinError 10053]": _PENALTY_MAXED_OUT, # Established connection was aborted
    "[Errno 32]": _PENALTY_MAXED_OUT, # Broken pipe
    # Server is Offline
    "[WinError 10061]": _PENALTY_SERVER_OFFLINE, # Target machine actively refused it
    "[Errno 111]": _PENALTY_SERVER_OFFLINE, # Connection refused
    # Host is offline:
    "[WinError 10060]": _PENALTY_CONN_TIMEOUT, # Not respond after a period of time
    # No route to Host:
    "[Errno 11001]": _PENALTY_NO_ADD_INFO,# getaddrinfo failed
    "[Errno -2]": _PENALTY_NO_ADD_INFO, # Name or service not known
    # Wrong Password
    "Access denied": _PENALTY_WRONG_PASSW
}
_TIMEOUT_PENALTIES_BY_ERR_NO = {
    1053: _PENALTY_RESTARTING
}
CONNECTION_CLOSED_ERROR = {
    1810: 'This session was closed because the connection has been idle for too '
          'long. Use "mysqlx.getSession()" or "mysqlx.getClient()" to create a '
          'new one.',
    1053: 'This session was closed because the server is shutting down.',
    3169: 'This session was closed because the connection has been killed in a '
          'different session. Use "mysqlx.getSession()" or "mysqlx.getClient()" '
          'to create a new one.',
};
_LOGGER = logging.getLogger("mysqlx")


def generate_pool_name(**kwargs):
    """Generate a pool name.

    This function takes keyword arguments, usually the connection arguments and
    tries to generate a name for the pool.

    Args:
        **kwargs: Arbitrary keyword arguments with the connection arguments.

    Raises:
        PoolError: If the name can't be generated.

    Returns:
        str: The generated pool name.
    """
    parts = []
    for key in ("host", "port", "user", "database", "client_id"):
        try:
            parts.append(str(kwargs[key]))
        except KeyError:
            pass

    if not parts:
        raise PoolError("Failed generating pool name; specify pool_name")

    return "_".join(parts)


def update_timeout_penalties_by_error(penalty_dict):
    """Update the timeout penalties directory.

    Update the timeout penalties by error dictionary used to deactivate a pool.
    Args:
        penalty_dict (dict): The dictionary with the new timeouts.
    """
    if penalty_dict and isinstance(penalty_dict, dict):
        _TIMEOUT_PENALTIES_BY_ERR_NO.update(penalty_dict)

class SocketStream(object):
    """Implements a socket stream."""
    def __init__(self):
        self._socket = None
        self._is_ssl = False
        self._is_socket = False
        self._host = None

    def connect(self, params, connect_timeout=_CONNECT_TIMEOUT):
        """Connects to a TCP service.

        Args:
            params (tuple): The connection parameters.

        Raises:
            :class:`mysqlx.InterfaceError`: If Unix socket is not supported.
        """
        if connect_timeout is not None:
            connect_timeout = connect_timeout / 1000  # Convert to seconds
        try:
            self._socket = socket.create_connection(params, connect_timeout)
            self._host = params[0]
        except ValueError:
            try:
                self._socket = socket.socket(socket.AF_UNIX)
                self._socket.settimeout(connect_timeout)
                self._socket.connect(params)
                self._is_socket = True
            except AttributeError:
                raise InterfaceError("Unix socket unsupported")
        self._socket.settimeout(None)

    def read(self, count):
        """Receive data from the socket.

        Args:
            count (int): Buffer size.

        Returns:
            bytes: The data received.
        """
        if self._socket is None:
            raise OperationalError("MySQLx Connection not available")
        buf = []
        while count > 0:
            data = self._socket.recv(count)
            if data == b"":
                raise RuntimeError("Unexpected connection close")
            buf.append(data)
            count -= len(data)
        return b"".join(buf)

    def sendall(self, data):
        """Send data to the socket.

        Args:
            data (bytes): The data to be sent.
        """
        if self._socket is None:
            raise OperationalError("MySQLx Connection not available")
        try:
            self._socket.sendall(data)
        except socket.error as err:
            raise OperationalError("Unexpected socket error: {}".format(err))

    def close(self):
        """Close the socket."""
        if not self._socket:
            return
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        except socket.error:
            # On [Errno 107] Transport endpoint is not connected
            pass
        self._socket = None

    def __del__(self):
        self.close()

    def set_ssl(self, ssl_protos, ssl_mode, ssl_ca, ssl_crl, ssl_cert, ssl_key,
                ssl_ciphers):
        """Set SSL parameters.

        Args:
            ssl_protos (list): SSL protocol to use.
            ssl_mode (str): SSL mode.
            ssl_ca (str): The certification authority certificate.
            ssl_crl (str): The certification revocation lists.
            ssl_cert (str): The certificate.
            ssl_key (str): The certificate key.
            ssl_ciphers (list): SSL ciphersuites to use.

        Raises:
            :class:`mysqlx.RuntimeError`: If Python installation has no SSL
                                          support.
            :class:`mysqlx.InterfaceError`: If the parameters are invalid.
        """
        if not SSL_AVAILABLE:
            self.close()
            raise RuntimeError("Python installation has no SSL support")

        if ssl_protos is None or not ssl_protos:
            context = ssl.create_default_context()
            if ssl_mode != SSLMode.VERIFY_IDENTITY:
                context.check_hostname = False
            if ssl_mode == SSLMode.REQUIRED:
                context.verify_mode = ssl.CERT_NONE
        else:
            ssl_protos.sort(reverse=True)
            tls_version = ssl_protos[0]
            if not TLS_V1_3_SUPPORTED and \
               tls_version == "TLSv1.3" and len(ssl_protos) > 1:
                tls_version = ssl_protos[1]
            ssl_protocol = TLS_VERSIONS[tls_version]
            context = ssl.SSLContext(ssl_protocol)

            if tls_version == "TLSv1.3":
                if "TLSv1.2" not in ssl_protos:
                    context.options |= ssl.OP_NO_TLSv1_2
                if "TLSv1.1" not in ssl_protos:
                    context.options |= ssl.OP_NO_TLSv1_1
                if "TLSv1" not in ssl_protos:
                    context.options |= ssl.OP_NO_TLSv1

        if ssl_ca:
            try:
                context.load_verify_locations(ssl_ca)
                context.verify_mode = ssl.CERT_REQUIRED
            except (IOError, ssl.SSLError) as err:
                self.close()
                raise InterfaceError("Invalid CA Certificate: {}".format(err))

        if ssl_crl:
            try:
                context.load_verify_locations(ssl_crl)
                context.verify_flags = ssl.VERIFY_CRL_CHECK_LEAF
            except (IOError, ssl.SSLError) as err:
                self.close()
                raise InterfaceError("Invalid CRL: {}".format(err))

        if ssl_cert:
            try:
                context.load_cert_chain(ssl_cert, ssl_key)
            except (IOError, ssl.SSLError) as err:
                self.close()
                raise InterfaceError("Invalid Certificate/Key: {}".format(err))

        if ssl_ciphers:
            context.set_ciphers(":".join(iani_to_openssl_cs_name(ssl_protos[0],
                                                                 ssl_ciphers)))
        try:
            self._socket = context.wrap_socket(self._socket,
                                               server_hostname=self._host)
        except ssl.CertificateError as err:
            raise InterfaceError(str(err))
        if ssl_mode == SSLMode.VERIFY_IDENTITY:
            context.check_hostname = True
            hostnames = []
            # Windows does not return loopback aliases on gethostbyaddr
            if os.name == 'nt' and (self._host == 'localhost' or \
               self._host == '127.0.0.1'):
                hostnames = ['localhost', '127.0.0.1']
            aliases = socket.gethostbyaddr(self._host)
            hostnames.extend([aliases[0]] + aliases[1])
            match_found = False
            errs = []
            for hostname in hostnames:
                try:
                    ssl.match_hostname(self._socket.getpeercert(), hostname)
                except ssl.CertificateError as err:
                    errs.append(str(err))
                else:
                    match_found = True
                    break
            if not match_found:
                self.close()
                raise InterfaceError("Unable to verify server identity: {}"
                                     "".format(", ".join(errs)))

        self._is_ssl = True

        # Raise a deprecation warning if TLSv1 or TLSv1.1 is being used
        tls_version = self._socket.version()
        if tls_version in ("TLSv1", "TLSv1.1"):
            warn_msg = (
                f"This connection is using {tls_version} which is now "
                "deprecated and will be removed in a future release of "
                "MySQL Connector/Python"
            )
            warnings.warn(warn_msg, DeprecationWarning)

    def is_ssl(self):
        """Verifies if SSL is being used.

        Returns:
            bool: Returns `True` if SSL is being used.
        """
        return self._is_ssl

    def is_socket(self):
        """Verifies if socket connection is being used.

        Returns:
            bool: Returns `True` if socket connection is being used.
        """
        return self._is_socket

    def is_secure(self):
        """Verifies if connection is secure.

        Returns:
            bool: Returns `True` if connection is secure.
        """
        return self._is_ssl or self._is_socket

    def is_open(self):
        """Verifies if connection is open.

        Returns:
            bool: Returns `True` if connection is open.
        """
        return self._socket is not None


def catch_network_exception(func):
    """Decorator used to catch socket.error or RuntimeError.

    Raises:
        :class:`mysqlx.InterfaceError`: If `socket.Error` or `RuntimeError`
                                        is raised.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """Wrapper function."""
        try:
            if isinstance(self, (Connection, PooledConnection)) and \
               self.is_server_disconnected():
                raise InterfaceError(*self.get_disconnected_reason())
            result = func(self, *args, **kwargs)
            if isinstance(result, BaseResult):
                warnings = result.get_warnings()
                for warning in warnings:
                    if warning["code"] in CONNECTION_CLOSED_ERROR:
                        error_msg = CONNECTION_CLOSED_ERROR[warning["code"]]
                        reason = ("Connection close: {}: {}"
                                  "".format(warning["msg"], error_msg), warning["code"])
                        if isinstance(self, (Connection, PooledConnection)):
                            self.set_server_disconnected(reason)
                        break
            return result
        except (socket.error, ConnectionResetError, ConnectionAbortedError, InterfaceError,
                RuntimeError, TimeoutError) as err:
            if func.__name__ == 'get_column_metadata' and args and \
               isinstance(args[0], SqlResult):
                warnings = args[0].get_warnings()
                if warnings:
                    warning = warnings[0]
                    error_msg = CONNECTION_CLOSED_ERROR[warning["code"]]
                    reason = ("Connection close: {}: {}"
                              "".format(warning["msg"], error_msg), warning["code"])
                    if isinstance(self, PooledConnection):
                        self.pool.remove_connections()
                        # pool must be listed as faulty if server is shutting down
                        if warning["code"] == 1053:
                            PoolsManager().set_pool_unavailable(self.pool, InterfaceError(*reason))
                    if isinstance(self, (Connection, PooledConnection)):
                        self.set_server_disconnected(reason)
                    self.disconnect()
                    raise InterfaceError(*reason)
                else:
                    self.disconnect()
                    raise
            else:
                self.disconnect()
                raise
    return wrapper


class Router(dict):
    """Represents a set of connection parameters.

    Args:
       settings (dict): Dictionary with connection settings
    .. versionadded:: 8.0.20
    """
    def __init__(self, connection_params):
        self.update(connection_params)
        self["available"] = self.get("available", True)

    def available(self):
        """Verifies if the Router is available to open connections.

        Returns:
            bool: True if this Router is available else False.
        """
        return self["available"]

    def set_unavailable(self):
        """Sets this Router unavailable to open connections.
        """
        self["available"] = False

    def get_connection_params(self):
        """Verifies if the Router is available to open connections.

        Returns:
            tuple: host and port or socket information tuple.
        """
        if "socket" in self:
            return self["socket"]
        return (self["host"], self["port"])


class RouterManager():
    """Manages the connection parameters of all the routers.

    Args:
        Routers (list): A list of Router objects.
        settings (dict): Dictionary with connection settings.
    .. versionadded:: 8.0.20
    """
    def __init__(self, routers, settings):
        self._routers = routers
        self._settings = settings
        self._cur_priority_idx = 0
        self._can_failover = True
        # Reuters status
        self._routers_directory = {}
        self.routers_priority_list = []
        self._ensure_priorities()

    def _ensure_priorities(self):
        """Ensure priorities.

        Raises:
            :class:`mysqlx.ProgrammingError`: If priorities are invalid.
        """
        priority_count = 0

        for router in self._routers:
            priority = router.get("priority", None)
            if priority is None:
                priority_count += 1
                router["priority"] = 100
            elif priority > 100:
                raise ProgrammingError("The priorities must be between 0 and "
                                       "100", 4007)

        if 0 < priority_count < len(self._routers):
            raise ProgrammingError("You must either assign no priority to any "
                                   "of the routers or give a priority for "
                                   "every router", 4000)

        self._routers.sort(key=lambda x: x["priority"], reverse=True)

        # Group servers with the same priority
        for router in self._routers:
            priority = router["priority"]
            if priority not in self._routers_directory.keys():
                self._routers_directory[priority] = [Router(router)]
                self.routers_priority_list.append(priority)
            else:
                self._routers_directory[priority].append(Router(router))

    def _get_available_routers(self, priority):
        """Get a list of the current available routers that shares the given priority.

        Returns:
            list: A list of the current available routers.
        """
        router_list = self._routers_directory[priority]
        router_list = [router for router in router_list if router.available()]
        return router_list

    def _get_random_connection_params(self, priority):
        """Get a random router from the group with the given priority.

        Returns:
            Router: A random router.
        """
        router_list = self._get_available_routers(priority)
        if not router_list:
            return None
        if len(router_list) == 1:
            return router_list[0]

        last = len(router_list) - 1
        index = random.randint(0, last)
        return router_list[index]

    def can_failover(self):
        """Returns the next connection parameters.

        Returns:
            bool: True if there is more server to failover to else False.
        """
        return self._can_failover

    def get_next_router(self):
        """Returns the next connection parameters.

        Returns:
            Router: with the connection parameters.
        """
        if not self._routers:
            self._can_failover = False
            router_settings = self._settings.copy()
            router_settings["host"] = self._settings.get("host", "localhost")
            router_settings["port"] = self._settings.get("port", 33060)
            return Router(router_settings)

        cur_priority = self.routers_priority_list[self._cur_priority_idx]
        routers_priority_len = len(self.routers_priority_list)

        search = True
        while search:
            router = self._get_random_connection_params(cur_priority)

            if router is not None or \
               self._cur_priority_idx >= routers_priority_len:
                if self._cur_priority_idx == routers_priority_len -1 and \
                    len(self._get_available_routers(cur_priority)) < 2:
                    self._can_failover = False
                break

            # Search on next group
            self._cur_priority_idx += 1
            if self._cur_priority_idx < routers_priority_len:
                cur_priority = self.routers_priority_list[self._cur_priority_idx]

        return router

    def get_routers_directory(self):
        """Returns the directory containing all the routers managed.

        Returns:
            dict: Dictionary with priorities as connection settings.
        """
        return self._routers_directory


class Connection(object):
    """Connection to a MySQL Server.

    Args:
        settings (dict): Dictionary with connection settings.
    """
    def __init__(self, settings):
        self.settings = settings
        self.stream = SocketStream()
        self.protocol = None
        self.keep_open = None
        self._user = settings.get("user")
        self._password = settings.get("password")
        self._schema = settings.get("schema")
        self._active_result = None
        self._routers = settings.get("routers", [])

        if "host" in settings and settings["host"]:
            self._routers.append({
                "host": settings.get("host"),
                "port": settings.get("port", None)
            })

        self.router_manager = RouterManager(self._routers, settings)
        self._connect_timeout = settings.get("connect-timeout",
                                             _CONNECT_TIMEOUT)
        if self._connect_timeout == 0:
            # None is assigned if connect timeout is 0, which disables timeouts
            # on socket operations
            self._connect_timeout = None

        self._stmt_counter = 0
        self._prepared_stmt_ids = []
        self._prepared_stmt_supported = True
        self._server_disconnected = False
        self._server_disconnected_reason = None

    def fetch_active_result(self):
        """Fetch active result."""
        if self._active_result is not None:
            self._active_result.fetch_all()
            self._active_result = None

    def set_active_result(self, result):
        """Set active result.

        Args:
            `Result`: It can be :class:`mysqlx.Result`,
                      :class:`mysqlx.BufferingResult`,
                      :class:`mysqlx.RowResult`, :class:`mysqlx.SqlResult` or
                      :class:`mysqlx.DocResult`.
        """
        self._active_result = result

    def connect(self):
        """Attempt to connect to the MySQL server.

        Raises:
            :class:`mysqlx.InterfaceError`: If fails to connect to the MySQL
                                            server.
            :class:`mysqlx.TimeoutError`: If connect timeout was exceeded.
        """
        # Loop and check
        error = None
        while self.router_manager.can_failover():
            try:
                router = self.router_manager.get_next_router()
                self.stream.connect(router.get_connection_params(),
                                    self._connect_timeout)
                reader = MessageReader(self.stream)
                writer = MessageWriter(self.stream)
                self.protocol = Protocol(reader, writer)

                caps_data = self.protocol.get_capabilites().capabilities
                caps = {
                    get_item_or_attr(cap, "name").lower():
                        cap for cap in caps_data
                } if caps_data else {}

                # Set TLS capabilities
                self._set_tls_capabilities(caps)

                # Set connection attributes capabilities
                if "attributes" in self.settings:
                    conn_attrs = self.settings["attributes"]
                    self.protocol.set_capabilities(
                        session_connect_attrs=conn_attrs)

                # Set compression capabilities
                compression = self.settings.get("compression", "preferred")
                algorithms = self.settings.get("compression-algorithms")
                algorithm = None if compression == "disabled" \
                    else self._set_compression_capabilities(caps,
                                                            compression,
                                                            algorithms)
                self._authenticate()
                self.protocol.set_compression(algorithm)
                return
            except (socket.error, RuntimeError) as err:
                error = err
                router.set_unavailable()

        # Python 2.7 does not raise a socket.timeout exception when using
        # settimeout(), but it raises a socket.error with errno.EAGAIN (11)
        # or errno.EINPROGRESS (115) if connect-timeout value is too low
        if error is not None and isinstance(error, socket.timeout):
            if len(self._routers) <= 1:
                raise TimeoutError("Connection attempt to the server was "
                                   "aborted. Timeout of {0} ms was exceeded"
                                   "".format(self._connect_timeout))
            raise TimeoutError("All server connection attempts were aborted. "
                               "Timeout of {0} ms was exceeded for each "
                               "selected server".format(self._connect_timeout))
        if len(self._routers) <= 1:
            raise InterfaceError("Cannot connect to host: {0}".format(error))
        raise InterfaceError("Unable to connect to any of the target hosts",
                             4001)

    def _set_tls_capabilities(self, caps):
        """Set the TLS capabilities.

        Args:
            caps (dict): Dictionary with the server capabilities.

        Raises:
            :class:`mysqlx.OperationalError`: If SSL is not enabled at the
                                             server.
            :class:`mysqlx.RuntimeError`: If support for SSL is not available
                                          in Python.

        .. versionadded:: 8.0.21
        """
        if self.settings.get("ssl-mode") == SSLMode.DISABLED:
            return

        if self.stream.is_socket():
            if self.settings.get("ssl-mode"):
                _LOGGER.warning("SSL not required when using Unix socket.")
            return

        if "tls" not in caps:
            self.close_connection()
            raise OperationalError("SSL not enabled at server")

        is_ol7 = False
        if platform.system() == "Linux":
            distname, version, _ = linux_distribution()
            try:
                is_ol7 = "Oracle Linux" in distname and \
                    version.split(".")[0] == "7"
            except IndexError:
                is_ol7 = False

        if sys.version_info < (2, 7, 9) and not is_ol7:
            self.close_connection()
            raise RuntimeError("The support for SSL is not available for "
                               "this Python version")

        self.protocol.set_capabilities(tls=True)
        self.stream.set_ssl(self.settings.get("tls-versions", None),
                            self.settings.get("ssl-mode", SSLMode.REQUIRED),
                            self.settings.get("ssl-ca"),
                            self.settings.get("ssl-crl"),
                            self.settings.get("ssl-cert"),
                            self.settings.get("ssl-key"),
                            self.settings.get("tls-ciphersuites"))
        if "attributes" in self.settings:
            conn_attrs = self.settings["attributes"]
            self.protocol.set_capabilities(session_connect_attrs=conn_attrs)

    def _set_compression_capabilities(self, caps, compression,
                                      algorithms=None):
        """Set the compression capabilities.

        If compression is available, negociates client and server algorithms.
        By trying to find an algorithm from the requested compression
        algorithms list, which is supported by the server.

        If no compression algorithms list is provided, the following priority
        is used:

        1) zstd_stream
        2) lz4_message
        3) deflate_stream

        Args:
            caps (dict): Dictionary with the server capabilities.
            compression (str): The compression connection setting.
            algorithms (list): List of requested compression algorithms.

        Returns:
            str: The compression algorithm.

        .. versionadded:: 8.0.21
        .. versionchanged:: 8.0.22
        """
        compression_data = caps.get("compression")
        if compression_data is None:
            msg = "Compression requested but the server does not support it"
            if compression == "required":
                raise NotSupportedError(msg)
            _LOGGER.warning(msg)
            return None

        compression_dict = {}
        if isinstance(compression_data, dict):  # C extension is being used
            for fld in compression_data["value"]["obj"]["fld"]:
                compression_dict[fld["key"]] = [
                    value["scalar"]["v_string"]["value"].decode("utf-8")
                    for value in fld["value"]["array"]["value"]
                ]
        else:
            for fld in compression_data.value.obj.fld:
                compression_dict[fld.key] = [
                    value.scalar.v_string.value.decode("utf-8")
                    for value in fld.value.array.value
                ]

        server_algorithms = compression_dict.get("algorithm", [])
        algorithm = None

        # Try to find an algorithm from the requested compression algorithms
        # list, which is supported by the server
        if algorithms:
            # Resolve compression algorithms aliases and ignore unsupported
            client_algorithms = [
                COMPRESSION_ALGORITHMS[item] for item in algorithms
                if item in COMPRESSION_ALGORITHMS
            ]
            matched = [
                item for item in client_algorithms
                if item in server_algorithms
            ]
            if matched:
                algorithm = COMPRESSION_ALGORITHMS.get(matched[0])
            elif compression == "required":
                raise InterfaceError("The connection compression is set as "
                                     "required, but none of the provided "
                                     "compression algorithms are supported.")
            else:
                return None  # Disable compression

        # No compression algorithms list was provided or couldn't found one
        # supported by the server
        if algorithm is None:
            if HAVE_ZSTD and "zstd_stream" in server_algorithms:
                algorithm = "zstd_stream"
            elif HAVE_LZ4 and "lz4_message" in server_algorithms:
                algorithm = "lz4_message"
            else:
                algorithm = "deflate_stream"

        if algorithm not in server_algorithms:
            msg = ("Compression requested but the compression algorithm "
                   "negotiation failed")
            if compression == "required":
                raise InterfaceError(msg)
            _LOGGER.warning(msg)
            return None

        self.protocol.set_capabilities(compression={"algorithm": algorithm})
        return algorithm

    def _authenticate(self):
        """Authenticate with the MySQL server."""
        auth = self.settings.get("auth")
        if auth:
            if auth == Auth.PLAIN:
                self._authenticate_plain()
            elif auth == Auth.SHA256_MEMORY:
                self._authenticate_sha256_memory()
            elif auth == Auth.MYSQL41:
                self._authenticate_mysql41()
        elif self.stream.is_secure():
            # Use PLAIN if no auth provided and connection is secure
            self._authenticate_plain()
        else:
            # Use MYSQL41 if connection is not secure
            try:
                self._authenticate_mysql41()
            except InterfaceError:
                pass
            else:
                return
            # Try SHA256_MEMORY if MYSQL41 fails
            try:
                self._authenticate_sha256_memory()
            except InterfaceError as err:
                raise InterfaceError("Authentication failed using MYSQL41 and "
                                     "SHA256_MEMORY, check username and "
                                     f"password or try a secure connection err:{err}")

    def _authenticate_mysql41(self):
        """Authenticate with the MySQL server using `MySQL41AuthPlugin`."""
        plugin = MySQL41AuthPlugin(self._user, self._password)
        self.protocol.send_auth_start(plugin.auth_name())
        extra_data = self.protocol.read_auth_continue()
        self.protocol.send_auth_continue(plugin.auth_data(extra_data))
        self.protocol.read_auth_ok()

    def _authenticate_plain(self):
        """Authenticate with the MySQL server using `PlainAuthPlugin`."""
        if not self.stream.is_secure():
            raise InterfaceError("PLAIN authentication is not allowed via "
                                 "unencrypted connection")
        plugin = PlainAuthPlugin(self._user, self._password)
        self.protocol.send_auth_start(plugin.auth_name(),
                                      auth_data=plugin.auth_data())
        self.protocol.read_auth_ok()

    def _authenticate_sha256_memory(self):
        """Authenticate with the MySQL server using `Sha256MemoryAuthPlugin`."""
        plugin = Sha256MemoryAuthPlugin(self._user, self._password)
        self.protocol.send_auth_start(plugin.auth_name())
        extra_data = self.protocol.read_auth_continue()
        self.protocol.send_auth_continue(plugin.auth_data(extra_data))
        self.protocol.read_auth_ok()

    def _deallocate_statement(self, statement):
        """Deallocates statement.

        Args:
            statement (Statement): A `Statement` based type object.
        """
        if statement.prepared:
            self.protocol.send_prepare_deallocate(statement.stmt_id)
            self._prepared_stmt_ids.remove(statement.stmt_id)
            statement.prepared = False

    def _prepare_statement(self, msg_type, msg, statement):
        """Prepares a statement.

        Args:
            msg_type (str): Message ID string.
            msg (mysqlx.protobuf.Message): MySQL X Protobuf Message.
            statement (Statement): A `Statement` based type object.
        """
        try:
            self.fetch_active_result()
            self.protocol.send_prepare_prepare(msg_type, msg, statement)
        except NotSupportedError:
            self._prepared_stmt_supported = False
            return
        self._prepared_stmt_ids.append(statement.stmt_id)
        statement.prepared = True

    def _execute_prepared_pipeline(self, msg_type, msg, statement):
        """Executes the prepared statement pipeline.

        Args:
            msg_type (str): Message ID string.
            msg (mysqlx.protobuf.Message): MySQL X Protobuf Message.
            statement (Statement): A `Statement` based type object.
        """
        # For old servers without prepared statement support
        if not self._prepared_stmt_supported:
            # Crud::<Operation>
            self.protocol.send_msg_without_ps(msg_type, msg, statement)
            return

        if statement.deallocate_prepare_execute:
            # Prepare::Deallocate + Prepare::Prepare + Prepare::Execute
            self._deallocate_statement(statement)
            self._prepare_statement(msg_type, msg, statement)
            if not self._prepared_stmt_supported:
                self.protocol.send_msg_without_ps(msg_type, msg, statement)
                return
            self.protocol.send_prepare_execute(msg_type, msg, statement)
            statement.deallocate_prepare_execute = False
            statement.reset_exec_counter()
        elif statement.prepared and not statement.changed:
            # Prepare::Execute
            self.protocol.send_prepare_execute(msg_type, msg, statement)
        elif statement.changed and not statement.repeated:
            # Crud::<Operation>
            self._deallocate_statement(statement)
            self.protocol.send_msg_without_ps(msg_type, msg, statement)
            statement.changed = False
            statement.reset_exec_counter()
        elif not statement.changed and not statement.repeated:
            # Prepare::Prepare + Prepare::Execute
            if not statement.prepared:
                self._prepare_statement(msg_type, msg, statement)
            if not self._prepared_stmt_supported:
                self.protocol.send_msg_without_ps(msg_type, msg, statement)
                return
            self.protocol.send_prepare_execute(msg_type, msg, statement)
        elif statement.changed and statement.repeated:
            # Prepare::Deallocate + Crud::<Operation>
            self._deallocate_statement(statement)
            self.protocol.send_msg_without_ps(msg_type, msg, statement)
            statement.changed = False
            statement.reset_exec_counter()

        statement.increment_exec_counter()

    @catch_network_exception
    def send_sql(self, statement):
        """Execute a SQL statement.

        Args:
            sql (str): The SQL statement.

        Raises:
            :class:`mysqlx.ProgrammingError`: If the SQL statement is not a
                                              valid string.
        """
        sql = statement.sql
        if self.protocol is None:
            raise OperationalError("MySQLx Connection not available")
        if not isinstance(sql, str):
            raise ProgrammingError("The SQL statement is not a valid string")
        else:
            msg_type, msg = self.protocol.build_execute_statement(
                "sql", sql)
        self.protocol.send_msg_without_ps(msg_type, msg, statement)
        return SqlResult(self)

    @catch_network_exception
    def send_insert(self, statement):
        """Send an insert statement.

        Args:
            statement (`Statement`): It can be :class:`mysqlx.InsertStatement`
                                     or :class:`mysqlx.AddStatement`.

        Returns:
            :class:`mysqlx.Result`: A result object.
        """
        if self.protocol is None:
            raise OperationalError("MySQLx Connection not available")
        msg_type, msg = self.protocol.build_insert(statement)
        self.protocol.send_msg(msg_type, msg)
        ids = None
        if isinstance(statement, AddStatement):
            ids = statement.ids
        return Result(self, ids)

    @catch_network_exception
    def send_find(self, statement):
        """Send an find statement.

        Args:
            statement (`Statement`): It can be :class:`mysqlx.SelectStatement`
                                     or :class:`mysqlx.FindStatement`.

        Returns:
            `Result`: It can be class:`mysqlx.DocResult` or
                      :class:`mysqlx.RowResult`.
        """
        msg_type, msg = self.protocol.build_find(statement)
        self._execute_prepared_pipeline(msg_type, msg, statement)
        return DocResult(self) if statement.is_doc_based() else RowResult(self)

    @catch_network_exception
    def send_delete(self, statement):
        """Send an delete statement.

        Args:
            statement (`Statement`): It can be :class:`mysqlx.RemoveStatement`
                                     or :class:`mysqlx.DeleteStatement`.

        Returns:
            :class:`mysqlx.Result`: The result object.
        """
        msg_type, msg = self.protocol.build_delete(statement)
        self._execute_prepared_pipeline(msg_type, msg, statement)
        return Result(self)

    @catch_network_exception
    def send_update(self, statement):
        """Send an delete statement.

        Args:
            statement (`Statement`): It can be :class:`mysqlx.ModifyStatement`
                                     or :class:`mysqlx.UpdateStatement`.

        Returns:
            :class:`mysqlx.Result`: The result object.
        """
        msg_type, msg = self.protocol.build_update(statement)
        self._execute_prepared_pipeline(msg_type, msg, statement)
        return Result(self)

    @catch_network_exception
    def execute_nonquery(self, namespace, cmd, raise_on_fail, fields=None):
        """Execute a non query command.

        Args:
            namespace (str): The namespace.
            cmd (str): The command.
            raise_on_fail (bool): `True` to raise on fail.
            fields (Optional[dict]): The message fields.

        Raises:
            :class:`mysqlx.OperationalError`: On errors.

        Returns:
            :class:`mysqlx.Result`: The result object.
        """
        try:
            msg_type, msg = \
                self.protocol.build_execute_statement(namespace, cmd, fields)
            self.protocol.send_msg(msg_type, msg)
            return Result(self)
        except OperationalError:
            if raise_on_fail:
                raise

    @catch_network_exception
    def execute_sql_scalar(self, sql):
        """Execute a SQL scalar.

        Args:
            sql (str): The SQL statement.

        Raises:
            :class:`mysqlx.InterfaceError`: If no data found.

        Returns:
            :class:`mysqlx.Result`: The result.
        """
        msg_type, msg = self.protocol.build_execute_statement("sql", sql)
        self.protocol.send_msg(msg_type, msg)
        result = RowResult(self)
        result.fetch_all()
        if result.count == 0:
            raise InterfaceError("No data found")
        return result[0][0]

    @catch_network_exception
    def get_row_result(self, cmd, fields):
        """Returns the row result.

        Args:
            cmd (str): The command.
            fields (dict): The message fields.

        Returns:
            :class:`mysqlx.RowResult`: The result object.
        """
        msg_type, msg = \
            self.protocol.build_execute_statement("mysqlx", cmd, fields)
        self.protocol.send_msg(msg_type, msg)
        return RowResult(self)

    @catch_network_exception
    def read_row(self, result):
        """Read row.

        Args:
            result (:class:`mysqlx.RowResult`): The result object.
        """
        return self.protocol.read_row(result)

    @catch_network_exception
    def close_result(self, result):
        """Close result.

        Args:
            result (:class:`mysqlx.Result`): The result object.
        """
        self.protocol.close_result(result)

    @catch_network_exception
    def get_column_metadata(self, result):
        """Get column metadata.

        Args:
            result (:class:`mysqlx.Result`): The result object.
        """
        return self.protocol.get_column_metadata(result)

    def get_next_statement_id(self):
        """Returns the next statement ID.

        Returns:
            int: A statement ID.

        .. versionadded:: 8.0.16
        """
        self._stmt_counter += 1
        return self._stmt_counter

    def is_open(self):
        """Check if connection is open.

        Returns:
            bool: `True` if connection is open.
        """
        return self.stream.is_open()

    def set_server_disconnected(self, reason):
        """Set the disconnection message from the server.

        Args:
            reason (str): disconnection reason from the server.
        """
        self._server_disconnected = True
        self._server_disconnected_reason = reason

    def is_server_disconnected(self):
        """Verify if the session has been disconnect from the server.

        Returns:
            bool: `True` if the connection has been closed from the server
                  otherwise `False`.
        """
        return self._server_disconnected

    def get_disconnected_reason(self):
        """Get the disconnection message sent by the server.

        Returns:
            string: disconnection reason from the server.
        """
        return self._server_disconnected_reason

    def disconnect(self):
        """Disconnect from server."""
        if not self.is_open():
            return
        self.stream.close()

    def close_session(self):
        """Close a sucessfully authenticated session."""
        if not self.is_open():
            return

        try:
            # Fetch any active result
            self.fetch_active_result()
            # Deallocate all prepared statements
            if self._prepared_stmt_supported:
                for stmt_id in self._prepared_stmt_ids:
                    self.protocol.send_prepare_deallocate(stmt_id)
                self._stmt_counter = 0
            # Send session close
            self.protocol.send_close()
            self.protocol.read_ok()
        except (InterfaceError, OperationalError, OSError) as err:
            _LOGGER.warning("Warning: An error occurred while attempting to "
                            "close the connection: {}".format(err))
        finally:
            # The remote connection with the server has been lost,
            # close the connection locally.
            self.stream.close()

    def reset_session(self):
        """Reset a sucessfully authenticated session."""
        if not self.is_open():
            return
        if self._active_result is not None:
            self._active_result.fetch_all()
        try:
            self.keep_open = self.protocol.send_reset(self.keep_open)
        except (InterfaceError, OperationalError) as err:
            _LOGGER.warning("Warning: An error occurred while attempting to "
                            "reset the session: {}".format(err))

    def close_connection(self):
        """Announce to the server that the client wants to close the
        connection. Discards any session state of the server.
        """
        if not self.is_open():
            return
        if self._active_result is not None:
            self._active_result.fetch_all()
        self.protocol.send_connection_close()
        self.protocol.read_ok()
        self.stream.close()


class PooledConnection(Connection):
    """Class to hold :class:`Connection` instances in a pool.

    PooledConnection is used by :class:`ConnectionPool` to facilitate the
    connection to return to the pool once is not required, more specifically
    once the close_session() method is invoked. It works like a normal
    Connection except for methods like close() and sql().

    The close_session() method will add the connection back to the pool rather
    than disconnecting from the MySQL server.

    The sql() method is used to execute sql statements.

    Args:
        pool (ConnectionPool): The pool where this connection must return.

    .. versionadded:: 8.0.13
    """
    def __init__(self, pool):
        if not isinstance(pool, ConnectionPool):
            raise AttributeError("pool should be a ConnectionPool object")
        super(PooledConnection, self).__init__(pool.cnx_config)
        self.pool = pool
        self.host = pool.cnx_config["host"]
        self.port = pool.cnx_config["port"]

    def close_connection(self):
        """Closes the connection.

        This method closes the socket.
        """
        super(PooledConnection, self).close_session()

    def close_session(self):
        """Do not close, but add connection back to pool.

        The close_session() method does not close the connection with the
        MySQL server. The connection is added back to the pool so it
        can be reused.

        When the pool is configured to reset the session, the session
        state will be cleared by re-authenticating the user once the connection
        is get from the pool.
        """
        self.pool.add_connection(self)

    def reconnect(self):
        """Reconnect this connection.
        """
        if self._active_result is not None:
            self._active_result.fetch_all()
        self._authenticate()

    def reset(self):
        """Reset the connection.

        Resets the connection by re-authenticate.
        """
        self.reconnect()

    def sql(self, sql):
        """Creates a :class:`mysqlx.SqlStatement` object to allow running the
        SQL statement on the target MySQL Server.

        Args:
            sql (string): The SQL statement to be executed.

        Returns:
            mysqlx.SqlStatement: SqlStatement object.
        """
        return SqlStatement(self, sql)


class ConnectionPool(queue.Queue):
    """This class represents a pool of connections.

    Initializes the Pool with the given name and settings.

    Args:
        name (str): The name of the pool, used to track a single pool per
                    combination of host and user.
        **kwargs:
            max_size (int): The maximun number of connections to hold in
                            the pool.
            reset_session (bool): If the connection should be reseted when
                                  is taken from the pool.
            max_idle_time (int): The maximum number of milliseconds to allow
                                 a connection to be idle in the queue before
                                 being closed. Zero value means infinite.
            queue_timeout (int): The maximum number of milliseconds a
                                 request will wait for a connection to
                                 become available. A zero value means
                                 infinite.
            priority (int): The router priority, to choose this pool over
                            other with lower priority.

    Raises:
        :class:`mysqlx.PoolError` on errors.

    .. versionadded:: 8.0.13
    """
    def __init__(self, name, **kwargs):
        self._set_pool_name(name)
        self._open_sessions = 0
        self._connections_openned = []
        self._available = True
        self._timeout = 0
        self._timeout_stamp = datetime.now()
        self.pool_max_size = kwargs.get("max_size", 25)
        # Can't invoke super due to Queue not is a new-style class
        queue.Queue.__init__(self, self.pool_max_size)
        self.reset_session = kwargs.get("reset_session", True)
        self.max_idle_time = kwargs.get("max_idle_time", 25)
        self.settings = kwargs
        self.queue_timeout = kwargs.get("queue_timeout", 25)
        self.priority = kwargs.get("priority", 0)
        self.cnx_config = kwargs
        self.host = kwargs['host']
        self.port = kwargs['port']

    def _set_pool_name(self, pool_name):
        r"""Set the name of the pool.

        This method checks the validity and sets the name of the pool.

        Args:
            pool_name (str): The pool name.

        Raises:
            AttributeError: If the pool_name contains illegal characters
                            ([^a-zA-Z0-9._\-*$#]) or is longer than
                            connection._CNX_POOL_MAX_NAME_SIZE.
        """
        if _CNX_POOL_NAME_REGEX.search(pool_name):
            raise AttributeError(
                "Pool name '{0}' contains illegal characters".format(pool_name))
        if len(pool_name) > _CNX_POOL_MAX_NAME_SIZE:
            raise AttributeError(
                "Pool name '{0}' is too long".format(pool_name))
        self.name = pool_name

    @property
    def open_connections(self):
        """Returns the number of open connections that can return to this pool.
        """
        return len(self._connections_openned)

    def remove_connection(self, cnx=None):
        """Removes a connection from this pool.

        Args:
            cnx (PooledConnection): The connection object.
        """
        self._connections_openned.remove(cnx)

    def remove_connections(self):
        """Removes all the connections from the pool."""
        while self.qsize() > 0:
            try:
                cnx = self.get(block=True,
                               timeout=self.queue_timeout)
            except queue.Empty:
                pass
            else:
                try:
                    cnx.close_connection()
                except (RuntimeError, socket.error, InterfaceError):
                    pass
                finally:
                    self.remove_connection(cnx)

    def add_connection(self, cnx=None):
        """Adds a connection to this pool.

        This method instantiates a Connection using the configuration passed
        when initializing the ConnectionPool instance or using the set_config()
        method.
        If cnx is a Connection instance, it will be added to the queue.

        Args:
            cnx (PooledConnection): The connection object.

        Raises:
            PoolError: If no configuration is set, if no more connection can
                       be added (maximum reached) or if the connection can not
                       be instantiated.
        """
        if not self.cnx_config:
            raise PoolError("Connection configuration not available")

        if self.full():
            raise PoolError("Failed adding connection; queue is full")

        if not cnx:
            cnx = PooledConnection(self)
            # mysqlx_wait_timeout is only available on MySQL 8
            ver = cnx.sql(_SELECT_VERSION_QUERY).execute().fetch_all()[0][0]
            if tuple([int(n) for n in ver.split("-")[0].split(".")]) > \
                (8, 0, 10):
                cnx.sql("set mysqlx_wait_timeout = {}"
                        "".format(self.max_idle_time)).execute()
            self._connections_openned.append(cnx)
        else:
            if not isinstance(cnx, PooledConnection):
                raise PoolError(
                    "Connection instance not subclass of PooledSession.")
            if cnx.is_server_disconnected():
                self.remove_connections()
                cnx.close()

        self.queue_connection(cnx)

    def queue_connection(self, cnx):
        """Put connection back in the queue:

        This method is putting a connection back in the queue.
        It will not acquire a lock as the methods using _queue_connection() will
        have it set.

        Args:
            PooledConnection: The connection object.

        Raises:
            PoolError: On errors.
        """
        if not isinstance(cnx, PooledConnection):
            raise PoolError(
                "Connection instance not subclass of PooledSession.")

        # Reset the connection
        if self.reset_session:
            cnx.reset_session()
        try:
            self.put(cnx, block=False)
        except queue.Full:
            PoolError("Failed adding connection; queue is full")

    def track_connection(self, connection):
        """Tracks connection in order of close it when client.close() is invoke.
        """
        self._connections_openned.append(connection)

    def __str__(self):
        return self.name

    def available(self):
        """Returns if this pool is available for pool connections from it.

        Returns:
            bool: True if this pool is available else False.
        .. versionadded:: 8.0.20
        """
        return self._available

    def set_unavailable(self, time_out=-1):
        """Sets this pool unavailable for a period of time (in seconds).

        .. versionadded:: 8.0.20
        """
        if self._available:
            _LOGGER.warning("ConnectionPool.set_unavailable pool: %s "
                            "time_out: %s", self, time_out)
            self._available = False
            self._timeout_stamp = datetime.now()
            self._timeout = time_out

    def set_available(self):
        """Sets this pool available for pool connections from it.

        .. versionadded:: 8.0.20
        """
        self._available = True
        self._timeout_stamp = datetime.now()

    def get_timeout_stamp(self):
        """Returns the penalized time (timeout) and the time at the penalty.

        Returns:
            tuple: penalty seconds (int), timestamp at penalty (datetime object)
        .. versionadded:: 8.0.20
        """
        return (self._timeout, self._timeout_stamp)

    def close(self):
        """Empty this ConnectionPool.
        """
        for cnx in self._connections_openned:
            cnx.close_connection()


class PoolsManager(object):
    """Manages a pool of connections for a host or hosts in routers.

    This class handles all the pools of Connections.

    .. versionadded:: 8.0.13
    """
    __instance = None
    __pools = {}

    def __new__(cls):
        if PoolsManager.__instance is None:
            PoolsManager.__instance = object.__new__(cls)
            PoolsManager.__pools = {}
        return PoolsManager.__instance

    def _pool_exists(self, client_id, pool_name):
        """Verifies if a pool exists with the given name.

        Args:
            client_id (str): The client id.
            pool_name (str): The name of the pool.

        Returns:
            bool: Returns `True` if the pool exists otherwise `False`.
        """
        pools = self.__pools.get(client_id, [])
        for pool in pools:
            if pool.name == pool_name:
                return True
        return False

    def _get_pools(self, settings):
        """Retrieves a list of pools that shares the given settings.

        Args:
            settings (dict): the configuration of the pool.

        Returns:
            list: A list of pools that shares the given settings.
        """
        available_pools = []
        pool_names = []
        connections_settings = self._get_connections_settings(settings)

        # Generate the names of the pools this settings can connect to
        for router_name, _ in connections_settings:
            pool_names.append(router_name)

        # Generate the names of the pools this settings can connect to
        for pool in self.__pools.get(settings.get("client_id", "No id"), []):
            if pool.name in pool_names:
                available_pools.append(pool)
        return available_pools

    def _get_connections_settings(self, settings):
        """Generates a list of separated connection settings for each host.

        Gets a list of connection settings for each host or router found in the
        given settings.

        Args:
            settings (dict): The configuration for the connections.

        Returns:
            list: A list of connections settings
        """
        pool_settings = settings.copy()
        routers = pool_settings.get("routers", [])
        connections_settings = []
        if "routers" in pool_settings:
            pool_settings.pop("routers")
        if "host" in pool_settings and "port" in pool_settings:
            routers.append({"priority": 100,
                            "weight": 0,
                            "host": pool_settings["host"],
                            "port": pool_settings["port"]})
        # Order routers
        routers.sort(key=lambda x: (x["priority"], -x.get("weight", 0)))
        for router in routers:
            connection_settings = pool_settings.copy()
            connection_settings["host"] = router["host"]
            connection_settings["port"] = router["port"]
            connection_settings["priority"] = router["priority"]
            connection_settings["weight"] = router.get("weight", 0)
            connections_settings.append(
                (generate_pool_name(**connection_settings),
                 connection_settings))
        return connections_settings

    def create_pool(self, cnx_settings):
        """Creates a `ConnectionPool` instance to hold the connections.

        Creates a `ConnectionPool` instance to hold the connections only if
        no other pool exists with the same configuration.

        Args:
            cnx_settings (dict): The configuration for the connections.
        """
        connections_settings = self._get_connections_settings(cnx_settings)

        # Subscribe client if it does not exists
        if cnx_settings.get("client_id", "No id") not in self.__pools:
            self.__pools[cnx_settings.get("client_id", "No id")] = []

        # Create a pool for each router
        for router_name, settings in connections_settings:
            if self._pool_exists(cnx_settings.get("client_id", "No id"),
                                 router_name):
                continue
            else:
                pool = self.__pools.get(cnx_settings.get("client_id", "No id"),
                                        [])
                pool.append(ConnectionPool(router_name, **settings))

    def _get_random_pool(self, pool_list):
        """Get a random router from the group with the given priority.

        Returns:
            Router: a random router.

        .. versionadded:: 8.0.20
        """
        if not pool_list:
            return None
        if len(pool_list) == 1:
            return pool_list[0]

        last = len(pool_list) - 1
        index = random.randint(0, last)
        return pool_list[index]

    def get_sublist(self, pools, index, cur_priority):
        sublist = []
        next_priority = None
        while index < len(pools):
            next_priority = pools[index].priority
            if cur_priority == next_priority and pools[index].available():
                sublist.append(pools[index])
            elif cur_priority != next_priority:
                break
            index += 1
        return sublist

    def _get_next_pool(self, pools, cur_priority):
        index = 0
        for pool in pools:
            if pool.available() and cur_priority == pool.priority:
                break
            index += 1
        subpool = []
        while not subpool and index < len(pools):
            subpool = self.get_sublist(pools, index, cur_priority)
            index += 1
        return self._get_random_pool(subpool)

    def _get_next_priority(self, pools, cur_priority=None):
        if cur_priority is None and pools:
            return pools[0].priority
        else:
            # find the first pool that does not share the same priority
            for t_pool in pools:
                if t_pool.available():
                    cur_priority = t_pool.priority
                    return cur_priority
        return pools[0].priority

    def _check_unavailable_pools(self, settings, revive=None):
        pools = self._get_pools(settings)
        for pool in pools:
            if pool.available():
                continue
            timeout, timeout_stamp = pool.get_timeout_stamp()
            if revive:
                timeout = revive
            if datetime.now() > (timeout_stamp + timedelta(seconds=timeout)):
                pool.set_available()

    def get_connection(self, settings):
        """Get a connection from the pool.

        This method returns an `PooledConnection` instance which has a reference
        to the pool that created it, and can be used as a normal Connection.

        When the MySQL connection is not connected, a reconnect is attempted.

        Raises:
            :class:`PoolError`: On errors.

        Returns:
            PooledConnection: A pooled connection object.
        """
        def set_mysqlx_wait_timeout(cnx):
            ver = cnx.sql(_SELECT_VERSION_QUERY).execute().fetch_all()[0][0]
            # mysqlx_wait_timeout is only available on MySQL 8
            if tuple([int(n) for n in
                      ver.split("-")[0].split(".")]) > (8, 0, 10):
                cnx.sql("set mysqlx_wait_timeout = {}"
                        "".format(pool.max_idle_time)).execute()

        pools = self._get_pools(settings)
        cur_priority = settings.get("cur_priority", None)
        error_list = []
        self._check_unavailable_pools(settings)
        cur_priority = self._get_next_priority(pools, cur_priority)
        if cur_priority is None:
            raise PoolError("Unable to connect to any of the target hosts. "
                            "No pool is available.")
        settings["cur_priority"] = cur_priority
        pool = self._get_next_pool(pools, cur_priority)
        while pool is not None:
            try:
                # Check connections aviability in this pool
                if pool.qsize() > 0:
                    # We have connections in pool, try to return a working one
                    with threading.RLock():
                        try:
                            cnx = pool.get(block=True,
                                           timeout=pool.queue_timeout)
                        except queue.Empty:
                            raise PoolError(
                                "Failed getting connection; pool exhausted")
                        try:
                            if cnx.is_server_disconnected():
                                pool.remove_connections()
                            # Only reset the connection by re-authentification
                            # if the connection was unable to keep open by the
                            # server
                            if not cnx.keep_open:
                                cnx.reset()
                            set_mysqlx_wait_timeout(cnx)
                        except (RuntimeError, socket.error, InterfaceError):
                            # Unable to reset connection, close and remove
                            try:
                                cnx.close_connection()
                            except (RuntimeError, socket.error, InterfaceError):
                                pass
                            finally:
                                pool.remove_connection(cnx)
                            # By WL#13222 all idle sessions that connect to the
                            # same endpoint should be removed from the pool.
                            while pool.qsize() > 0:
                                try:
                                    cnx = pool.get(block=True,
                                                   timeout=pool.queue_timeout)
                                except queue.Empty:
                                    pass
                                else:
                                    try:
                                        cnx.close_connection()
                                    except (RuntimeError, socket.error, InterfaceError):
                                        pass
                                    finally:
                                        pool.remove_connection(cnx)
                            # Connection was closed by the server, create new
                            try:
                                cnx = PooledConnection(pool)
                                pool.track_connection(cnx)
                                cnx.connect()
                                set_mysqlx_wait_timeout(cnx)
                            except (RuntimeError, socket.error, InterfaceError):
                                pass
                            finally:
                                # Server must be down, take down idle
                                # connections from this pool
                                while pool.qsize() > 0:
                                    try:
                                        cnx = pool.get(block=True,
                                                       timeout=pool.queue_timeout)
                                        cnx.close_connection()
                                        pool.remove_connection(cnx)
                                    except (RuntimeError, socket.error, InterfaceError):
                                        pass
                        return cnx
                elif pool.open_connections < pool.pool_max_size:
                    # No connections in pool, but we can open a new one
                    cnx = PooledConnection(pool)
                    pool.track_connection(cnx)
                    cnx.connect()
                    set_mysqlx_wait_timeout(cnx)
                    return cnx
                else:
                    # Pool is exaust so the client needs to wait
                    with threading.RLock():
                        try:
                            cnx = pool.get(block=True,
                                           timeout=pool.queue_timeout)
                            cnx.reset()
                            set_mysqlx_wait_timeout(cnx)
                            return cnx
                        except queue.Empty:
                            raise PoolError("pool max size has been reached")
            except (InterfaceError, TimeoutError, PoolError) as err:
                error_list.append("pool: {} error: {}".format(pool, err))
                if isinstance(err, PoolError):
                    # Pool can be exhaust now but can be ready again in no time,
                    # e.g a connection is returned to the pool.
                    pool.set_unavailable(2)
                else:
                    self.set_pool_unavailable(pool, err)

                self._check_unavailable_pools(settings)
                # Try next pool with the same priority
                pool = self._get_next_pool(pools, cur_priority)

                if pool is None:
                    cur_priority = self._get_next_priority(pools, cur_priority)
                    settings["cur_priority"] = cur_priority
                    pool = self._get_next_pool(pools, cur_priority)
                    if pool is None:
                        msg = "\n  ".join(error_list)
                        raise PoolError("Unable to connect to any of the "
                                        "target hosts: [\n  {}\n]".format(msg))
                continue

        raise PoolError("Unable to connect to any of the target hosts")

    def close_pool(self, cnx_settings):
        """Closes the connections in the pools

        Returns:
            int: The number of closed pools
        """
        pools = self._get_pools(cnx_settings)
        for pool in pools:
            pool.close()
            # Remove the pool
            if cnx_settings.get("client_id", None) is not None:
                client_pools = self.__pools.get(cnx_settings.get("client_id"))
                if pool in client_pools:
                    client_pools.remove(pool)
        return len(pools)

    def set_pool_unavailable(self, pool, err):
        """Sets a pool as unavailable.

        The time a pool is set unavailable depends on the given error message
        or the error number.

        Args:
            pool (ConnectionPool): The pool to set unavailable.
            err (Exception): The raised exception raised by a connection belonging
                             to the pool.
        """
        penalty = None
        try:
            err_no = err.errno
            penalty = _TIMEOUT_PENALTIES_BY_ERR_NO[err_no]
        except (AttributeError, KeyError):
            pass
        if not penalty:
            err_msg = err.msg
            for timeout_penalty in _TIMEOUT_PENALTIES:
                if timeout_penalty in err_msg:
                    penalty = _TIMEOUT_PENALTIES[timeout_penalty]
        if penalty:
            pool.set_unavailable(penalty)
        else:
            # Other errors are severe punished
            pool.set_unavailable(100000)

class Session(object):
    """Enables interaction with a X Protocol enabled MySQL Product.

    The functionality includes:

    - Accessing available schemas.
    - Schema management operations.
    - Retrieval of connection information.

    Args:
        settings (dict): Connection data used to connect to the database.
    """

    def __init__(self, settings):
        self.use_pure = settings.get("use-pure", Protobuf.use_pure)
        self._settings = settings

        # Check for DNS SRV
        if settings.get("host") and settings.get("dns-srv"):
            if not HAVE_DNSPYTHON:
                raise InterfaceError("MySQL host configuration requested DNS "
                                     "SRV. This requires the Python dnspython "
                                     "module. Please refer to documentation")
            try:
                srv_records = dns.resolver.query(settings["host"], "SRV")
            except dns.exception.DNSException:
                raise InterfaceError("Unable to locate any hosts for '{0}'"
                                     "".format(settings["host"]))
            self._settings["routers"] = []
            for srv in srv_records:
                self._settings["routers"].append({
                    "host": srv.target.to_text(omit_final_dot=True),
                    "port": srv.port,
                    "priority": srv.priority,
                    "weight": srv.weight
                })

        if "connection-attributes" not in self._settings or \
           self._settings["connection-attributes"] != False:
            self._settings["attributes"] = {}
            self._init_attributes()

        if "pooling" in settings and settings["pooling"]:
            # Create pool and retrieve a Connection instance
            PoolsManager().create_pool(settings)
            self._connection = PoolsManager().get_connection(settings)
            if self._connection is None:
                raise PoolError("Connection could not be retrieved from pool")
        else:
            self._connection = Connection(self._settings)
            self._connection.connect()
        # Set default schema
        schema = self._settings.get("schema")
        if schema:
            try:
                self.sql("USE {}".format(quote_identifier(schema))).execute()
            except OperationalError as err:
                # Access denied for user will raise err.errno = 1044
                errmsg = err.msg if err.errno == 1044 \
                    else "Default schema '{}' does not exists".format(schema)
                raise InterfaceError(errmsg, err.errno)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _init_attributes(self):
        """Setup default and user defined connection-attributes."""
        if os.name == "nt":
            if "64" in platform.architecture()[0]:
                platform_arch = 'x86_64'
            elif "32" in platform.architecture()[0]:
                platform_arch = 'i386'
            else:
                platform_arch = platform.architecture()
            os_ver = "Windows-{}".format(platform.win32_ver()[1])
        else:
            platform_arch = platform.machine()
            if platform.system() == "Darwin":
                os_ver = "{}-{}".format("macOS", platform.mac_ver()[0])
            else:
                os_ver = "-".join(linux_distribution()[0:2])

        license_chunks = LICENSE.split(' ')
        if license_chunks[0] == "GPLv2":
            client_license = "GPL-2.0"
        else:
            client_license = "Commercial"

        default_attributes = {
            # Process id
            "_pid": str(os.getpid()),
            # Platform architecture
            "_platform": platform_arch,
            # OS version
            "_os": os_ver,
            # Hostname of the local machine
            "_source_host": socket.gethostname(),
            # Client's name
            "_client_name": "mysql-connector-python",
            # Client's version
            "_client_version": ".".join([str(x) for x in VERSION[0:3]]),
            # Client's License identifier
            "_client_license": client_license
        }
        self._settings["attributes"].update(default_attributes)

        if "connection-attributes" in self._settings:
            for attr_name in self._settings["connection-attributes"]:
                attr_value = self._settings["connection-attributes"][attr_name]
                # Validate name type
                if not isinstance(attr_name, str):
                    raise InterfaceError("Attribute name '{}' must be a string "
                                         "type".format(attr_name))
                # Validate attribute name limit 32 characters
                if len(attr_name) > 32:
                    raise InterfaceError("Attribute name '{}' exceeds 32 "
                                         "characters limit size"
                                         "".format(attr_name))
                # Validate names in connection-attributes cannot start with "_"
                if attr_name.startswith("_"):
                    raise InterfaceError("Key names in 'session-connect-"
                                         "attributes' cannot start with '_', "
                                         "found: {}".format(attr_name))
                # Validate value type
                if not isinstance(attr_value, str):
                    raise InterfaceError("Attribute name '{}' value '{}' must "
                                         "be a string type"
                                         "".format(attr_name, attr_value))

                # Validate attribute value limit 1024 characters
                if len(attr_value) > 1024:
                    raise InterfaceError("Attribute name '{}' value: '{}' "
                                         "exceeds 1024 characters limit size"
                                         "".format(attr_name, attr_value))

                self._settings["attributes"][attr_name] = attr_value

    @property
    def use_pure(self):
        """bool: `True` to use pure Python Protobuf implementation.
        """
        return Protobuf.use_pure

    @use_pure.setter
    def use_pure(self, value):
        if not isinstance(value, bool):
            raise ProgrammingError("'use_pure' option should be True or False")
        Protobuf.set_use_pure(value)

    def is_open(self):
        """Returns `True` if the session is open.

        Returns:
            bool: Returns `True` if the session is open.
        """
        return self._connection.stream.is_open()

    def sql(self, sql):
        """Creates a :class:`mysqlx.SqlStatement` object to allow running the
        SQL statement on the target MySQL Server.

        Args:
            sql (string): The SQL statement to be executed.

        Returns:
            mysqlx.SqlStatement: SqlStatement object.
        """
        return SqlStatement(self._connection, sql)

    def get_connection(self):
        """Returns the underlying connection.

        Returns:
            mysqlx.connection.Connection: The connection object.
        """
        return self._connection

    def get_schemas(self):
        """Returns the list of schemas in the current session.

        Returns:
            `list`: The list of schemas in the current session.

        .. versionadded:: 8.0.12
        """
        result = self.sql("SHOW DATABASES").execute()
        return [row[0] for row in result.fetch_all()]

    def get_schema(self, name):
        """Retrieves a Schema object from the current session by it's name.

        Args:
            name (string): The name of the Schema object to be retrieved.

        Returns:
            mysqlx.Schema: The Schema object with the given name.
        """
        return Schema(self, name)

    def get_default_schema(self):
        """Retrieves a Schema object from the current session by the schema
        name configured in the connection settings.

        Returns:
            mysqlx.Schema: The Schema object with the given name at connect
                           time.
            None: In case the default schema was not provided with the
                  initialization data.

        Raises:
            :class:`mysqlx.ProgrammingError`: If the provided default schema
                                              does not exists.
        """
        schema = self._connection.settings.get("schema")
        if schema:
            res = self.sql(
                _SELECT_SCHEMA_NAME_QUERY.format(escape(schema))
            ).execute().fetch_all()
            try:
                if res[0][0] == schema:
                    return Schema(self, schema)
            except IndexError:
                raise ProgrammingError(
                    "Default schema '{}' does not exists".format(schema))
        return None

    def drop_schema(self, name):
        """Drops the schema with the specified name.

        Args:
            name (string): The name of the Schema object to be retrieved.
        """
        self._connection.execute_nonquery(
            "sql", _DROP_DATABASE_QUERY.format(quote_identifier(name)), True)

    def create_schema(self, name):
        """Creates a schema on the database and returns the corresponding
        object.

        Args:
            name (string): A string value indicating the schema name.
        """
        self._connection.execute_nonquery(
            "sql", _CREATE_DATABASE_QUERY.format(quote_identifier(name)), True)
        return Schema(self, name)

    def start_transaction(self):
        """Starts a transaction context on the server."""
        self._connection.execute_nonquery("sql", "START TRANSACTION", True)

    def commit(self):
        """Commits all the operations executed after a call to
        startTransaction().
        """
        self._connection.execute_nonquery("sql", "COMMIT", True)

    def rollback(self):
        """Discards all the operations executed after a call to
        startTransaction().
        """
        self._connection.execute_nonquery("sql", "ROLLBACK", True)

    def set_savepoint(self, name=None):
        """Creates a transaction savepoint.

        If a name is not provided, one will be generated using the uuid.uuid1()
        function.

        Args:
            name (Optional[string]): The savepoint name.

        Returns:
            string: The savepoint name.
        """
        if name is None:
            name = "{0}".format(uuid.uuid1())
        elif not isinstance(name, str) or len(name.strip()) == 0:
            raise ProgrammingError("Invalid SAVEPOINT name")
        self._connection.execute_nonquery("sql", "SAVEPOINT {0}"
                                          "".format(quote_identifier(name)),
                                          True)
        return name

    def rollback_to(self, name):
        """Rollback to a transaction savepoint with the given name.

        Args:
            name (string): The savepoint name.
        """
        if not isinstance(name, str) or len(name.strip()) == 0:
            raise ProgrammingError("Invalid SAVEPOINT name")
        self._connection.execute_nonquery("sql", "ROLLBACK TO SAVEPOINT {0}"
                                          "".format(quote_identifier(name)),
                                          True)

    def release_savepoint(self, name):
        """Release a transaction savepoint with the given name.

        Args:
            name (string): The savepoint name.
        """
        if not isinstance(name, str) or len(name.strip()) == 0:
            raise ProgrammingError("Invalid SAVEPOINT name")
        self._connection.execute_nonquery("sql", "RELEASE SAVEPOINT {0}"
                                          "".format(quote_identifier(name)),
                                          True)

    def close(self):
        """Closes the session."""
        self._connection.close_session()
        # Set an unconnected connection
        self._connection = Connection(self._settings)

    def close_connections(self):
        """Closes all underliying connections as pooled connections"""
        self._connection.close_connection()


class Client(object):
    """Class defining a client, it stores a connection configuration.

       Args:
           connection_dict (dict): The connection information to connect to a
                                   MySQL server.
           options_dict (dict): The options to configure this client.

       .. versionadded:: 8.0.13
    """
    def __init__(self, connection_dict, options_dict=None):
        self.settings = connection_dict
        if options_dict is None:
            options_dict = {}

        self.sessions = []
        self.client_id = uuid.uuid4()

        self._set_pool_size(options_dict.get("max_size", 25))
        self._set_max_idle_time(options_dict.get("max_idle_time", 0))
        self._set_queue_timeout(options_dict.get("queue_timeout", 0))
        self._set_pool_enabled(options_dict.get("enabled", True))

        self.settings["pooling"] = self.pooling_enabled
        self.settings["max_size"] = self.max_size
        self.settings["client_id"] = self.client_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _set_pool_size(self, pool_size):
        """Set the size of the pool.

        This method sets the size of the pool but it will not resize the pool.

        Args:
            pool_size (int): An integer equal or greater than 0 indicating
                             the pool size.

        Raises:
            :class:`AttributeError`: If the pool_size value is not an integer
                                     greater or equal to 0.
        """
        if isinstance(pool_size, bool) or not isinstance(pool_size, int) or \
           not pool_size > 0:
            raise AttributeError("Pool max_size value must be an integer "
                                 "greater than 0, the given value {} "
                                 "is not valid.".format(pool_size))

        self.max_size = _CNX_POOL_MAXSIZE if pool_size == 0 else pool_size

    def _set_max_idle_time(self, max_idle_time):
        """Set the max idle time.

        This method sets the max idle time.

        Args:
            max_idle_time (int): An integer equal or greater than 0 indicating
                                 the max idle time.

        Raises:
            :class:`AttributeError`: If the max_idle_time value is not an
                                     integer greater or equal to 0.
        """
        if isinstance(max_idle_time, bool) or \
           not isinstance(max_idle_time, int) or not max_idle_time > -1:
            raise AttributeError("Connection max_idle_time value must be an "
                                 "integer greater or equal to 0, the given "
                                 "value {} is not valid.".format(max_idle_time))

        self.max_idle_time = max_idle_time
        self.settings["max_idle_time"] = _CNX_POOL_MAX_IDLE_TIME \
            if max_idle_time == 0 else int(max_idle_time / 1000)

    def _set_pool_enabled(self, enabled):
        """Set if the pool is enabled.

        This method sets if the pool is enabled.

        Args:
            enabled (bool): True if to enabling the pool.

        Raises:
            :class:`AttributeError`: If the value of enabled is not a bool type.
        """
        if not isinstance(enabled, bool):
            raise AttributeError("The enabled value should be True or False.")
        self.pooling_enabled = enabled

    def _set_queue_timeout(self, queue_timeout):
        """Set the queue timeout.

        This method sets the queue timeout.

        Args:
            queue_timeout (int): An integer equal or greater than 0 indicating
                                 the queue timeout.

        Raises:
            :class:`AttributeError`: If the queue_timeout value is not an
                                     integer greater or equal to 0.
        """
        if isinstance(queue_timeout, bool) or \
           not isinstance(queue_timeout, int) or not queue_timeout > -1:
            raise AttributeError("Connection queue_timeout value must be an "
                                 "integer greater or equal to 0, the given "
                                 "value {} is not valid.".format(queue_timeout))

        self.queue_timeout = queue_timeout
        self.settings["queue_timeout"] = _CNX_POOL_QUEUE_TIMEOUT \
            if queue_timeout == 0 else int(queue_timeout / 1000)
        # To avoid a connection stall waiting for the server, if the
        # connect-timeout is not given, use the queue_timeout
        if not "connect-timeout" in self.settings:
            self.settings["connect-timeout"] = self.queue_timeout

    def get_session(self):
        """Creates a Session instance using the provided connection data.

        Returns:
            Session: Session object.
        """
        session = Session(self.settings)
        self.sessions.append(session)
        return session

    def close(self):
        """Closes the sessions opened by this client.
        """
        PoolsManager().close_pool(self.settings)
        for session in self.sessions:
            session.close_connections()
