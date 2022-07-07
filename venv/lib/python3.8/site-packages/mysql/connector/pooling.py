# Copyright (c) 2013, 2021, Oracle and/or its affiliates. All rights reserved.
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

"""Implementing pooling of connections to MySQL servers.
"""

import re
from uuid import uuid4
# pylint: disable=F0401
try:
    import queue
except ImportError:
    # Python v2
    import Queue as queue
# pylint: enable=F0401
import threading

try:
    from mysql.connector.connection_cext import (CMySQLConnection)
except ImportError:
    CMySQLConnection = None

from . import errors
from . import Connect
from .connection import MySQLConnection

CONNECTION_POOL_LOCK = threading.RLock()
CNX_POOL_MAXSIZE = 32
CNX_POOL_MAXNAMESIZE = 64
CNX_POOL_NAMEREGEX = re.compile(r'[^a-zA-Z0-9._:\-*$#]')
MYSQL_CNX_CLASS = ((MySQLConnection) if CMySQLConnection is None else
                   (MySQLConnection, CMySQLConnection))


def generate_pool_name(**kwargs):
    """Generate a pool name

    This function takes keyword arguments, usually the connection
    arguments for MySQLConnection, and tries to generate a name for
    a pool.

    Raises PoolError when no name can be generated.

    Returns a string.
    """
    parts = []
    for key in ('host', 'port', 'user', 'database'):
        try:
            parts.append(str(kwargs[key]))
        except KeyError:
            pass

    if not parts:
        raise errors.PoolError(
            "Failed generating pool name; specify pool_name")

    return '_'.join(parts)


class PooledMySQLConnection(object):
    """Class holding a MySQL Connection in a pool

    PooledMySQLConnection is used by MySQLConnectionPool to return an
    instance holding a MySQL connection. It works like a MySQLConnection
    except for methods like close() and config().

    The close()-method will add the connection back to the pool rather
    than disconnecting from the MySQL server.

    Configuring the connection have to be done through the MySQLConnectionPool
    method set_config(). Using config() on pooled connection will raise a
    PoolError.
    """
    def __init__(self, pool, cnx):
        """Initialize

        The pool argument must be an instance of MySQLConnectionPoll. cnx
        if an instance of MySQLConnection.
        """
        if not isinstance(pool, MySQLConnectionPool):
            raise AttributeError(
                "pool should be a MySQLConnectionPool")
        if not isinstance(cnx, MYSQL_CNX_CLASS):
            raise AttributeError(
                "cnx should be a MySQLConnection")
        self._cnx_pool = pool
        self._cnx = cnx

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __getattr__(self, attr):
        """Calls attributes of the MySQLConnection instance"""
        return getattr(self._cnx, attr)

    def close(self):
        """Do not close, but add connection back to pool

        The close() method does not close the connection with the
        MySQL server. The connection is added back to the pool so it
        can be reused.

        When the pool is configured to reset the session, the session
        state will be cleared by re-authenticating the user.
        """
        try:
            cnx = self._cnx
            if self._cnx_pool.reset_session:
                cnx.reset_session()
        finally:
            self._cnx_pool.add_connection(cnx)
            self._cnx = None

    def config(self, **kwargs):
        """Configuration is done through the pool"""
        raise errors.PoolError(
            "Configuration for pooled connections should "
            "be done through the pool itself."
        )

    @property
    def pool_name(self):
        """Return the name of the connection pool"""
        return self._cnx_pool.pool_name


class MySQLConnectionPool(object):
    """Class defining a pool of MySQL connections"""
    def __init__(self, pool_size=5, pool_name=None, pool_reset_session=True,
                 **kwargs):
        """Initialize

        Initialize a MySQL connection pool with a maximum number of
        connections set to pool_size. The rest of the keywords
        arguments, kwargs, are configuration arguments for MySQLConnection
        instances.
        """
        self._pool_size = None
        self._pool_name = None
        self._reset_session = pool_reset_session
        self._set_pool_size(pool_size)
        self._set_pool_name(pool_name or generate_pool_name(**kwargs))
        self._cnx_config = {}
        self._cnx_queue = queue.Queue(self._pool_size)
        self._config_version = uuid4()

        if kwargs:
            self.set_config(**kwargs)
            cnt = 0
            while cnt < self._pool_size:
                self.add_connection()
                cnt += 1

    @property
    def pool_name(self):
        """Return the name of the connection pool"""
        return self._pool_name

    @property
    def pool_size(self):
        """Return number of connections managed by the pool"""
        return self._pool_size

    @property
    def reset_session(self):
        """Return whether to reset session"""
        return self._reset_session

    def set_config(self, **kwargs):
        """Set the connection configuration for MySQLConnection instances

        This method sets the configuration used for creating MySQLConnection
        instances. See MySQLConnection for valid connection arguments.

        Raises PoolError when a connection argument is not valid, missing
        or not supported by MySQLConnection.
        """
        if not kwargs:
            return

        with CONNECTION_POOL_LOCK:
            try:
                test_cnx = Connect()
                test_cnx.config(**kwargs)
                self._cnx_config = kwargs
                self._config_version = uuid4()
            except AttributeError as err:
                raise errors.PoolError(
                    "Connection configuration not valid: {0}".format(err))

    def _set_pool_size(self, pool_size):
        """Set the size of the pool

        This method sets the size of the pool but it will not resize the pool.

        Raises an AttributeError when the pool_size is not valid. Invalid size
        is 0, negative or higher than pooling.CNX_POOL_MAXSIZE.
        """
        if pool_size <= 0 or pool_size > CNX_POOL_MAXSIZE:
            raise AttributeError(
                "Pool size should be higher than 0 and "
                "lower or equal to {0}".format(CNX_POOL_MAXSIZE))
        self._pool_size = pool_size

    def _set_pool_name(self, pool_name):
        r"""Set the name of the pool

        This method checks the validity and sets the name of the pool.

        Raises an AttributeError when pool_name contains illegal characters
        ([^a-zA-Z0-9._\-*$#]) or is longer than pooling.CNX_POOL_MAXNAMESIZE.
        """
        if CNX_POOL_NAMEREGEX.search(pool_name):
            raise AttributeError(
                "Pool name '{0}' contains illegal characters".format(pool_name))
        if len(pool_name) > CNX_POOL_MAXNAMESIZE:
            raise AttributeError(
                "Pool name '{0}' is too long".format(pool_name))
        self._pool_name = pool_name

    def _queue_connection(self, cnx):
        """Put connection back in the queue

        This method is putting a connection back in the queue. It will not
        acquire a lock as the methods using _queue_connection() will have it
        set.

        Raises PoolError on errors.
        """
        if not isinstance(cnx, MYSQL_CNX_CLASS):
            raise errors.PoolError(
                "Connection instance not subclass of MySQLConnection.")

        try:
            self._cnx_queue.put(cnx, block=False)
        except queue.Full:
            raise errors.PoolError("Failed adding connection; queue is full")

    def add_connection(self, cnx=None):
        """Add a connection to the pool

        This method instantiates a MySQLConnection using the configuration
        passed when initializing the MySQLConnectionPool instance or using
        the set_config() method.
        If cnx is a MySQLConnection instance, it will be added to the
        queue.

        Raises PoolError when no configuration is set, when no more
        connection can be added (maximum reached) or when the connection
        can not be instantiated.
        """
        with CONNECTION_POOL_LOCK:
            if not self._cnx_config:
                raise errors.PoolError(
                    "Connection configuration not available")

            if self._cnx_queue.full():
                raise errors.PoolError(
                    "Failed adding connection; queue is full")

            if not cnx:
                cnx = Connect(**self._cnx_config)
                try:
                    if (self._reset_session and self._cnx_config['compress']
                            and cnx.get_server_version() < (5, 7, 3)):
                        raise errors.NotSupportedError("Pool reset session is "
                                                       "not supported with "
                                                       "compression for MySQL "
                                                       "server version 5.7.2 "
                                                       "or earlier.")
                except KeyError:
                    pass

                # pylint: disable=W0201,W0212
                cnx._pool_config_version = self._config_version
                # pylint: enable=W0201,W0212
            else:
                if not isinstance(cnx, MYSQL_CNX_CLASS):
                    raise errors.PoolError(
                        "Connection instance not subclass of MySQLConnection.")

            self._queue_connection(cnx)

    def get_connection(self):
        """Get a connection from the pool

        This method returns an PooledMySQLConnection instance which
        has a reference to the pool that created it, and the next available
        MySQL connection.

        When the MySQL connection is not connect, a reconnect is attempted.

        Raises PoolError on errors.

        Returns a PooledMySQLConnection instance.
        """
        with CONNECTION_POOL_LOCK:
            try:
                cnx = self._cnx_queue.get(block=False)
            except queue.Empty:
                raise errors.PoolError(
                    "Failed getting connection; pool exhausted")

            # pylint: disable=W0201,W0212
            if not cnx.is_connected() \
                    or self._config_version != cnx._pool_config_version:
                cnx.config(**self._cnx_config)
                try:
                    cnx.reconnect()
                except errors.InterfaceError:
                    # Failed to reconnect, give connection back to pool
                    self._queue_connection(cnx)
                    raise
                cnx._pool_config_version = self._config_version
            # pylint: enable=W0201,W0212

            return PooledMySQLConnection(self, cnx)

    def _remove_connections(self):
        """Close all connections

        This method closes all connections. It returns the number
        of connections it closed.

        Used mostly for tests.

        Returns int.
        """
        with CONNECTION_POOL_LOCK:
            cnt = 0
            cnxq = self._cnx_queue
            while cnxq.qsize():
                try:
                    cnx = cnxq.get(block=False)
                    cnx.disconnect()
                    cnt += 1
                except queue.Empty:
                    return cnt
                except errors.PoolError:
                    raise
                except errors.Error:
                    # Any other error when closing means connection is closed
                    pass

            return cnt
