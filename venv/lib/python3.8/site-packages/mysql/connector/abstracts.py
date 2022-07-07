# Copyright (c) 2014, 2022, Oracle and/or its affiliates.
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

"""Module gathering all abstract base classes"""

from abc import ABCMeta, abstractmethod, abstractproperty
from decimal import Decimal
from time import sleep
from datetime import date, datetime, time, timedelta
from inspect import signature
import importlib
import os
import re
import weakref
TLS_V1_3_SUPPORTED = False
try:
    import ssl
    if hasattr(ssl, "HAS_TLSv1_3") and ssl.HAS_TLSv1_3: 
        TLS_V1_3_SUPPORTED = True
except:
    # If import fails, we don't have SSL support.
    pass

from .conversion import MySQLConverterBase
from .constants import (ClientFlag, CharacterSet, CONN_ATTRS_DN,
                        DEFAULT_CONFIGURATION, DEPRECATED_TLS_VERSIONS,
                        OPENSSL_CS_NAMES, TLS_CIPHER_SUITES, TLS_VERSIONS)
from .optionfiles import MySQLOptionsParser
from .utils import make_abc
from . import errors

NAMED_TUPLE_CACHE = weakref.WeakValueDictionary()

DUPLICATED_IN_LIST_ERROR = (
    "The '{list}' list must not contain repeated values, the value "
    "'{value}' is duplicated.")

TLS_VERSION_ERROR = ("The given tls_version: '{}' is not recognized as a valid "
                     "TLS protocol version (should be one of {}).")

TLS_VERSION_DEPRECATED_ERROR = ("The given tls_version: '{}' are no longer "
                                "allowed (should be one of {}).")

TLS_VER_NO_SUPPORTED = ("No supported TLS protocol version found in the "
                        "'tls-versions' list '{}'. ")

KRB_SERVICE_PINCIPAL_ERROR = (
    'Option "krb_service_principal" {error}, must be a string in the form '
    '"primary/instance@realm" e.g "ldap/ldapauth@MYSQL.COM" where "@realm" '
    'is optional and if it is not given will be assumed to belong to the '
    'default realm, as configured in the krb5.conf file.')

MYSQL_PY_TYPES = (
    (int, str, bytes, Decimal, float, datetime, date, timedelta, time,))


@make_abc(ABCMeta)
class MySQLConnectionAbstract(object):

    """Abstract class for classes connecting to a MySQL server"""

    def __init__(self, **kwargs):
        """Initialize"""
        self._client_flags = ClientFlag.get_default()
        self._charset_id = 45
        self._sql_mode = None
        self._time_zone = None
        self._autocommit = False
        self._server_version = None
        self._handshake = None
        self._conn_attrs = {}

        self._user = ''
        self._password = ''
        self._password1 = ''
        self._password2 = ''
        self._password3 = ''
        self._database = ''
        self._host = '127.0.0.1'
        self._port = 3306
        self._unix_socket = None
        self._client_host = ''
        self._client_port = 0
        self._ssl = {}
        self._ssl_disabled = DEFAULT_CONFIGURATION["ssl_disabled"]
        self._force_ipv6 = False
        self._oci_config_file = None
        self._fido_callback = None

        self._use_unicode = True
        self._get_warnings = False
        self._raise_on_warnings = False
        self._connection_timeout = DEFAULT_CONFIGURATION["connect_timeout"]
        self._buffered = False
        self._unread_result = False
        self._have_next_result = False
        self._raw = False
        self._in_transaction = False
        self._allow_local_infile = DEFAULT_CONFIGURATION["allow_local_infile"]
        self._allow_local_infile_in_path = (
            DEFAULT_CONFIGURATION["allow_local_infile_in_path"])

        self._prepared_statements = None
        self._query_attrs = []

        self._ssl_active = False
        self._auth_plugin = None
        self._pool_config_version = None
        self.converter = None
        self._converter_class = None
        self._converter_str_fallback = False
        self._compress = False

        self._consume_results = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _get_self(self):
        """Return self for weakref.proxy

        This method is used when the original object is needed when using
        weakref.proxy.
        """
        return self

    def _read_option_files(self, config):
        """
        Read option files for connection parameters.

        Checks if connection arguments contain option file arguments, and then
        reads option files accordingly.
        """
        if 'option_files' in config:
            try:
                if isinstance(config['option_groups'], str):
                    config['option_groups'] = [config['option_groups']]
                groups = config['option_groups']
                del config['option_groups']
            except KeyError:
                groups = ['client', 'connector_python']

            if isinstance(config['option_files'], str):
                config['option_files'] = [config['option_files']]
            option_parser = MySQLOptionsParser(list(config['option_files']),
                                               keep_dashes=False)
            del config['option_files']

            config_from_file = option_parser.get_groups_as_dict_with_priority(
                *groups)
            config_options = {}
            for group in groups:
                try:
                    for option, value in config_from_file[group].items():
                        try:
                            if option == 'socket':
                                option = 'unix_socket'
                            # pylint: disable=W0104
                            DEFAULT_CONFIGURATION[option]
                            # pylint: enable=W0104

                            if (option not in config_options or
                                    config_options[option][1] <= value[1]):
                                config_options[option] = value
                        except KeyError:
                            if group == 'connector_python':
                                raise AttributeError("Unsupported argument "
                                                     "'{0}'".format(option))
                except KeyError:
                    continue

            for option, value in config_options.items():
                if option not in config:
                    try:
                        config[option] = eval(value[0])  # pylint: disable=W0123
                    except (NameError, SyntaxError):
                        config[option] = value[0]
        return config

    def _validate_tls_ciphersuites(self):
        """Validates the tls_ciphersuites option.
        """
        tls_ciphersuites = []
        tls_cs = self._ssl["tls_ciphersuites"]

        if isinstance(tls_cs, str):
            if not (tls_cs.startswith("[") and
                    tls_cs.endswith("]")):
                raise AttributeError("tls_ciphersuites must be a list, "
                                     "found: '{}'".format(tls_cs))
            else:
                tls_css = tls_cs[1:-1].split(",")
                if not tls_css:
                    raise AttributeError("No valid cipher suite found "
                                         "in 'tls_ciphersuites' list.")
                for _tls_cs in tls_css:
                    _tls_cs = tls_cs.strip().upper()
                    if _tls_cs:
                        tls_ciphersuites.append(_tls_cs)

        elif isinstance(tls_cs, list):
            tls_ciphersuites = [tls_cs for tls_cs in tls_cs if tls_cs]

        elif isinstance(tls_cs, set):
            for tls_cs in tls_ciphersuites:
                if tls_cs:
                    tls_ciphersuites.append(tls_cs)
        else:
            raise AttributeError(
                "tls_ciphersuites should be a list with one or more "
                "ciphersuites. Found: '{}'".format(tls_cs))

        tls_versions = TLS_VERSIONS[:] if self._ssl.get("tls_versions", None) \
           is None else self._ssl["tls_versions"][:]

        # A newer TLS version can use a cipher introduced on
        # an older version.
        tls_versions.sort(reverse=True)
        newer_tls_ver = tls_versions[0]
        # translated_names[0] belongs to TLSv1, TLSv1.1 and TLSv1.2
        # translated_names[1] are TLSv1.3 only
        translated_names = [[],[]]
        iani_cipher_suites_names = {}
        ossl_cipher_suites_names = []

        # Old ciphers can work with new TLS versions.
        # Find all the ciphers introduced on previous TLS versions.
        for tls_ver in TLS_VERSIONS[:TLS_VERSIONS.index(newer_tls_ver) + 1]:
            iani_cipher_suites_names.update(TLS_CIPHER_SUITES[tls_ver])
            ossl_cipher_suites_names.extend(OPENSSL_CS_NAMES[tls_ver])

        for name in tls_ciphersuites:
            if "-" in name and name in ossl_cipher_suites_names:
                if name in OPENSSL_CS_NAMES["TLSv1.3"]:
                    translated_names[1].append(name)
                else:
                    translated_names[0].append(name)
            elif name in iani_cipher_suites_names:
                translated_name = iani_cipher_suites_names[name]
                if translated_name in translated_names:
                    raise AttributeError(
                        DUPLICATED_IN_LIST_ERROR.format(
                            list="tls_ciphersuites", value=translated_name))
                else:
                    if name in TLS_CIPHER_SUITES["TLSv1.3"]:
                        translated_names[1].append(
                            iani_cipher_suites_names[name])
                    else:
                        translated_names[0].append(
                            iani_cipher_suites_names[name])
            else:
                raise AttributeError(
                    "The value '{}' in tls_ciphersuites is not a valid "
                    "cipher suite".format(name))
        if not translated_names[0] and not translated_names[1]:
            raise AttributeError("No valid cipher suite found in the "
                                 "'tls_ciphersuites' list.")
        translated_names = [":".join(translated_names[0]),
                            ":".join(translated_names[1])]
        self._ssl["tls_ciphersuites"] = translated_names

    def _validate_tls_versions(self):
        """Validates the tls_versions option.
        """
        tls_versions = []
        tls_version = self._ssl["tls_versions"]

        if isinstance(tls_version, str):
            if not (tls_version.startswith("[") and tls_version.endswith("]")):
                raise AttributeError("tls_versions must be a list, found: '{}'"
                                     "".format(tls_version))
            else:
                tls_vers = tls_version[1:-1].split(",")
                for tls_ver in tls_vers:
                    tls_version = tls_ver.strip()
                    if tls_version == "":
                        continue
                    elif tls_version in tls_versions:
                        raise AttributeError(
                            DUPLICATED_IN_LIST_ERROR.format(
                                list="tls_versions", value=tls_version))
                    tls_versions.append(tls_version)
                if tls_vers == ["TLSv1.3"] and not TLS_V1_3_SUPPORTED:
                        raise AttributeError(
                            TLS_VER_NO_SUPPORTED.format(tls_version, TLS_VERSIONS))
        elif isinstance(tls_version, list):
            if not tls_version:
                raise AttributeError(
                    "At least one TLS protocol version must be specified in "
                    "'tls_versions' list.")
            for tls_ver in tls_version:
                if tls_ver in tls_versions:
                    raise AttributeError(
                        DUPLICATED_IN_LIST_ERROR.format(
                            list="tls_versions", value=tls_ver))
                else:
                    tls_versions.append(tls_ver)
        elif isinstance(tls_version, set):
            for tls_ver in tls_version:
                tls_versions.append(tls_ver)
        else:
            raise AttributeError(
                "tls_versions should be a list with one or more of versions in "
                "{}. found: '{}'".format(", ".join(TLS_VERSIONS), tls_versions))

        if not tls_versions:
            raise AttributeError(
                "At least one TLS protocol version must be specified "
                "in 'tls_versions' list when this option is given.")

        use_tls_versions = []
        deprecated_tls_versions = []
        invalid_tls_versions = []
        for tls_ver in tls_versions:
            if tls_ver in TLS_VERSIONS:
                use_tls_versions.append(tls_ver)
            if tls_ver in DEPRECATED_TLS_VERSIONS:
                deprecated_tls_versions.append(tls_ver)
            else:
                invalid_tls_versions.append(tls_ver)

        if use_tls_versions:
            if use_tls_versions == ["TLSv1.3"] and not TLS_V1_3_SUPPORTED:
                raise errors.NotSupportedError(
                    TLS_VER_NO_SUPPORTED.format(tls_version, TLS_VERSIONS))
            use_tls_versions.sort()
            self._ssl["tls_versions"] = use_tls_versions
        elif deprecated_tls_versions:
            raise errors.NotSupportedError(
                TLS_VERSION_DEPRECATED_ERROR.format(deprecated_tls_versions,
                                                    TLS_VERSIONS))
        elif invalid_tls_versions:
            raise AttributeError(
                TLS_VERSION_ERROR.format(tls_ver, TLS_VERSIONS))

    @property
    def user(self):
        """User used while connecting to MySQL"""
        return self._user

    @property
    def server_host(self):
        """MySQL server IP address or name"""
        return self._host

    @property
    def server_port(self):
        "MySQL server TCP/IP port"
        return self._port

    @property
    def unix_socket(self):
        "MySQL Unix socket file location"
        return self._unix_socket

    @abstractproperty
    def database(self):
        """Get the current database"""
        pass

    @database.setter
    def database(self, value):
        """Set the current database"""
        self.cmd_query("USE %s" % value)

    @property
    def can_consume_results(self):
        """Returns whether to consume results"""
        return self._consume_results

    def config(self, **kwargs):
        """Configure the MySQL Connection

        This method allows you to configure the MySQLConnection instance.

        Raises on errors.
        """
        config = kwargs.copy()
        if 'dsn' in config:
            raise errors.NotSupportedError("Data source name is not supported")

        # Read option files
        self._read_option_files(config)

        # Configure how we handle MySQL warnings
        try:
            self.get_warnings = config['get_warnings']
            del config['get_warnings']
        except KeyError:
            pass  # Leave what was set or default
        try:
            self.raise_on_warnings = config['raise_on_warnings']
            del config['raise_on_warnings']
        except KeyError:
            pass  # Leave what was set or default

        # Configure client flags
        try:
            default = ClientFlag.get_default()
            self.set_client_flags(config['client_flags'] or default)
            del config['client_flags']
        except KeyError:
            pass  # Missing client_flags-argument is OK

        try:
            if config['compress']:
                self._compress = True
                self.set_client_flags([ClientFlag.COMPRESS])
        except KeyError:
            pass  # Missing compress argument is OK

        self._allow_local_infile = config.get(
            'allow_local_infile', DEFAULT_CONFIGURATION['allow_local_infile'])
        self._allow_local_infile_in_path = config.get(
            'allow_local_infile_in_path',
            DEFAULT_CONFIGURATION['allow_local_infile_in_path'])
        infile_in_path = None
        if self._allow_local_infile_in_path:
            infile_in_path = os.path.abspath(self._allow_local_infile_in_path)
            if infile_in_path and os.path.exists(infile_in_path) and \
               not os.path.isdir(infile_in_path) or \
               os.path.islink(infile_in_path):
                raise AttributeError("allow_local_infile_in_path must be a "
                                     "directory")
        if self._allow_local_infile or self._allow_local_infile_in_path:
            self.set_client_flags([ClientFlag.LOCAL_FILES])
        else:
            self.set_client_flags([-ClientFlag.LOCAL_FILES])

        try:
            if not config['consume_results']:
                self._consume_results = False
            else:
                self._consume_results = True
        except KeyError:
            self._consume_results = False

        # Configure auth_plugin
        try:
            self._auth_plugin = config['auth_plugin']
            del config['auth_plugin']
        except KeyError:
            self._auth_plugin = ''

        # Configure character set and collation
        if 'charset' in config or 'collation' in config:
            try:
                charset = config['charset']
                del config['charset']
            except KeyError:
                charset = None
            try:
                collation = config['collation']
                del config['collation']
            except KeyError:
                collation = None
            self._charset_id = CharacterSet.get_charset_info(charset,
                                                             collation)[0]

        # Set converter class
        try:
            self.set_converter_class(config['converter_class'])
        except KeyError:
            pass  # Using default converter class
        except TypeError:
            raise AttributeError("Converter class should be a subclass "
                                 "of conversion.MySQLConverterBase.")

        # Compatible configuration with other drivers
        compat_map = [
            # (<other driver argument>,<translates to>)
            ('db', 'database'),
            ('username', 'user'),
            ('passwd', 'password'),
            ('connect_timeout', 'connection_timeout'),
            ('read_default_file', 'option_files'),
        ]
        for compat, translate in compat_map:
            try:
                if translate not in config:
                    config[translate] = config[compat]
                del config[compat]
            except KeyError:
                pass  # Missing compat argument is OK

        # Configure login information
        if 'user' in config or 'password' in config:
            try:
                user = config['user']
                del config['user']
            except KeyError:
                user = self._user
            try:
                password = config['password']
                del config['password']
            except KeyError:
                password = self._password
            self.set_login(user, password)

        # Configure host information
        if 'host' in config and config['host']:
            self._host = config['host']

        # Check network locations
        try:
            self._port = int(config['port'])
            del config['port']
        except KeyError:
            pass  # Missing port argument is OK
        except ValueError:
            raise errors.InterfaceError(
                "TCP/IP port number should be an integer")

        if "ssl_disabled" in config:
            self._ssl_disabled = config.pop("ssl_disabled")

        if self._ssl_disabled and self._auth_plugin == "mysql_clear_password":
            raise errors.InterfaceError("Clear password authentication is not "
                                        "supported over insecure channels")

        # Other configuration
        set_ssl_flag = False
        for key, value in config.items():
            try:
                DEFAULT_CONFIGURATION[key]
            except KeyError:
                raise AttributeError("Unsupported argument '{0}'".format(key))
            # SSL Configuration
            if key.startswith('ssl_'):
                set_ssl_flag = True
                self._ssl.update({key.replace('ssl_', ''): value})
            elif key.startswith('tls_'):
                set_ssl_flag = True
                self._ssl.update({key: value})
            else:
                attribute = '_' + key
                try:
                    setattr(self, attribute, value.strip())
                except AttributeError:
                    setattr(self, attribute, value)

        if set_ssl_flag:
            if 'verify_cert' not in self._ssl:
                self._ssl['verify_cert'] = \
                    DEFAULT_CONFIGURATION['ssl_verify_cert']
            if 'verify_identity' not in self._ssl:
                self._ssl['verify_identity'] = \
                    DEFAULT_CONFIGURATION['ssl_verify_identity']
            # Make sure both ssl_key/ssl_cert are set, or neither (XOR)
            if 'ca' not in self._ssl or self._ssl['ca'] is None:
                self._ssl['ca'] = ""
            if bool('key' in self._ssl) != bool('cert' in self._ssl):
                raise AttributeError(
                    "ssl_key and ssl_cert need to be both "
                    "specified, or neither."
                )
            # Make sure key/cert are set to None
            elif not set(('key', 'cert')) <= set(self._ssl):
                self._ssl['key'] = None
                self._ssl['cert'] = None
            elif (self._ssl['key'] is None) != (self._ssl['cert'] is None):
                raise AttributeError(
                    "ssl_key and ssl_cert need to be both "
                    "set, or neither."
                )
            if "tls_versions" in self._ssl and \
               self._ssl["tls_versions"] is not None:
                self._validate_tls_versions()

            if "tls_ciphersuites" in self._ssl and self._ssl["tls_ciphersuites"] is not None:
                self._validate_tls_ciphersuites()

        if self._conn_attrs is None:
            self._conn_attrs = {}
        elif not isinstance(self._conn_attrs, dict):
            raise errors.InterfaceError('conn_attrs must be of type dict.')
        else:
            for attr_name in self._conn_attrs:
                if attr_name in CONN_ATTRS_DN:
                    continue
                # Validate name type
                if not isinstance(attr_name, str):
                    raise errors.InterfaceError(
                        "Attribute name should be a string, found: '{}' in '{}'"
                        "".format(attr_name, self._conn_attrs))
                # Validate attribute name limit 32 characters
                if len(attr_name) > 32:
                    raise errors.InterfaceError(
                        "Attribute name '{}' exceeds 32 characters limit size."
                        "".format(attr_name))
                # Validate names in connection attributes cannot start with "_"
                if attr_name.startswith("_"):
                    raise errors.InterfaceError(
                        "Key names in connection attributes cannot start with "
                        "'_', found: '{}'".format(attr_name))
                # Validate value type
                attr_value = self._conn_attrs[attr_name]
                if not isinstance(attr_value, str):
                    raise errors.InterfaceError(
                        "Attribute '{}' value: '{}' must be a string type."
                        "".format(attr_name, attr_value))
                # Validate attribute value limit 1024 characters
                if len(attr_value) > 1024:
                    raise errors.InterfaceError(
                        "Attribute '{}' value: '{}' exceeds 1024 characters "
                        "limit size".format(attr_name, attr_value))

        if self._client_flags & ClientFlag.CONNECT_ARGS:
            self._add_default_conn_attrs()
        if "krb_service_principal" in config and \
            config["krb_service_principal"] is not None:
            self._krb_service_principal = config["krb_service_principal"]
            if not isinstance(self._krb_service_principal, str):
                raise errors.InterfaceError(KRB_SERVICE_PINCIPAL_ERROR.format(
                    error="is not a string"))
            if self._krb_service_principal == "":
                raise errors.InterfaceError(KRB_SERVICE_PINCIPAL_ERROR.format(
                    error="can not be an empty string"))
            if "/" not in self._krb_service_principal:
                raise errors.InterfaceError(KRB_SERVICE_PINCIPAL_ERROR.format(
                    error="is incorrectly formatted"))

        if self._fido_callback:
            # Import the callable if it's a str
            if isinstance(self._fido_callback, str):
                try:
                    module, callback = self._fido_callback.rsplit(".", 1)
                except ValueError:
                    raise errors.ProgrammingError(
                        f"No callable named '{self._fido_callback}'"
                    )
                try:
                    module = importlib.import_module(module)
                    self._fido_callback = getattr(module, callback)
                except (AttributeError, ModuleNotFoundError) as err:
                    raise errors.ProgrammingError(f"{err}")
            # Check if it's a callable
            if not callable(self._fido_callback):
                raise errors.ProgrammingError(
                    "Expected a callable for 'fido_callback'"
                )
            # Check the callable signature if has only 1 positional argument
            params = len(signature(self._fido_callback).parameters)
            if params != 1:
                raise errors.ProgrammingError(
                    "'fido_callback' requires 1 positional argument, but the "
                    f"callback provided has {params}"
                )

    def _add_default_conn_attrs(self):
        """Add the default connection attributes."""
        pass

    def _check_server_version(self, server_version):
        """Check the MySQL version

        This method will check the MySQL version and raise an InterfaceError
        when it is not supported or invalid. It will return the version
        as a tuple with major, minor and patch.

        Raises InterfaceError if invalid server version.

        Returns tuple
        """
        if isinstance(server_version, (bytearray, bytes)):
            server_version = server_version.decode()

        # pylint: disable=W1401
        regex_ver = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{1,3})(.*)")
        # pylint: enable=W1401
        match = regex_ver.match(server_version)
        if not match:
            raise errors.InterfaceError("Failed parsing MySQL version")

        version = tuple([int(v) for v in match.groups()[0:3]])
        if version < (4, 1):
            raise errors.InterfaceError(
                "MySQL Version '{0}' is not supported.".format(server_version))

        return version

    def get_server_version(self):
        """Get the MySQL version

        This method returns the MySQL server version as a tuple. If not
        previously connected, it will return None.

        Returns a tuple or None.
        """
        return self._server_version

    def get_server_info(self):
        """Get the original MySQL version information

        This method returns the original MySQL server as text. If not
        previously connected, it will return None.

        Returns a string or None.
        """
        try:
            return self._handshake['server_version_original']
        except (TypeError, KeyError):
            return None

    @abstractproperty
    def in_transaction(self):
        """MySQL session has started a transaction"""
        pass

    def set_client_flags(self, flags):
        """Set the client flags

        The flags-argument can be either an int or a list (or tuple) of
        ClientFlag-values. If it is an integer, it will set client_flags
        to flags as is.
        If flags is a list (or tuple), each flag will be set or unset
        when it's negative.

        set_client_flags([ClientFlag.FOUND_ROWS,-ClientFlag.LONG_FLAG])

        Raises ProgrammingError when the flags argument is not a set or
        an integer bigger than 0.

        Returns self.client_flags
        """
        if isinstance(flags, int) and flags > 0:
            self._client_flags = flags
        elif isinstance(flags, (tuple, list)):
            for flag in flags:
                if flag < 0:
                    self._client_flags &= ~abs(flag)
                else:
                    self._client_flags |= flag
        else:
            raise errors.ProgrammingError(
                "set_client_flags expect integer (>0) or set")
        return self._client_flags

    def isset_client_flag(self, flag):
        """Check if a client flag is set"""
        if (self._client_flags & flag) > 0:
            return True
        return False

    @property
    def time_zone(self):
        """Get the current time zone"""
        return self.info_query("SELECT @@session.time_zone")[0]

    @time_zone.setter
    def time_zone(self, value):
        """Set the time zone"""
        self.cmd_query("SET @@session.time_zone = '{0}'".format(value))
        self._time_zone = value

    @property
    def sql_mode(self):
        """Get the SQL mode"""
        return self.info_query("SELECT @@session.sql_mode")[0]

    @sql_mode.setter
    def sql_mode(self, value):
        """Set the SQL mode

        This method sets the SQL Mode for the current connection. The value
        argument can be either a string with comma separate mode names, or
        a sequence of mode names.

        It is good practice to use the constants class SQLMode:
          from mysql.connector.constants import SQLMode
          cnx.sql_mode = [SQLMode.NO_ZERO_DATE, SQLMode.REAL_AS_FLOAT]
        """
        if isinstance(value, (list, tuple)):
            value = ','.join(value)
        self.cmd_query("SET @@session.sql_mode = '{0}'".format(value))
        self._sql_mode = value

    @abstractmethod
    def info_query(self, query):
        """Send a query which only returns 1 row"""
        pass

    def set_login(self, username=None, password=None):
        """Set login information for MySQL

        Set the username and/or password for the user connecting to
        the MySQL Server.
        """
        if username is not None:
            self._user = username.strip()
        else:
            self._user = ''
        if password is not None:
            self._password = password
        else:
            self._password = ''

    def set_unicode(self, value=True):
        """Toggle unicode mode

        Set whether we return string fields as unicode or not.
        Default is True.
        """
        self._use_unicode = value
        if self.converter:
            self.converter.set_unicode(value)

    @property
    def autocommit(self):
        """Get whether autocommit is on or off"""
        value = self.info_query("SELECT @@session.autocommit")[0]
        return True if value == 1 else False

    @autocommit.setter
    def autocommit(self, value):
        """Toggle autocommit"""
        switch = 'ON' if value else 'OFF'
        self.cmd_query("SET @@session.autocommit = {0}".format(switch))
        self._autocommit = value

    @property
    def get_warnings(self):
        """Get whether this connection retrieves warnings automatically

        This method returns whether this connection retrieves warnings
        automatically.

        Returns True, or False when warnings are not retrieved.
        """
        return self._get_warnings

    @get_warnings.setter
    def get_warnings(self, value):
        """Set whether warnings should be automatically retrieved

        The toggle-argument must be a boolean. When True, cursors for this
        connection will retrieve information about warnings (if any).

        Raises ValueError on error.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._get_warnings = value

    @property
    def raise_on_warnings(self):
        """Get whether this connection raises an error on warnings

        This method returns whether this connection will raise errors when
        MySQL reports warnings.

        Returns True or False.
        """
        return self._raise_on_warnings

    @raise_on_warnings.setter
    def raise_on_warnings(self, value):
        """Set whether warnings raise an error

        The toggle-argument must be a boolean. When True, cursors for this
        connection will raise an error when MySQL reports warnings.

        Raising on warnings implies retrieving warnings automatically. In
        other words: warnings will be set to True. If set to False, warnings
        will be also set to False.

        Raises ValueError on error.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._raise_on_warnings = value
        self._get_warnings = value


    @property
    def unread_result(self):
        """Get whether there is an unread result

        This method is used by cursors to check whether another cursor still
        needs to retrieve its result set.

        Returns True, or False when there is no unread result.
        """
        return self._unread_result

    @unread_result.setter
    def unread_result(self, value):
        """Set whether there is an unread result

        This method is used by cursors to let other cursors know there is
        still a result set that needs to be retrieved.

        Raises ValueError on errors.
        """
        if not isinstance(value, bool):
            raise ValueError("Expected a boolean type")
        self._unread_result = value

    @property
    def charset(self):
        """Returns the character set for current connection

        This property returns the character set name of the current connection.
        The server is queried when the connection is active. If not connected,
        the configured character set name is returned.

        Returns a string.
        """
        return CharacterSet.get_info(self._charset_id)[0]

    @property
    def python_charset(self):
        """Returns the Python character set for current connection

        This property returns the character set name of the current connection.
        Note that, unlike property charset, this checks if the previously set
        character set is supported by Python and if not, it returns the
        equivalent character set that Python supports.

        Returns a string.
        """
        encoding = CharacterSet.get_info(self._charset_id)[0]
        if encoding in ('utf8mb4', 'binary'):
            return 'utf8'
        return encoding

    def set_charset_collation(self, charset=None, collation=None):
        """Sets the character set and collation for the current connection

        This method sets the character set and collation to be used for
        the current connection. The charset argument can be either the
        name of a character set as a string, or the numerical equivalent
        as defined in constants.CharacterSet.

        When the collation is not given, the default will be looked up and
        used.

        For example, the following will set the collation for the latin1
        character set to latin1_general_ci:

           set_charset('latin1','latin1_general_ci')

        """
        if charset:
            if isinstance(charset, int):
                (self._charset_id, charset_name, collation_name) = \
                    CharacterSet.get_charset_info(charset)
            elif isinstance(charset, str):
                (self._charset_id, charset_name, collation_name) = \
                    CharacterSet.get_charset_info(charset, collation)
            else:
                raise ValueError(
                    "charset should be either integer, string or None")
        elif collation:
            (self._charset_id, charset_name, collation_name) = \
                    CharacterSet.get_charset_info(collation=collation)

        self._execute_query("SET NAMES '{0}' COLLATE '{1}'".format(
            charset_name, collation_name))

        try:
            # Required for C Extension
            self.set_character_set_name(charset_name)  # pylint: disable=E1101
        except AttributeError:
            # Not required for pure Python connection
            pass

        if self.converter:
            self.converter.set_charset(charset_name)

    @property
    def collation(self):
        """Returns the collation for current connection

        This property returns the collation name of the current connection.
        The server is queried when the connection is active. If not connected,
        the configured collation name is returned.

        Returns a string.
        """
        return CharacterSet.get_charset_info(self._charset_id)[2]

    @abstractmethod
    def _do_handshake(self):
        """Gather information of the MySQL server before authentication"""
        pass

    @abstractmethod
    def _open_connection(self):
        """Open the connection to the MySQL server"""
        pass

    def _post_connection(self):
        """Executes commands after connection has been established

        This method executes commands after the connection has been
        established. Some setting like autocommit, character set, and SQL mode
        are set using this method.
        """
        self.set_charset_collation(self._charset_id)
        self.autocommit = self._autocommit
        if self._time_zone:
            self.time_zone = self._time_zone
        if self._sql_mode:
            self.sql_mode = self._sql_mode

    @abstractmethod
    def disconnect(self):
        """Disconnect from the MySQL server"""
        pass
    close = disconnect

    def connect(self, **kwargs):
        """Connect to the MySQL server

        This method sets up the connection to the MySQL server. If no
        arguments are given, it will use the already configured or default
        values.
        """
        if kwargs:
            self.config(**kwargs)

        self.disconnect()
        self._open_connection()
        # Server does not allow to run any other statement different from ALTER
        # when user's password has been expired.
        if not self._client_flags & ClientFlag.CAN_HANDLE_EXPIRED_PASSWORDS:
            self._post_connection()

    def reconnect(self, attempts=1, delay=0):
        """Attempt to reconnect to the MySQL server

        The argument attempts should be the number of times a reconnect
        is tried. The delay argument is the number of seconds to wait between
        each retry.

        You may want to set the number of attempts higher and use delay when
        you expect the MySQL server to be down for maintenance or when you
        expect the network to be temporary unavailable.

        Raises InterfaceError on errors.
        """
        counter = 0
        while counter != attempts:
            counter = counter + 1
            try:
                self.disconnect()
                self.connect()
                if self.is_connected():
                    break
            except Exception as err:  # pylint: disable=W0703
                if counter == attempts:
                    msg = "Can not reconnect to MySQL after {0} "\
                          "attempt(s): {1}".format(attempts, str(err))
                    raise errors.InterfaceError(msg)
            if delay > 0:
                sleep(delay)

    @abstractmethod
    def is_connected(self):
        """Reports whether the connection to MySQL Server is available"""
        pass

    @abstractmethod
    def ping(self, reconnect=False, attempts=1, delay=0):
        """Check availability of the MySQL server"""
        pass

    @abstractmethod
    def commit(self):
        """Commit current transaction"""
        pass

    @abstractmethod
    def cursor(self, buffered=None, raw=None, prepared=None, cursor_class=None,
               dictionary=None, named_tuple=None):
        """Instantiates and returns a cursor"""
        pass

    @abstractmethod
    def _execute_query(self, query):
        """Execute a query"""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback current transaction"""
        pass

    def start_transaction(self, consistent_snapshot=False,
                          isolation_level=None, readonly=None):
        """Start a transaction

        This method explicitly starts a transaction sending the
        START TRANSACTION statement to the MySQL server. You can optionally
        set whether there should be a consistent snapshot, which
        isolation level you need or which access mode i.e. READ ONLY or
        READ WRITE.

        For example, to start a transaction with isolation level SERIALIZABLE,
        you would do the following:
            >>> cnx = mysql.connector.connect(..)
            >>> cnx.start_transaction(isolation_level='SERIALIZABLE')

        Raises ProgrammingError when a transaction is already in progress
        and when ValueError when isolation_level specifies an Unknown
        level.
        """
        if self.in_transaction:
            raise errors.ProgrammingError("Transaction already in progress")

        if isolation_level:
            level = isolation_level.strip().replace('-', ' ').upper()
            levels = ['READ UNCOMMITTED', 'READ COMMITTED', 'REPEATABLE READ',
                      'SERIALIZABLE']

            if level not in levels:
                raise ValueError(
                    'Unknown isolation level "{0}"'.format(isolation_level))

            self._execute_query(
                "SET TRANSACTION ISOLATION LEVEL {0}".format(level))

        if readonly is not None:
            if self._server_version < (5, 6, 5):
                raise ValueError(
                    "MySQL server version {0} does not support "
                    "this feature".format(self._server_version))

            if readonly:
                access_mode = 'READ ONLY'
            else:
                access_mode = 'READ WRITE'
            self._execute_query(
                "SET TRANSACTION {0}".format(access_mode))

        query = "START TRANSACTION"
        if consistent_snapshot:
            query += " WITH CONSISTENT SNAPSHOT"
        self.cmd_query(query)

    def reset_session(self, user_variables=None, session_variables=None):
        """Clears the current active session

        This method resets the session state, if the MySQL server is 5.7.3
        or later active session will be reset without re-authenticating.
        For other server versions session will be reset by re-authenticating.

        It is possible to provide a sequence of variables and their values to
        be set after clearing the session. This is possible for both user
        defined variables and session variables.
        This method takes two arguments user_variables and session_variables
        which are dictionaries.

        Raises OperationalError if not connected, InternalError if there are
        unread results and InterfaceError on errors.
        """
        if not self.is_connected():
            raise errors.OperationalError("MySQL Connection not available.")

        try:
            self.cmd_reset_connection()
        except (errors.NotSupportedError, NotImplementedError):
            if self._compress:
                raise errors.NotSupportedError(
                    "Reset session is not supported with compression for "
                    "MySQL server version 5.7.2 or earlier.")
            else:
                self.cmd_change_user(self._user, self._password,
                                     self._database, self._charset_id)

        if user_variables or session_variables:
            cur = self.cursor()
            if user_variables:
                for key, value in user_variables.items():
                    cur.execute("SET @`{0}` = %s".format(key), (value,))
            if session_variables:
                for key, value in session_variables.items():
                    cur.execute("SET SESSION `{0}` = %s".format(key), (value,))
            cur.close()

    def set_converter_class(self, convclass):
        """
        Set the converter class to be used. This should be a class overloading
        methods and members of conversion.MySQLConverter.
        """
        if convclass and issubclass(convclass, MySQLConverterBase):
            charset_name = CharacterSet.get_info(self._charset_id)[0]
            self._converter_class = convclass
            self.converter = convclass(charset_name, self._use_unicode)
            self.converter.str_fallback = self._converter_str_fallback
        else:
            raise TypeError("Converter class should be a subclass "
                            "of conversion.MySQLConverterBase.")

    @abstractmethod
    def get_rows(self, count=None, binary=False, columns=None, raw=None,
                 prep_stmt=None):
        """Get all rows returned by the MySQL server"""
        pass

    def cmd_init_db(self, database):
        """Change the current database"""
        raise NotImplementedError

    def cmd_query(self, query, raw=False, buffered=False, raw_as_string=False):
        """Send a query to the MySQL server"""
        raise NotImplementedError

    def cmd_query_iter(self, statements):
        """Send one or more statements to the MySQL server"""
        raise NotImplementedError

    def cmd_refresh(self, options):
        """Send the Refresh command to the MySQL server"""
        raise NotImplementedError

    def cmd_quit(self):
        """Close the current connection with the server"""
        raise NotImplementedError

    def cmd_shutdown(self, shutdown_type=None):
        """Shut down the MySQL Server"""
        raise NotImplementedError

    def cmd_statistics(self):
        """Send the statistics command to the MySQL Server"""
        raise NotImplementedError

    def cmd_process_info(self):
        """Get the process list of the MySQL Server

        This method is a placeholder to notify that the PROCESS_INFO command
        is not supported by raising the NotSupportedError. The command
        "SHOW PROCESSLIST" should be send using the cmd_query()-method or
        using the INFORMATION_SCHEMA database.

        Raises NotSupportedError exception
        """
        raise errors.NotSupportedError(
            "Not implemented. Use SHOW PROCESSLIST or INFORMATION_SCHEMA")

    def cmd_process_kill(self, mysql_pid):
        """Kill a MySQL process"""
        raise NotImplementedError

    def cmd_debug(self):
        """Send the DEBUG command"""
        raise NotImplementedError

    def cmd_ping(self):
        """Send the PING command"""
        raise NotImplementedError

    def cmd_change_user(self, username='', password='', database='',
                        charset=45, password1='', password2='', password3=''):
        """Change the current logged in user"""
        raise NotImplementedError

    def cmd_stmt_prepare(self, statement):
        """Prepare a MySQL statement"""
        raise NotImplementedError

    def cmd_stmt_execute(self, statement_id, data=(), parameters=(), flags=0):
        """Execute a prepared MySQL statement"""
        raise NotImplementedError

    def cmd_stmt_close(self, statement_id):
        """Deallocate a prepared MySQL statement"""
        raise NotImplementedError

    def cmd_stmt_send_long_data(self, statement_id, param_id, data):
        """Send data for a column"""
        raise NotImplementedError

    def cmd_stmt_reset(self, statement_id):
        """Reset data for prepared statement sent as long data"""
        raise NotImplementedError

    def cmd_reset_connection(self):
        """Resets the session state without re-authenticating"""
        raise NotImplementedError


@make_abc(ABCMeta)
class MySQLCursorAbstract(object):
    """Abstract cursor class

    Abstract class defining cursor class with method and members
    required by the Python Database API Specification v2.0.
    """
    def __init__(self):
        """Initialization"""
        self._description = None
        self._rowcount = -1
        self._last_insert_id = None
        self._warnings = None
        self.arraysize = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def callproc(self, procname, args=()):
        """Calls a stored procedure with the given arguments

        The arguments will be set during this session, meaning
        they will be called like  _<procname>__arg<nr> where
        <nr> is an enumeration (+1) of the arguments.

        Coding Example:
          1) Defining the Stored Routine in MySQL:
          CREATE PROCEDURE multiply(IN pFac1 INT, IN pFac2 INT, OUT pProd INT)
          BEGIN
            SET pProd := pFac1 * pFac2;
          END

          2) Executing in Python:
          args = (5,5,0) # 0 is to hold pprod
          cursor.callproc('multiply', args)
          print(cursor.fetchone())

        Does not return a value, but a result set will be
        available when the CALL-statement execute successfully.
        Raises exceptions when something is wrong.
        """
        pass

    @abstractmethod
    def close(self):
        """Close the cursor."""
        pass

    @abstractmethod
    def execute(self, operation, params=(), multi=False):
        """Executes the given operation

        Executes the given operation substituting any markers with
        the given parameters.

        For example, getting all rows where id is 5:
          cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))

        The multi argument should be set to True when executing multiple
        statements in one operation. If not set and multiple results are
        found, an InterfaceError will be raised.

        If warnings where generated, and connection.get_warnings is True, then
        self._warnings will be a list containing these warnings.

        Returns an iterator when multi is True, otherwise None.
        """
        pass

    @abstractmethod
    def executemany(self, operation, seq_params):
        """Execute the given operation multiple times

        The executemany() method will execute the operation iterating
        over the list of parameters in seq_params.

        Example: Inserting 3 new employees and their phone number

        data = [
            ('Jane','555-001'),
            ('Joe', '555-001'),
            ('John', '555-003')
            ]
        stmt = "INSERT INTO employees (name, phone) VALUES ('%s','%s')"
        cursor.executemany(stmt, data)

        INSERT statements are optimized by batching the data, that is
        using the MySQL multiple rows syntax.

        Results are discarded. If they are needed, consider looping over
        data using the execute() method.
        """
        pass

    @abstractmethod
    def fetchone(self):
        """Returns next row of a query result set

        Returns a tuple or None.
        """
        pass

    @abstractmethod
    def fetchmany(self, size=1):
        """Returns the next set of rows of a query result, returning a
        list of tuples. When no more rows are available, it returns an
        empty list.

        The number of rows returned can be specified using the size argument,
        which defaults to one
        """
        pass

    @abstractmethod
    def fetchall(self):
        """Returns all rows of a query result set

        Returns a list of tuples.
        """
        pass

    def nextset(self):
        """Not Implemented."""
        pass

    def setinputsizes(self, sizes):
        """Not Implemented."""
        pass

    def setoutputsize(self, size, column=None):
        """Not Implemented."""
        pass

    def reset(self, free=True):
        """Reset the cursor to default"""
        pass

    @abstractproperty
    def description(self):
        """Returns description of columns in a result

        This property returns a list of tuples describing the columns in
        in a result set. A tuple is described as follows::

                (column_name,
                 type,
                 None,
                 None,
                 None,
                 None,
                 null_ok,
                 column_flags)  # Addition to PEP-249 specs

        Returns a list of tuples.
        """
        return self._description

    @abstractproperty
    def rowcount(self):
        """Returns the number of rows produced or affected

        This property returns the number of rows produced by queries
        such as a SELECT, or affected rows when executing DML statements
        like INSERT or UPDATE.

        Note that for non-buffered cursors it is impossible to know the
        number of rows produced before having fetched them all. For those,
        the number of rows will be -1 right after execution, and
        incremented when fetching rows.

        Returns an integer.
        """
        return self._rowcount

    @abstractproperty
    def lastrowid(self):
        """Returns the value generated for an AUTO_INCREMENT column

        Returns the value generated for an AUTO_INCREMENT column by
        the previous INSERT or UPDATE statement or None when there is
        no such value available.

        Returns a long value or None.
        """
        return self._last_insert_id

    def fetchwarnings(self):
        """Returns Warnings."""
        return self._warnings

    def get_attributes(self):
        """Get the added query attributes so far."""
        if hasattr(self, "_cnx"):
            return self._cnx._query_attrs
        elif hasattr(self, "_connection"):
            return self._connection._query_attrs

    def add_attribute(self, name, value):
        """Add a query attribute and his value."""
        if not isinstance(name, str):
            raise errors.ProgrammingError(
                "Parameter `name` must be a string type.")
        if value is not None and not isinstance(value, MYSQL_PY_TYPES):
            raise errors.ProgrammingError(
                f"Object {value} cannot be converted to a MySQL type.")
        if hasattr(self, "_cnx"):
            self._cnx._query_attrs.append((name, value))
        elif hasattr(self, "_connection"):
            self._connection._query_attrs.append((name, value))

    def clear_attributes(self):
        """Remove all the query attributes."""
        if hasattr(self, "_cnx"):
            self._cnx._query_attrs = []
        elif hasattr(self, "_connection"):
            self._connection._query_attrs = []
