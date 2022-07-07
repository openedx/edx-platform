# Copyright (c) 2009, 2022, Oracle and/or its affiliates. All rights reserved.
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

"""Various MySQL constants and character sets
"""

import ssl
import warnings

from .utils import make_abc
from .errors import ProgrammingError
from .charsets import MYSQL_CHARACTER_SETS

MAX_PACKET_LENGTH = 16777215
NET_BUFFER_LENGTH = 8192
MAX_MYSQL_TABLE_COLUMNS = 4096
# Flag used to send the Query Attributes with 0 (or more) parameters.
PARAMETER_COUNT_AVAILABLE = 8

DEFAULT_CONFIGURATION = {
    'database': None,
    'user': '',
    'password': '',
    'password1': '',
    'password2': '',
    'password3': '',
    'host': '127.0.0.1',
    'port': 3306,
    'unix_socket': None,
    'use_unicode': True,
    'charset': 'utf8mb4',
    'collation': None,
    'converter_class': None,
    'converter_str_fallback': False,
    'autocommit': False,
    'time_zone': None,
    'sql_mode': None,
    'get_warnings': False,
    'raise_on_warnings': False,
    'connection_timeout': None,
    'client_flags': 0,
    'compress': False,
    'buffered': False,
    'raw': False,
    'ssl_ca': None,
    'ssl_cert': None,
    'ssl_key': None,
    'ssl_verify_cert': False,
    'ssl_verify_identity': False,
    'ssl_cipher': None,
    'tls_ciphersuites': None,
    'ssl_disabled': False,
    'tls_versions': None,
    'passwd': None,
    'db': None,
    'connect_timeout': None,
    'dsn': None,
    'force_ipv6': False,
    'auth_plugin': None,
    'allow_local_infile': False,
    'allow_local_infile_in_path': None,
    'consume_results': False,
    'conn_attrs': None,
    'dns_srv': False,
    'use_pure': False,
    'krb_service_principal': None,
    'oci_config_file': None,
    'fido_callback': None,
}

CNX_POOL_ARGS = ('pool_name', 'pool_size', 'pool_reset_session')

TLS_VERSIONS = ["TLSv1.2", "TLSv1.3"]

DEPRECATED_TLS_VERSIONS = ["TLSv1", "TLSv1.1"]


def flag_is_set(flag, flags):
    """Checks if the flag is set

    Returns boolean"""
    if (flags & flag) > 0:
        return True
    return False


def _obsolete_option(name, new_name, value):
    warnings.warn('The option "{}" has been deprecated, use "{}" instead.'
                  ''.format(name, new_name), category=DeprecationWarning)
    return value


class _Constants(object):
    """
    Base class for constants
    """
    prefix = ''
    desc = {}

    def __new__(cls):
        raise TypeError("Can not instanciate from %s" % cls.__name__)

    @classmethod
    def get_desc(cls, name):
        """Get description of given constant"""
        try:
            return cls.desc[name][1]
        except:
            return None

    @classmethod
    def get_info(cls, setid):
        """Get information about given constant"""
        for name, info in cls.desc.items():
            if info[0] == setid:
                return name
        return None

    @classmethod
    def get_full_info(cls):
        """get full information about given constant"""
        res = ()
        try:
            res = ["%s : %s" % (k, v[1]) for k, v in cls.desc.items()]
        except Exception as err:  # pylint: disable=W0703
            res = ('No information found in constant class.%s' % err)

        return res


class _Flags(_Constants):
    """Base class for classes describing flags
    """

    @classmethod
    def get_bit_info(cls, value):
        """Get the name of all bits set

        Returns a list of strings."""
        res = []
        for name, info in cls.desc.items():
            if value & info[0]:
                res.append(name)
        return res


class FieldType(_Constants):
    """MySQL Field Types
    """
    prefix = 'FIELD_TYPE_'
    DECIMAL = 0x00
    TINY = 0x01
    SHORT = 0x02
    LONG = 0x03
    FLOAT = 0x04
    DOUBLE = 0x05
    NULL = 0x06
    TIMESTAMP = 0x07
    LONGLONG = 0x08
    INT24 = 0x09
    DATE = 0x0a
    TIME = 0x0b
    DATETIME = 0x0c
    YEAR = 0x0d
    NEWDATE = 0x0e
    VARCHAR = 0x0f
    BIT = 0x10
    JSON = 0xf5
    NEWDECIMAL = 0xf6
    ENUM = 0xf7
    SET = 0xf8
    TINY_BLOB = 0xf9
    MEDIUM_BLOB = 0xfa
    LONG_BLOB = 0xfb
    BLOB = 0xfc
    VAR_STRING = 0xfd
    STRING = 0xfe
    GEOMETRY = 0xff

    desc = {
        'DECIMAL': (0x00, 'DECIMAL'),
        'TINY': (0x01, 'TINY'),
        'SHORT': (0x02, 'SHORT'),
        'LONG': (0x03, 'LONG'),
        'FLOAT': (0x04, 'FLOAT'),
        'DOUBLE': (0x05, 'DOUBLE'),
        'NULL': (0x06, 'NULL'),
        'TIMESTAMP': (0x07, 'TIMESTAMP'),
        'LONGLONG': (0x08, 'LONGLONG'),
        'INT24': (0x09, 'INT24'),
        'DATE': (0x0a, 'DATE'),
        'TIME': (0x0b, 'TIME'),
        'DATETIME': (0x0c, 'DATETIME'),
        'YEAR': (0x0d, 'YEAR'),
        'NEWDATE': (0x0e, 'NEWDATE'),
        'VARCHAR': (0x0f, 'VARCHAR'),
        'BIT': (0x10, 'BIT'),
        'JSON': (0xf5, 'JSON'),
        'NEWDECIMAL': (0xf6, 'NEWDECIMAL'),
        'ENUM': (0xf7, 'ENUM'),
        'SET': (0xf8, 'SET'),
        'TINY_BLOB': (0xf9, 'TINY_BLOB'),
        'MEDIUM_BLOB': (0xfa, 'MEDIUM_BLOB'),
        'LONG_BLOB': (0xfb, 'LONG_BLOB'),
        'BLOB': (0xfc, 'BLOB'),
        'VAR_STRING': (0xfd, 'VAR_STRING'),
        'STRING': (0xfe, 'STRING'),
        'GEOMETRY': (0xff, 'GEOMETRY'),
    }

    @classmethod
    def get_string_types(cls):
        """Get the list of all string types"""
        return [
            cls.VARCHAR,
            cls.ENUM,
            cls.VAR_STRING, cls.STRING,
        ]

    @classmethod
    def get_binary_types(cls):
        """Get the list of all binary types"""
        return [
            cls.TINY_BLOB, cls.MEDIUM_BLOB,
            cls.LONG_BLOB, cls.BLOB,
        ]

    @classmethod
    def get_number_types(cls):
        """Get the list of all number types"""
        return [
            cls.DECIMAL, cls.NEWDECIMAL,
            cls.TINY, cls.SHORT, cls.LONG,
            cls.FLOAT, cls.DOUBLE,
            cls.LONGLONG, cls.INT24,
            cls.BIT,
            cls.YEAR,
        ]

    @classmethod
    def get_timestamp_types(cls):
        """Get the list of all timestamp types"""
        return [
            cls.DATETIME, cls.TIMESTAMP,
        ]


class FieldFlag(_Flags):
    """MySQL Field Flags

    Field flags as found in MySQL sources mysql-src/include/mysql_com.h
    """
    _prefix = ''
    NOT_NULL = 1 << 0
    PRI_KEY = 1 << 1
    UNIQUE_KEY = 1 << 2
    MULTIPLE_KEY = 1 << 3
    BLOB = 1 << 4
    UNSIGNED = 1 << 5
    ZEROFILL = 1 << 6
    BINARY = 1 << 7

    ENUM = 1 << 8
    AUTO_INCREMENT = 1 << 9
    TIMESTAMP = 1 << 10
    SET = 1 << 11

    NO_DEFAULT_VALUE = 1 << 12
    ON_UPDATE_NOW = 1 << 13
    NUM = 1 << 14
    PART_KEY = 1 << 15
    GROUP = 1 << 14  # SAME AS NUM !!!!!!!????
    UNIQUE = 1 << 16
    BINCMP = 1 << 17

    GET_FIXED_FIELDS = 1 << 18
    FIELD_IN_PART_FUNC = 1 << 19
    FIELD_IN_ADD_INDEX = 1 << 20
    FIELD_IS_RENAMED = 1 << 21

    desc = {
        'NOT_NULL': (1 << 0, "Field can't be NULL"),
        'PRI_KEY': (1 << 1, "Field is part of a primary key"),
        'UNIQUE_KEY': (1 << 2, "Field is part of a unique key"),
        'MULTIPLE_KEY': (1 << 3, "Field is part of a key"),
        'BLOB': (1 << 4, "Field is a blob"),
        'UNSIGNED': (1 << 5, "Field is unsigned"),
        'ZEROFILL': (1 << 6, "Field is zerofill"),
        'BINARY': (1 << 7, "Field is binary  "),
        'ENUM': (1 << 8, "field is an enum"),
        'AUTO_INCREMENT': (1 << 9, "field is a autoincrement field"),
        'TIMESTAMP': (1 << 10, "Field is a timestamp"),
        'SET': (1 << 11, "field is a set"),
        'NO_DEFAULT_VALUE': (1 << 12, "Field doesn't have default value"),
        'ON_UPDATE_NOW': (1 << 13, "Field is set to NOW on UPDATE"),
        'NUM': (1 << 14, "Field is num (for clients)"),

        'PART_KEY': (1 << 15, "Intern; Part of some key"),
        'GROUP': (1 << 14, "Intern: Group field"),  # Same as NUM
        'UNIQUE': (1 << 16, "Intern: Used by sql_yacc"),
        'BINCMP': (1 << 17, "Intern: Used by sql_yacc"),
        'GET_FIXED_FIELDS': (1 << 18, "Used to get fields in item tree"),
        'FIELD_IN_PART_FUNC': (1 << 19, "Field part of partition func"),
        'FIELD_IN_ADD_INDEX': (1 << 20, "Intern: Field used in ADD INDEX"),
        'FIELD_IS_RENAMED': (1 << 21, "Intern: Field is being renamed"),
    }


class ServerCmd(_Constants):
    """MySQL Server Commands
    """
    _prefix = 'COM_'
    SLEEP = 0
    QUIT = 1
    INIT_DB = 2
    QUERY = 3
    FIELD_LIST = 4
    CREATE_DB = 5
    DROP_DB = 6
    REFRESH = 7
    SHUTDOWN = 8
    STATISTICS = 9
    PROCESS_INFO = 10
    CONNECT = 11
    PROCESS_KILL = 12
    DEBUG = 13
    PING = 14
    TIME = 15
    DELAYED_INSERT = 16
    CHANGE_USER = 17
    BINLOG_DUMP = 18
    TABLE_DUMP = 19
    CONNECT_OUT = 20
    REGISTER_REPLICA = 21
    STMT_PREPARE = 22
    STMT_EXECUTE = 23
    STMT_SEND_LONG_DATA = 24
    STMT_CLOSE = 25
    STMT_RESET = 26
    SET_OPTION = 27
    STMT_FETCH = 28
    DAEMON = 29
    BINLOG_DUMP_GTID = 30
    RESET_CONNECTION = 31

    desc = {
        'SLEEP': (0, 'SLEEP'),
        'QUIT': (1, 'QUIT'),
        'INIT_DB': (2, 'INIT_DB'),
        'QUERY': (3, 'QUERY'),
        'FIELD_LIST': (4, 'FIELD_LIST'),
        'CREATE_DB': (5, 'CREATE_DB'),
        'DROP_DB': (6, 'DROP_DB'),
        'REFRESH': (7, 'REFRESH'),
        'SHUTDOWN': (8, 'SHUTDOWN'),
        'STATISTICS': (9, 'STATISTICS'),
        'PROCESS_INFO': (10, 'PROCESS_INFO'),
        'CONNECT': (11, 'CONNECT'),
        'PROCESS_KILL': (12, 'PROCESS_KILL'),
        'DEBUG': (13, 'DEBUG'),
        'PING': (14, 'PING'),
        'TIME': (15, 'TIME'),
        'DELAYED_INSERT': (16, 'DELAYED_INSERT'),
        'CHANGE_USER': (17, 'CHANGE_USER'),
        'BINLOG_DUMP': (18, 'BINLOG_DUMP'),
        'TABLE_DUMP': (19, 'TABLE_DUMP'),
        'CONNECT_OUT': (20, 'CONNECT_OUT'),
        'REGISTER_REPLICA': (21, 'REGISTER_REPLICA'),
        'STMT_PREPARE': (22, 'STMT_PREPARE'),
        'STMT_EXECUTE': (23, 'STMT_EXECUTE'),
        'STMT_SEND_LONG_DATA': (24, 'STMT_SEND_LONG_DATA'),
        'STMT_CLOSE': (25, 'STMT_CLOSE'),
        'STMT_RESET': (26, 'STMT_RESET'),
        'SET_OPTION': (27, 'SET_OPTION'),
        'STMT_FETCH': (28, 'STMT_FETCH'),
        'DAEMON': (29, 'DAEMON'),
        'BINLOG_DUMP_GTID': (30, 'BINLOG_DUMP_GTID'),
        'RESET_CONNECTION': (31, 'RESET_CONNECTION'),
    }


class ClientFlag(_Flags):
    """MySQL Client Flags

    Client options as found in the MySQL sources mysql-src/include/mysql_com.h
    """
    LONG_PASSWD = 1 << 0
    FOUND_ROWS = 1 << 1
    LONG_FLAG = 1 << 2
    CONNECT_WITH_DB = 1 << 3
    NO_SCHEMA = 1 << 4
    COMPRESS = 1 << 5
    ODBC = 1 << 6
    LOCAL_FILES = 1 << 7
    IGNORE_SPACE = 1 << 8
    PROTOCOL_41 = 1 << 9
    INTERACTIVE = 1 << 10
    SSL = 1 << 11
    IGNORE_SIGPIPE = 1 << 12
    TRANSACTIONS = 1 << 13
    RESERVED = 1 << 14
    SECURE_CONNECTION = 1 << 15
    MULTI_STATEMENTS = 1 << 16
    MULTI_RESULTS = 1 << 17
    PS_MULTI_RESULTS = 1 << 18
    PLUGIN_AUTH = 1 << 19
    CONNECT_ARGS = 1 << 20
    PLUGIN_AUTH_LENENC_CLIENT_DATA = 1 << 21
    CAN_HANDLE_EXPIRED_PASSWORDS = 1 << 22
    SESION_TRACK = 1 << 23
    DEPRECATE_EOF = 1 << 24
    CLIENT_QUERY_ATTRIBUTES = 1 << 27
    SSL_VERIFY_SERVER_CERT = 1 << 30
    REMEMBER_OPTIONS = 1 << 31
    MULTI_FACTOR_AUTHENTICATION = 1 << 28

    desc = {
        'LONG_PASSWD': (1 << 0, 'New more secure passwords'),
        'FOUND_ROWS': (1 << 1, 'Found instead of affected rows'),
        'LONG_FLAG': (1 << 2, 'Get all column flags'),
        'CONNECT_WITH_DB': (1 << 3, 'One can specify db on connect'),
        'NO_SCHEMA': (1 << 4, "Don't allow database.table.column"),
        'COMPRESS': (1 << 5, 'Can use compression protocol'),
        'ODBC': (1 << 6, 'ODBC client'),
        'LOCAL_FILES': (1 << 7, 'Can use LOAD DATA LOCAL'),
        'IGNORE_SPACE': (1 << 8, "Ignore spaces before ''"),
        'PROTOCOL_41': (1 << 9, 'New 4.1 protocol'),
        'INTERACTIVE': (1 << 10, 'This is an interactive client'),
        'SSL': (1 << 11, 'Switch to SSL after handshake'),
        'IGNORE_SIGPIPE': (1 << 12, 'IGNORE sigpipes'),
        'TRANSACTIONS': (1 << 13, 'Client knows about transactions'),
        'RESERVED': (1 << 14, 'Old flag for 4.1 protocol'),
        'SECURE_CONNECTION': (1 << 15, 'New 4.1 authentication'),
        'MULTI_STATEMENTS': (1 << 16, 'Enable/disable multi-stmt support'),
        'MULTI_RESULTS': (1 << 17, 'Enable/disable multi-results'),
        'PS_MULTI_RESULTS': (1 << 18, 'Multi-results in PS-protocol'),
        'PLUGIN_AUTH': (1 << 19, 'Client supports plugin authentication'),
        'CONNECT_ARGS': (1 << 20, 'Client supports connection attributes'),
        'PLUGIN_AUTH_LENENC_CLIENT_DATA': (1 << 21,
                                           'Enable authentication response packet to be larger than 255 bytes'),
        'CAN_HANDLE_EXPIRED_PASSWORDS': (1 << 22, "Don't close the connection for a connection with expired password"),
        'SESION_TRACK': (1 << 23, 'Capable of handling server state change information'),
        'DEPRECATE_EOF': (1 << 24, 'Client no longer needs EOF packet'),
        'CLIENT_QUERY_ATTRIBUTES': (1 << 27, 'Support optional extension for query parameters'),
        'SSL_VERIFY_SERVER_CERT': (1 << 30, ''),
        'REMEMBER_OPTIONS': (1 << 31, ''),
    }

    default = [
        LONG_PASSWD,
        LONG_FLAG,
        CONNECT_WITH_DB,
        PROTOCOL_41,
        TRANSACTIONS,
        SECURE_CONNECTION,
        MULTI_STATEMENTS,
        MULTI_RESULTS,
        CONNECT_ARGS,
    ]

    @classmethod
    def get_default(cls):
        """Get the default client options set

        Returns a flag with all the default client options set"""
        flags = 0
        for option in cls.default:
            flags |= option
        return flags


class ServerFlag(_Flags):
    """MySQL Server Flags

    Server flags as found in the MySQL sources mysql-src/include/mysql_com.h
    """
    _prefix = 'SERVER_'
    STATUS_IN_TRANS = 1 << 0
    STATUS_AUTOCOMMIT = 1 << 1
    MORE_RESULTS_EXISTS = 1 << 3
    QUERY_NO_GOOD_INDEX_USED = 1 << 4
    QUERY_NO_INDEX_USED = 1 << 5
    STATUS_CURSOR_EXISTS = 1 << 6
    STATUS_LAST_ROW_SENT = 1 << 7
    STATUS_DB_DROPPED = 1 << 8
    STATUS_NO_BACKSLASH_ESCAPES = 1 << 9
    SERVER_STATUS_METADATA_CHANGED = 1 << 10
    SERVER_QUERY_WAS_SLOW = 1 << 11
    SERVER_PS_OUT_PARAMS = 1 << 12
    SERVER_STATUS_IN_TRANS_READONLY = 1 << 13
    SERVER_SESSION_STATE_CHANGED = 1 << 14

    desc = {
        'SERVER_STATUS_IN_TRANS': (1 << 0,
                                   'Transaction has started'),
        'SERVER_STATUS_AUTOCOMMIT': (1 << 1,
                                     'Server in auto_commit mode'),
        'SERVER_MORE_RESULTS_EXISTS': (1 << 3,
                                       'Multi query - '
                                       'next query exists'),
        'SERVER_QUERY_NO_GOOD_INDEX_USED': (1 << 4, ''),
        'SERVER_QUERY_NO_INDEX_USED': (1 << 5, ''),
        'SERVER_STATUS_CURSOR_EXISTS': (1 << 6,
                                        'Set when server opened a read-only '
                                        'non-scrollable cursor for a query.'),
        'SERVER_STATUS_LAST_ROW_SENT': (1 << 7,
                                        'Set when a read-only cursor is '
                                        'exhausted'),
        'SERVER_STATUS_DB_DROPPED': (1 << 8, 'A database was dropped'),
        'SERVER_STATUS_NO_BACKSLASH_ESCAPES': (1 << 9, ''),
        'SERVER_STATUS_METADATA_CHANGED': (1024,
                                           'Set if after a prepared statement '
                                           'reprepare we discovered that the '
                                           'new statement returns a different '
                                           'number of result set columns.'),
        'SERVER_QUERY_WAS_SLOW': (2048, ''),
        'SERVER_PS_OUT_PARAMS': (4096,
                                 'To mark ResultSet containing output '
                                 'parameter values.'),
        'SERVER_STATUS_IN_TRANS_READONLY': (8192,
                                            'Set if multi-statement '
                                            'transaction is a read-only '
                                            'transaction.'),
        'SERVER_SESSION_STATE_CHANGED': (1 << 14,
                                         'Session state has changed on the '
                                         'server because of the execution of '
                                         'the last statement'),
    }


class RefreshOption_meta(type):
    @property
    def SLAVE(self):
        return _obsolete_option("RefreshOption.SLAVE", "RefreshOption.REPLICA",
                                RefreshOption.REPLICA)

@make_abc(RefreshOption_meta)
class RefreshOption(_Constants):
    """MySQL Refresh command options

    Options used when sending the COM_REFRESH server command.
    """
    _prefix = 'REFRESH_'
    GRANT = 1 << 0
    LOG = 1 << 1
    TABLES = 1 << 2
    HOST = 1 << 3
    STATUS = 1 << 4
    THREADS = 1 << 5
    REPLICA = 1 << 6

    desc = {
        'GRANT': (1 << 0, 'Refresh grant tables'),
        'LOG': (1 << 1, 'Start on new log file'),
        'TABLES': (1 << 2, 'close all tables'),
        'HOST': (1 << 3, 'Flush host cache'),
        'STATUS': (1 << 4, 'Flush status variables'),
        'THREADS': (1 << 5, 'Flush thread cache'),
        'REPLICA': (1 << 6, 'Reset source info and restart replica thread'),
        'SLAVE': (1 << 6, 'Deprecated option; use REPLICA instead.'),
    }


class ShutdownType(_Constants):
    """MySQL Shutdown types

    Shutdown types used by the COM_SHUTDOWN server command.
    """
    _prefix = ''
    SHUTDOWN_DEFAULT = 0
    SHUTDOWN_WAIT_CONNECTIONS = 1
    SHUTDOWN_WAIT_TRANSACTIONS = 2
    SHUTDOWN_WAIT_UPDATES = 8
    SHUTDOWN_WAIT_ALL_BUFFERS = 16
    SHUTDOWN_WAIT_CRITICAL_BUFFERS = 17
    KILL_QUERY = 254
    KILL_CONNECTION = 255

    desc = {
        'SHUTDOWN_DEFAULT': (
            SHUTDOWN_DEFAULT,
            "defaults to SHUTDOWN_WAIT_ALL_BUFFERS"),
        'SHUTDOWN_WAIT_CONNECTIONS': (
            SHUTDOWN_WAIT_CONNECTIONS,
            "wait for existing connections to finish"),
        'SHUTDOWN_WAIT_TRANSACTIONS': (
            SHUTDOWN_WAIT_TRANSACTIONS,
            "wait for existing trans to finish"),
        'SHUTDOWN_WAIT_UPDATES': (
            SHUTDOWN_WAIT_UPDATES,
            "wait for existing updates to finish"),
        'SHUTDOWN_WAIT_ALL_BUFFERS': (
            SHUTDOWN_WAIT_ALL_BUFFERS,
            "flush InnoDB and other storage engine buffers"),
        'SHUTDOWN_WAIT_CRITICAL_BUFFERS': (
            SHUTDOWN_WAIT_CRITICAL_BUFFERS,
            "don't flush InnoDB buffers, "
            "flush other storage engines' buffers"),
        'KILL_QUERY': (
            KILL_QUERY,
            "(no description)"),
        'KILL_CONNECTION': (
            KILL_CONNECTION,
            "(no description)"),
    }


class CharacterSet(_Constants):
    """MySQL supported character sets and collations

    List of character sets with their collations supported by MySQL. This
    maps to the character set we get from the server within the handshake
    packet.

    The list is hardcode so we avoid a database query when getting the
    name of the used character set or collation.
    """
    desc = MYSQL_CHARACTER_SETS

    # Multi-byte character sets which use 5c (backslash) in characters
    slash_charsets = (1, 13, 28, 84, 87, 88)

    @classmethod
    def get_info(cls, setid):
        """Retrieves character set information as tuple using an ID

        Retrieves character set and collation information based on the
        given MySQL ID.

        Raises ProgrammingError when character set is not supported.

        Returns a tuple.
        """
        try:
            return cls.desc[setid][0:2]
        except IndexError:
            raise ProgrammingError(
                "Character set '{0}' unsupported".format(setid))

    @classmethod
    def get_desc(cls, name):
        """Retrieves character set information as string using an ID

        Retrieves character set and collation information based on the
        given MySQL ID.

        Returns a tuple.
        """
        try:
            return "%s/%s" % cls.get_info(name)
        except:
            raise

    @classmethod
    def get_default_collation(cls, charset):
        """Retrieves the default collation for given character set

        Raises ProgrammingError when character set is not supported.

        Returns list (collation, charset, index)
        """
        if isinstance(charset, int):
            try:
                info = cls.desc[charset]
                return info[1], info[0], charset
            except:
                ProgrammingError("Character set ID '%s' unsupported." % (
                    charset))

        for cid, info in enumerate(cls.desc):
            if info is None:
                continue
            if info[0] == charset and info[2] is True:
                return info[1], info[0], cid

        raise ProgrammingError("Character set '%s' unsupported." % (charset))

    @classmethod
    def get_charset_info(cls, charset=None, collation=None):
        """Get character set information using charset name and/or collation

        Retrieves character set and collation information given character
        set name and/or a collation name.
        If charset is an integer, it will look up the character set based
        on the MySQL's ID.
        For example:
            get_charset_info('utf8',None)
            get_charset_info(collation='utf8_general_ci')
            get_charset_info(47)

        Raises ProgrammingError when character set is not supported.

        Returns a tuple with (id, characterset name, collation)
        """
        if isinstance(charset, int):
            try:
                info = cls.desc[charset]
                return (charset, info[0], info[1])
            except IndexError:
                ProgrammingError("Character set ID {0} unknown.".format(
                    charset))

        if charset is not None and collation is None:
            info = cls.get_default_collation(charset)
            return (info[2], info[1], info[0])
        elif charset is None and collation is not None:
            for cid, info in enumerate(cls.desc):
                if info is None:
                    continue
                if collation == info[1]:
                    return (cid, info[0], info[1])
            raise ProgrammingError("Collation '{0}' unknown.".format(collation))
        else:
            for cid, info in enumerate(cls.desc):
                if info is None:
                    continue
                if info[0] == charset and info[1] == collation:
                    return (cid, info[0], info[1])
            _ = cls.get_default_collation(charset)
            raise ProgrammingError("Collation '{0}' unknown.".format(collation))

    @classmethod
    def get_supported(cls):
        """Retrieves a list with names of all supproted character sets

        Returns a tuple.
        """
        res = []
        for info in cls.desc:
            if info and info[0] not in res:
                res.append(info[0])
        return tuple(res)


class SQLMode(_Constants):
    """MySQL SQL Modes

    The numeric values of SQL Modes are not interesting, only the names
    are used when setting the SQL_MODE system variable using the MySQL
    SET command.

    See http://dev.mysql.com/doc/refman/5.6/en/server-sql-mode.html
    """
    _prefix = 'MODE_'
    REAL_AS_FLOAT = 'REAL_AS_FLOAT'
    PIPES_AS_CONCAT = 'PIPES_AS_CONCAT'
    ANSI_QUOTES = 'ANSI_QUOTES'
    IGNORE_SPACE = 'IGNORE_SPACE'
    NOT_USED = 'NOT_USED'
    ONLY_FULL_GROUP_BY = 'ONLY_FULL_GROUP_BY'
    NO_UNSIGNED_SUBTRACTION = 'NO_UNSIGNED_SUBTRACTION'
    NO_DIR_IN_CREATE = 'NO_DIR_IN_CREATE'
    POSTGRESQL = 'POSTGRESQL'
    ORACLE = 'ORACLE'
    MSSQL = 'MSSQL'
    DB2 = 'DB2'
    MAXDB = 'MAXDB'
    NO_KEY_OPTIONS = 'NO_KEY_OPTIONS'
    NO_TABLE_OPTIONS = 'NO_TABLE_OPTIONS'
    NO_FIELD_OPTIONS = 'NO_FIELD_OPTIONS'
    MYSQL323 = 'MYSQL323'
    MYSQL40 = 'MYSQL40'
    ANSI = 'ANSI'
    NO_AUTO_VALUE_ON_ZERO = 'NO_AUTO_VALUE_ON_ZERO'
    NO_BACKSLASH_ESCAPES = 'NO_BACKSLASH_ESCAPES'
    STRICT_TRANS_TABLES = 'STRICT_TRANS_TABLES'
    STRICT_ALL_TABLES = 'STRICT_ALL_TABLES'
    NO_ZERO_IN_DATE = 'NO_ZERO_IN_DATE'
    NO_ZERO_DATE = 'NO_ZERO_DATE'
    INVALID_DATES = 'INVALID_DATES'
    ERROR_FOR_DIVISION_BY_ZERO = 'ERROR_FOR_DIVISION_BY_ZERO'
    TRADITIONAL = 'TRADITIONAL'
    NO_AUTO_CREATE_USER = 'NO_AUTO_CREATE_USER'
    HIGH_NOT_PRECEDENCE = 'HIGH_NOT_PRECEDENCE'
    NO_ENGINE_SUBSTITUTION = 'NO_ENGINE_SUBSTITUTION'
    PAD_CHAR_TO_FULL_LENGTH = 'PAD_CHAR_TO_FULL_LENGTH'

    @classmethod
    def get_desc(cls, name):
        raise NotImplementedError

    @classmethod
    def get_info(cls, setid):
        raise NotImplementedError

    @classmethod
    def get_full_info(cls):
        """Returns a sequence of all available SQL Modes

        This class method returns a tuple containing all SQL Mode names. The
        names will be alphabetically sorted.

        Returns a tuple.
        """
        res = []
        for key in vars(cls).keys():
            if not key.startswith('_') \
                    and not hasattr(getattr(cls, key), '__call__'):
                res.append(key)
        return tuple(sorted(res))

CONN_ATTRS_DN = ["_pid", "_platform", "_source_host", "_client_name",
                 "_client_license", "_client_version", "_os", "_connector_name",
                 "_connector_license", "_connector_version"]

# TLS v1.0 cipher suites IANI to OpenSSL name translation
TLSV1_CIPHER_SUITES = {
    "TLS_RSA_WITH_NULL_MD5": "NULL-MD5",
    "TLS_RSA_WITH_NULL_SHA": "NULL-SHA",
    "TLS_RSA_WITH_RC4_128_MD5": "RC4-MD5",
    "TLS_RSA_WITH_RC4_128_SHA": "RC4-SHA",
    "TLS_RSA_WITH_IDEA_CBC_SHA": "IDEA-CBC-SHA",
    "TLS_RSA_WITH_3DES_EDE_CBC_SHA": "DES-CBC3-SHA",

    "TLS_DH_DSS_WITH_3DES_EDE_CBC_SHA": "Not implemented.",
    "TLS_DH_RSA_WITH_3DES_EDE_CBC_SHA": "Not implemented.",
    "TLS_DHE_DSS_WITH_3DES_EDE_CBC_SHA": "DHE-DSS-DES-CBC3-SHA",
    "TLS_DHE_RSA_WITH_3DES_EDE_CBC_SHA": "DHE-RSA-DES-CBC3-SHA",

    "TLS_DH_anon_WITH_RC4_128_MD5": "ADH-RC4-MD5",
    "TLS_DH_anon_WITH_3DES_EDE_CBC_SHA": "ADH-DES-CBC3-SHA",

    # AES cipher suites from RFC3268, extending TLS v1.0
    "TLS_RSA_WITH_AES_128_CBC_SHA": "AES128-SHA",
    "TLS_RSA_WITH_AES_256_CBC_SHA": "AES256-SHA",

    "TLS_DH_DSS_WITH_AES_128_CBC_SHA": "DH-DSS-AES128-SHA",
    "TLS_DH_DSS_WITH_AES_256_CBC_SHA": "DH-DSS-AES256-SHA",
    "TLS_DH_RSA_WITH_AES_128_CBC_SHA": "DH-RSA-AES128-SHA",
    "TLS_DH_RSA_WITH_AES_256_CBC_SHA": "DH-RSA-AES256-SHA",

    "TLS_DHE_DSS_WITH_AES_128_CBC_SHA": "DHE-DSS-AES128-SHA",
    "TLS_DHE_DSS_WITH_AES_256_CBC_SHA": "DHE-DSS-AES256-SHA",
    "TLS_DHE_RSA_WITH_AES_128_CBC_SHA": "DHE-RSA-AES128-SHA",
    "TLS_DHE_RSA_WITH_AES_256_CBC_SHA": "DHE-RSA-AES256-SHA",

    "TLS_DH_anon_WITH_AES_128_CBC_SHA": "ADH-AES128-SHA",
    "TLS_DH_anon_WITH_AES_256_CBC_SHA": "ADH-AES256-SHA",

    # Camellia cipher suites from RFC4132, extending TLS v1.0
    "TLS_RSA_WITH_CAMELLIA_128_CBC_SHA": "CAMELLIA128-SHA",
    "TLS_RSA_WITH_CAMELLIA_256_CBC_SHA": "CAMELLIA256-SHA",

    "TLS_DH_DSS_WITH_CAMELLIA_128_CBC_SHA": "DH-DSS-CAMELLIA128-SHA",
    "TLS_DH_DSS_WITH_CAMELLIA_256_CBC_SHA": "DH-DSS-CAMELLIA256-SHA",
    "TLS_DH_RSA_WITH_CAMELLIA_128_CBC_SHA": "DH-RSA-CAMELLIA128-SHA",
    "TLS_DH_RSA_WITH_CAMELLIA_256_CBC_SHA": "DH-RSA-CAMELLIA256-SHA",

    "TLS_DHE_DSS_WITH_CAMELLIA_128_CBC_SHA": "DHE-DSS-CAMELLIA128-SHA",
    "TLS_DHE_DSS_WITH_CAMELLIA_256_CBC_SHA": "DHE-DSS-CAMELLIA256-SHA",
    "TLS_DHE_RSA_WITH_CAMELLIA_128_CBC_SHA": "DHE-RSA-CAMELLIA128-SHA",
    "TLS_DHE_RSA_WITH_CAMELLIA_256_CBC_SHA": "DHE-RSA-CAMELLIA256-SHA",

    "TLS_DH_anon_WITH_CAMELLIA_128_CBC_SHA": "ADH-CAMELLIA128-SHA",
    "TLS_DH_anon_WITH_CAMELLIA_256_CBC_SHA": "ADH-CAMELLIA256-SHA",

    # SEED cipher suites from RFC4162, extending TLS v1.0
    "TLS_RSA_WITH_SEED_CBC_SHA": "SEED-SHA",

    "TLS_DH_DSS_WITH_SEED_CBC_SHA": "DH-DSS-SEED-SHA",
    "TLS_DH_RSA_WITH_SEED_CBC_SHA": "DH-RSA-SEED-SHA",

    "TLS_DHE_DSS_WITH_SEED_CBC_SHA": "DHE-DSS-SEED-SHA",
    "TLS_DHE_RSA_WITH_SEED_CBC_SHA": "DHE-RSA-SEED-SHA",

    "TLS_DH_anon_WITH_SEED_CBC_SHA": "ADH-SEED-SHA",

    # GOST cipher suites from draft-chudov-cryptopro-cptls, extending TLS v1.0
    "TLS_GOSTR341094_WITH_28147_CNT_IMIT": "GOST94-GOST89-GOST89",
    "TLS_GOSTR341001_WITH_28147_CNT_IMIT": "GOST2001-GOST89-GOST89",
    "TLS_GOSTR341094_WITH_NULL_GOSTR3411": "GOST94-NULL-GOST94",
    "TLS_GOSTR341001_WITH_NULL_GOSTR3411": "GOST2001-NULL-GOST94"}

# TLS v1.1 cipher suites IANI to OpenSSL name translation
TLSV1_1_CIPHER_SUITES = TLSV1_CIPHER_SUITES

# TLS v1.2 cipher suites IANI to OpenSSL name translation
TLSV1_2_CIPHER_SUITES = {
    "TLS_RSA_WITH_NULL_SHA256": "NULL-SHA256",

    "TLS_RSA_WITH_AES_128_CBC_SHA256": "AES128-SHA256",
    "TLS_RSA_WITH_AES_256_CBC_SHA256": "AES256-SHA256",
    "TLS_RSA_WITH_AES_128_GCM_SHA256": "AES128-GCM-SHA256",
    "TLS_RSA_WITH_AES_256_GCM_SHA384": "AES256-GCM-SHA384",

    "TLS_DH_RSA_WITH_AES_128_CBC_SHA256": "DH-RSA-AES128-SHA256",
    "TLS_DH_RSA_WITH_AES_256_CBC_SHA256": "DH-RSA-AES256-SHA256",
    "TLS_DH_RSA_WITH_AES_128_GCM_SHA256": "DH-RSA-AES128-GCM-SHA256",
    "TLS_DH_RSA_WITH_AES_256_GCM_SHA384": "DH-RSA-AES256-GCM-SHA384",

    "TLS_DH_DSS_WITH_AES_128_CBC_SHA256": "DH-DSS-AES128-SHA256",
    "TLS_DH_DSS_WITH_AES_256_CBC_SHA256": "DH-DSS-AES256-SHA256",
    "TLS_DH_DSS_WITH_AES_128_GCM_SHA256": "DH-DSS-AES128-GCM-SHA256",
    "TLS_DH_DSS_WITH_AES_256_GCM_SHA384": "DH-DSS-AES256-GCM-SHA384",

    "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256": "DHE-RSA-AES128-SHA256",
    "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256": "DHE-RSA-AES256-SHA256",
    "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256": "DHE-RSA-AES128-GCM-SHA256",
    "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384": "DHE-RSA-AES256-GCM-SHA384",

    "TLS_DHE_DSS_WITH_AES_128_CBC_SHA256": "DHE-DSS-AES128-SHA256",
    "TLS_DHE_DSS_WITH_AES_256_CBC_SHA256": "DHE-DSS-AES256-SHA256",
    "TLS_DHE_DSS_WITH_AES_128_GCM_SHA256": "DHE-DSS-AES128-GCM-SHA256",
    "TLS_DHE_DSS_WITH_AES_256_GCM_SHA384": "DHE-DSS-AES256-GCM-SHA384",

    "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256": "ECDHE-RSA-AES128-SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384": "ECDHE-RSA-AES256-SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256": "ECDHE-RSA-AES128-GCM-SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384": "ECDHE-RSA-AES256-GCM-SHA384",

    "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256": "ECDHE-ECDSA-AES128-SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384": "ECDHE-ECDSA-AES256-SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256": "ECDHE-ECDSA-AES128-GCM-SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384": "ECDHE-ECDSA-AES256-GCM-SHA384",

    "TLS_DH_anon_WITH_AES_128_CBC_SHA256": "ADH-AES128-SHA256",
    "TLS_DH_anon_WITH_AES_256_CBC_SHA256": "ADH-AES256-SHA256",
    "TLS_DH_anon_WITH_AES_128_GCM_SHA256": "ADH-AES128-GCM-SHA256",
    "TLS_DH_anon_WITH_AES_256_GCM_SHA384": "ADH-AES256-GCM-SHA384",

    "RSA_WITH_AES_128_CCM": "AES128-CCM",
    "RSA_WITH_AES_256_CCM": "AES256-CCM",
    "DHE_RSA_WITH_AES_128_CCM": "DHE-RSA-AES128-CCM",
    "DHE_RSA_WITH_AES_256_CCM": "DHE-RSA-AES256-CCM",
    "RSA_WITH_AES_128_CCM_8": "AES128-CCM8",
    "RSA_WITH_AES_256_CCM_8": "AES256-CCM8",
    "DHE_RSA_WITH_AES_128_CCM_8": "DHE-RSA-AES128-CCM8",
    "DHE_RSA_WITH_AES_256_CCM_8": "DHE-RSA-AES256-CCM8",
    "ECDHE_ECDSA_WITH_AES_128_CCM": "ECDHE-ECDSA-AES128-CCM",
    "ECDHE_ECDSA_WITH_AES_256_CCM": "ECDHE-ECDSA-AES256-CCM",
    "ECDHE_ECDSA_WITH_AES_128_CCM_8": "ECDHE-ECDSA-AES128-CCM8",
    "ECDHE_ECDSA_WITH_AES_256_CCM_8": "ECDHE-ECDSA-AES256-CCM8",

    # ARIA cipher suites from RFC6209, extending TLS v1.2
    "TLS_RSA_WITH_ARIA_128_GCM_SHA256": "ARIA128-GCM-SHA256",
    "TLS_RSA_WITH_ARIA_256_GCM_SHA384": "ARIA256-GCM-SHA384",
    "TLS_DHE_RSA_WITH_ARIA_128_GCM_SHA256": "DHE-RSA-ARIA128-GCM-SHA256",
    "TLS_DHE_RSA_WITH_ARIA_256_GCM_SHA384": "DHE-RSA-ARIA256-GCM-SHA384",
    "TLS_DHE_DSS_WITH_ARIA_128_GCM_SHA256": "DHE-DSS-ARIA128-GCM-SHA256",
    "TLS_DHE_DSS_WITH_ARIA_256_GCM_SHA384": "DHE-DSS-ARIA256-GCM-SHA384",
    "TLS_ECDHE_ECDSA_WITH_ARIA_128_GCM_SHA256": "ECDHE-ECDSA-ARIA128-GCM-SHA256",
    "TLS_ECDHE_ECDSA_WITH_ARIA_256_GCM_SHA384": "ECDHE-ECDSA-ARIA256-GCM-SHA384",
    "TLS_ECDHE_RSA_WITH_ARIA_128_GCM_SHA256": "ECDHE-ARIA128-GCM-SHA256",
    "TLS_ECDHE_RSA_WITH_ARIA_256_GCM_SHA384": "ECDHE-ARIA256-GCM-SHA384",
    "TLS_PSK_WITH_ARIA_128_GCM_SHA256": "PSK-ARIA128-GCM-SHA256",
    "TLS_PSK_WITH_ARIA_256_GCM_SHA384": "PSK-ARIA256-GCM-SHA384",
    "TLS_DHE_PSK_WITH_ARIA_128_GCM_SHA256": "DHE-PSK-ARIA128-GCM-SHA256",
    "TLS_DHE_PSK_WITH_ARIA_256_GCM_SHA384": "DHE-PSK-ARIA256-GCM-SHA384",
    "TLS_RSA_PSK_WITH_ARIA_128_GCM_SHA256": "RSA-PSK-ARIA128-GCM-SHA256",
    "TLS_RSA_PSK_WITH_ARIA_256_GCM_SHA384": "RSA-PSK-ARIA256-GCM-SHA384",

    # Camellia HMAC-Based cipher suites from RFC6367, extending TLS v1.2
    "TLS_ECDHE_ECDSA_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-ECDSA-CAMELLIA128-SHA256",
    "TLS_ECDHE_ECDSA_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-ECDSA-CAMELLIA256-SHA384",
    "TLS_ECDHE_RSA_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-RSA-CAMELLIA128-SHA256",
    "TLS_ECDHE_RSA_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-RSA-CAMELLIA256-SHA384",

    # Pre-shared keying (PSK) cipher suites",
    "PSK_WITH_NULL_SHA": "PSK-NULL-SHA",
    "DHE_PSK_WITH_NULL_SHA": "DHE-PSK-NULL-SHA",
    "RSA_PSK_WITH_NULL_SHA": "RSA-PSK-NULL-SHA",

    "PSK_WITH_RC4_128_SHA": "PSK-RC4-SHA",
    "PSK_WITH_3DES_EDE_CBC_SHA": "PSK-3DES-EDE-CBC-SHA",
    "PSK_WITH_AES_128_CBC_SHA": "PSK-AES128-CBC-SHA",
    "PSK_WITH_AES_256_CBC_SHA": "PSK-AES256-CBC-SHA",

    "DHE_PSK_WITH_RC4_128_SHA": "DHE-PSK-RC4-SHA",
    "DHE_PSK_WITH_3DES_EDE_CBC_SHA": "DHE-PSK-3DES-EDE-CBC-SHA",
    "DHE_PSK_WITH_AES_128_CBC_SHA": "DHE-PSK-AES128-CBC-SHA",
    "DHE_PSK_WITH_AES_256_CBC_SHA": "DHE-PSK-AES256-CBC-SHA",

    "RSA_PSK_WITH_RC4_128_SHA": "RSA-PSK-RC4-SHA",
    "RSA_PSK_WITH_3DES_EDE_CBC_SHA": "RSA-PSK-3DES-EDE-CBC-SHA",
    "RSA_PSK_WITH_AES_128_CBC_SHA": "RSA-PSK-AES128-CBC-SHA",
    "RSA_PSK_WITH_AES_256_CBC_SHA": "RSA-PSK-AES256-CBC-SHA",

    "PSK_WITH_AES_128_GCM_SHA256": "PSK-AES128-GCM-SHA256",
    "PSK_WITH_AES_256_GCM_SHA384": "PSK-AES256-GCM-SHA384",
    "DHE_PSK_WITH_AES_128_GCM_SHA256": "DHE-PSK-AES128-GCM-SHA256",
    "DHE_PSK_WITH_AES_256_GCM_SHA384": "DHE-PSK-AES256-GCM-SHA384",
    "RSA_PSK_WITH_AES_128_GCM_SHA256": "RSA-PSK-AES128-GCM-SHA256",
    "RSA_PSK_WITH_AES_256_GCM_SHA384": "RSA-PSK-AES256-GCM-SHA384",

    "PSK_WITH_AES_128_CBC_SHA256": "PSK-AES128-CBC-SHA256",
    "PSK_WITH_AES_256_CBC_SHA384": "PSK-AES256-CBC-SHA384",
    "PSK_WITH_NULL_SHA256": "PSK-NULL-SHA256",
    "PSK_WITH_NULL_SHA384": "PSK-NULL-SHA384",
    "DHE_PSK_WITH_AES_128_CBC_SHA256": "DHE-PSK-AES128-CBC-SHA256",
    "DHE_PSK_WITH_AES_256_CBC_SHA384": "DHE-PSK-AES256-CBC-SHA384",
    "DHE_PSK_WITH_NULL_SHA256": "DHE-PSK-NULL-SHA256",
    "DHE_PSK_WITH_NULL_SHA384": "DHE-PSK-NULL-SHA384",
    "RSA_PSK_WITH_AES_128_CBC_SHA256": "RSA-PSK-AES128-CBC-SHA256",
    "RSA_PSK_WITH_AES_256_CBC_SHA384": "RSA-PSK-AES256-CBC-SHA384",
    "RSA_PSK_WITH_NULL_SHA256": "RSA-PSK-NULL-SHA256",
    "RSA_PSK_WITH_NULL_SHA384": "RSA-PSK-NULL-SHA384",

    "ECDHE_PSK_WITH_RC4_128_SHA": "ECDHE-PSK-RC4-SHA",
    "ECDHE_PSK_WITH_3DES_EDE_CBC_SHA": "ECDHE-PSK-3DES-EDE-CBC-SHA",
    "ECDHE_PSK_WITH_AES_128_CBC_SHA": "ECDHE-PSK-AES128-CBC-SHA",
    "ECDHE_PSK_WITH_AES_256_CBC_SHA": "ECDHE-PSK-AES256-CBC-SHA",
    "ECDHE_PSK_WITH_AES_128_CBC_SHA256": "ECDHE-PSK-AES128-CBC-SHA256",
    "ECDHE_PSK_WITH_AES_256_CBC_SHA384": "ECDHE-PSK-AES256-CBC-SHA384",
    "ECDHE_PSK_WITH_NULL_SHA": "ECDHE-PSK-NULL-SHA",
    "ECDHE_PSK_WITH_NULL_SHA256": "ECDHE-PSK-NULL-SHA256",
    "ECDHE_PSK_WITH_NULL_SHA384": "ECDHE-PSK-NULL-SHA384",

    "PSK_WITH_CAMELLIA_128_CBC_SHA256": "PSK-CAMELLIA128-SHA256",
    "PSK_WITH_CAMELLIA_256_CBC_SHA384": "PSK-CAMELLIA256-SHA384",

    "DHE_PSK_WITH_CAMELLIA_128_CBC_SHA256": "DHE-PSK-CAMELLIA128-SHA256",
    "DHE_PSK_WITH_CAMELLIA_256_CBC_SHA384": "DHE-PSK-CAMELLIA256-SHA384",

    "RSA_PSK_WITH_CAMELLIA_128_CBC_SHA256": "RSA-PSK-CAMELLIA128-SHA256",
    "RSA_PSK_WITH_CAMELLIA_256_CBC_SHA384": "RSA-PSK-CAMELLIA256-SHA384",

    "ECDHE_PSK_WITH_CAMELLIA_128_CBC_SHA256": "ECDHE-PSK-CAMELLIA128-SHA256",
    "ECDHE_PSK_WITH_CAMELLIA_256_CBC_SHA384": "ECDHE-PSK-CAMELLIA256-SHA384",

    "PSK_WITH_AES_128_CCM": "PSK-AES128-CCM",
    "PSK_WITH_AES_256_CCM": "PSK-AES256-CCM",
    "DHE_PSK_WITH_AES_128_CCM": "DHE-PSK-AES128-CCM",
    "DHE_PSK_WITH_AES_256_CCM": "DHE-PSK-AES256-CCM",
    "PSK_WITH_AES_128_CCM_8": "PSK-AES128-CCM8",
    "PSK_WITH_AES_256_CCM_8": "PSK-AES256-CCM8",
    "DHE_PSK_WITH_AES_128_CCM_8": "DHE-PSK-AES128-CCM8",
    "DHE_PSK_WITH_AES_256_CCM_8": "DHE-PSK-AES256-CCM8",

    # ChaCha20-Poly1305 cipher suites, extending TLS v1.2
    "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-RSA-CHACHA20-POLY1305",
    "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-ECDSA-CHACHA20-POLY1305",
    "TLS_DHE_RSA_WITH_CHACHA20_POLY1305_SHA256": "DHE-RSA-CHACHA20-POLY1305",
    "TLS_PSK_WITH_CHACHA20_POLY1305_SHA256": "PSK-CHACHA20-POLY1305",
    "TLS_ECDHE_PSK_WITH_CHACHA20_POLY1305_SHA256": "ECDHE-PSK-CHACHA20-POLY1305",
    "TLS_DHE_PSK_WITH_CHACHA20_POLY1305_SHA256": "DHE-PSK-CHACHA20-POLY1305",
    "TLS_RSA_PSK_WITH_CHACHA20_POLY1305_SHA256": "RSA-PSK-CHACHA20-POLY1305"}

# TLS v1.3 cipher suites IANI to OpenSSL name translation
TLSV1_3_CIPHER_SUITES = {
    "TLS_AES_128_GCM_SHA256": "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384": "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256": "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_128_CCM_SHA256": "TLS_AES_128_CCM_SHA256",
    "TLS_AES_128_CCM_8_SHA256": "TLS_AES_128_CCM_8_SHA256"}

TLS_CIPHER_SUITES = {
    "TLSv1": TLSV1_CIPHER_SUITES,
    "TLSv1.1": TLSV1_1_CIPHER_SUITES,
    "TLSv1.2": TLSV1_2_CIPHER_SUITES,
    "TLSv1.3": TLSV1_3_CIPHER_SUITES}

OPENSSL_CS_NAMES = {
    "TLSv1": TLSV1_CIPHER_SUITES.values(),
    "TLSv1.1": TLSV1_1_CIPHER_SUITES.values(),
    "TLSv1.2": TLSV1_2_CIPHER_SUITES.values(),
    "TLSv1.3": TLSV1_3_CIPHER_SUITES.values()}
