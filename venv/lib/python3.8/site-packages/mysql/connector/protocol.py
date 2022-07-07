# Copyright (c) 2009, 2022, Oracle and/or its affiliates.
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

"""Implements the MySQL Client/Server protocol
"""

import struct
import datetime

from decimal import Decimal

from .constants import (
    FieldFlag, ServerCmd, FieldType, ClientFlag, PARAMETER_COUNT_AVAILABLE)
from . import errors, utils
from .authentication import get_auth_plugin
from .errors import DatabaseError, get_exception

PROTOCOL_VERSION = 10


class MySQLProtocol(object):
    """Implements MySQL client/server protocol

    Create and parses MySQL packets.
    """

    def _connect_with_db(self, client_flags, database):
        """Prepare database string for handshake response"""
        if client_flags & ClientFlag.CONNECT_WITH_DB and database:
            return database.encode('utf8') + b'\x00'
        return b'\x00'

    def _auth_response(self, client_flags, username, password, database,
                       auth_plugin, auth_data, ssl_enabled):
        """Prepare the authentication response"""
        if not password:
            return b'\x00'

        try:
            auth = get_auth_plugin(auth_plugin)(
                auth_data,
                username=username, password=password, database=database,
                ssl_enabled=ssl_enabled)
            plugin_auth_response = auth.auth_response()
        except (TypeError, errors.InterfaceError) as exc:
            raise errors.InterfaceError(
                "Failed authentication: {0}".format(str(exc)))

        if client_flags & ClientFlag.SECURE_CONNECTION:
            resplen = len(plugin_auth_response)
            auth_response = struct.pack('<B', resplen) + plugin_auth_response
        else:
            auth_response = plugin_auth_response + b'\x00'
        return auth_response

    def make_auth(self, handshake, username=None, password=None, database=None,
                  charset=45, client_flags=0,
                  max_allowed_packet=1073741824, ssl_enabled=False,
                  auth_plugin=None, conn_attrs=None):
        """Make a MySQL Authentication packet"""

        try:
            auth_data = handshake['auth_data']
            auth_plugin = auth_plugin or handshake['auth_plugin']
        except (TypeError, KeyError) as exc:
            raise errors.ProgrammingError(
                "Handshake misses authentication info ({0})".format(exc))

        if not username:
            username = b''
        try:
            username_bytes = username.encode('utf8')  # pylint: disable=E1103
        except AttributeError:
            # Username is already bytes
            username_bytes = username
        packet = struct.pack('<IIH{filler}{usrlen}sx'.format(
            filler='x' * 22, usrlen=len(username_bytes)),
                             client_flags, max_allowed_packet, charset,
                             username_bytes)

        packet += self._auth_response(client_flags, username, password,
                                      database,
                                      auth_plugin,
                                      auth_data, ssl_enabled)

        packet += self._connect_with_db(client_flags, database)

        if client_flags & ClientFlag.PLUGIN_AUTH:
            packet += auth_plugin.encode('utf8') + b'\x00'

        if (client_flags & ClientFlag.CONNECT_ARGS) and conn_attrs is not None:
            packet += self.make_conn_attrs(conn_attrs)

        return packet

    def make_conn_attrs(self, conn_attrs):
        """Encode the connection attributes"""
        for attr_name in conn_attrs:
            if conn_attrs[attr_name] is None:
                conn_attrs[attr_name] = ""
        conn_attrs_len = (
            sum([len(x) + len(conn_attrs[x]) for x in conn_attrs]) +
            len(conn_attrs.keys()) + len(conn_attrs.values()))

        conn_attrs_packet = struct.pack('<B', conn_attrs_len)
        for attr_name in conn_attrs:
            conn_attrs_packet += struct.pack('<B', len(attr_name))
            conn_attrs_packet += attr_name.encode('utf8')
            conn_attrs_packet += struct.pack('<B', len(conn_attrs[attr_name]))
            conn_attrs_packet += conn_attrs[attr_name].encode('utf8')
        return conn_attrs_packet

    def make_auth_ssl(self, charset=45, client_flags=0,
                      max_allowed_packet=1073741824):
        """Make a SSL authentication packet"""
        return utils.int4store(client_flags) + \
               utils.int4store(max_allowed_packet) + \
               utils.int2store(charset) + \
               b'\x00' * 22

    def make_command(self, command, argument=None):
        """Make a MySQL packet containing a command"""
        data = utils.int1store(command)
        if argument is not None:
            data += argument
        return data

    def make_stmt_fetch(self, statement_id, rows=1):
        """Make a MySQL packet with Fetch Statement command"""
        return utils.int4store(statement_id) + utils.int4store(rows)

    def make_change_user(self, handshake, username=None, password=None,
                         database=None, charset=45, client_flags=0,
                         ssl_enabled=False, auth_plugin=None, conn_attrs=None):
        """Make a MySQL packet with the Change User command"""

        try:
            auth_data = handshake['auth_data']
            auth_plugin = auth_plugin or handshake['auth_plugin']
        except (TypeError, KeyError) as exc:
            raise errors.ProgrammingError(
                "Handshake misses authentication info ({0})".format(exc))

        if not username:
            username = b''
        try:
            username_bytes = username.encode('utf8')  # pylint: disable=E1103
        except AttributeError:
            # Username is already bytes
            username_bytes = username
        packet = struct.pack('<B{usrlen}sx'.format(usrlen=len(username_bytes)),
                             ServerCmd.CHANGE_USER, username_bytes)

        packet += self._auth_response(client_flags, username, password,
                                      database,
                                      auth_plugin,
                                      auth_data, ssl_enabled)

        packet += self._connect_with_db(client_flags, database)

        packet += struct.pack('<H', charset)

        if client_flags & ClientFlag.PLUGIN_AUTH:
            packet += auth_plugin.encode('utf8') + b'\x00'

        if (client_flags & ClientFlag.CONNECT_ARGS) and conn_attrs is not None:
            packet += self.make_conn_attrs(conn_attrs)

        return packet

    def parse_handshake(self, packet):
        """Parse a MySQL Handshake-packet"""
        res = {}
        res['protocol'] = struct.unpack('<xxxxB', packet[0:5])[0]
        if res["protocol"] != PROTOCOL_VERSION:
            raise DatabaseError("Protocol mismatch; server version = {}, "
                                "client version = {}".format(res["protocol"],
                                                             PROTOCOL_VERSION))
        (packet, res['server_version_original']) = utils.read_string(
            packet[5:], end=b'\x00')

        (res['server_threadid'],
         auth_data1,
         capabilities1,
         res['charset'],
         res['server_status'],
         capabilities2,
         auth_data_length
        ) = struct.unpack('<I8sx2sBH2sBxxxxxxxxxx', packet[0:31])
        res['server_version_original'] = res['server_version_original'].decode()

        packet = packet[31:]

        capabilities = utils.intread(capabilities1 + capabilities2)
        auth_data2 = b''
        if capabilities & ClientFlag.SECURE_CONNECTION:
            size = min(13, auth_data_length - 8) if auth_data_length else 13
            auth_data2 = packet[0:size]
            packet = packet[size:]
            if auth_data2[-1] == 0:
                auth_data2 = auth_data2[:-1]

        if capabilities & ClientFlag.PLUGIN_AUTH:
            if (b'\x00' not in packet
                    and res['server_version_original'].startswith("5.5.8")):
                # MySQL server 5.5.8 has a bug where end byte is not send
                (packet, res['auth_plugin']) = (b'', packet)
            else:
                (packet, res['auth_plugin']) = utils.read_string(
                    packet, end=b'\x00')
            res['auth_plugin'] = res['auth_plugin'].decode('utf-8')
        else:
            res['auth_plugin'] = 'mysql_native_password'

        res['auth_data'] = auth_data1 + auth_data2
        res['capabilities'] = capabilities
        return res

    def parse_auth_next_factor(self, packet):
        """Parse a MySQL AuthNextFactor packet."""
        packet, status = utils.read_int(packet, 1)
        if not status == 2:
            raise errors.InterfaceError(
                "Failed parsing AuthNextFactor packet (invalid)"
            )
        packet, auth_plugin = utils.read_string(packet, end=b"\x00")
        return packet, auth_plugin.decode("utf-8")


    def parse_ok(self, packet):
        """Parse a MySQL OK-packet"""
        if not packet[4] == 0:
            raise errors.InterfaceError("Failed parsing OK packet (invalid).")

        ok_packet = {}
        try:
            ok_packet['field_count'] = struct.unpack('<xxxxB', packet[0:5])[0]
            (packet, ok_packet['affected_rows']) = utils.read_lc_int(packet[5:])
            (packet, ok_packet['insert_id']) = utils.read_lc_int(packet)
            (ok_packet['status_flag'],
             ok_packet['warning_count']) = struct.unpack('<HH', packet[0:4])
            packet = packet[4:]
            if packet:
                (packet, ok_packet['info_msg']) = utils.read_lc_string(packet)
                ok_packet['info_msg'] = ok_packet['info_msg'].decode('utf-8')
        except ValueError:
            raise errors.InterfaceError("Failed parsing OK packet.")
        return ok_packet

    def parse_column_count(self, packet):
        """Parse a MySQL packet with the number of columns in result set"""
        try:
            count = utils.read_lc_int(packet[4:])[1]
            return count
        except (struct.error, ValueError):
            raise errors.InterfaceError("Failed parsing column count")

    def parse_column(self, packet, encoding='utf-8'):
        """Parse a MySQL column-packet"""
        (packet, _) = utils.read_lc_string(packet[4:])  # catalog
        (packet, _) = utils.read_lc_string(packet)  # db
        (packet, _) = utils.read_lc_string(packet)  # table
        (packet, _) = utils.read_lc_string(packet)  # org_table
        (packet, name) = utils.read_lc_string(packet)  # name
        (packet, _) = utils.read_lc_string(packet)  # org_name

        try:
            (
                charset,
                _,
                column_type,
                flags,
                _,
            ) = struct.unpack('<xHIBHBxx', packet)
        except struct.error:
            raise errors.InterfaceError("Failed parsing column information")

        return (
            name.decode(encoding),
            column_type,
            None,  # display_size
            None,  # internal_size
            None,  # precision
            None,  # scale
            ~flags & FieldFlag.NOT_NULL,  # null_ok
            flags,  # MySQL specific
            charset,
        )

    def parse_eof(self, packet):
        """Parse a MySQL EOF-packet"""
        if packet[4] == 0:
            # EOF packet deprecation
            return self.parse_ok(packet)

        err_msg = "Failed parsing EOF packet."
        res = {}
        try:
            unpacked = struct.unpack('<xxxBBHH', packet)
        except struct.error:
            raise errors.InterfaceError(err_msg)

        if not (unpacked[1] == 254 and len(packet) <= 9):
            raise errors.InterfaceError(err_msg)

        res['warning_count'] = unpacked[2]
        res['status_flag'] = unpacked[3]
        return res

    def parse_statistics(self, packet, with_header=True):
        """Parse the statistics packet"""
        errmsg = "Failed getting COM_STATISTICS information"
        res = {}
        # Information is separated by 2 spaces
        if with_header:
            pairs = packet[4:].split(b'\x20\x20')
        else:
            pairs = packet.split(b'\x20\x20')
        for pair in pairs:
            try:
                (lbl, val) = [v.strip() for v in pair.split(b':', 2)]
            except:
                raise errors.InterfaceError(errmsg)

            # It's either an integer or a decimal
            lbl = lbl.decode('utf-8')
            try:
                res[lbl] = int(val)
            except:
                try:
                    res[lbl] = Decimal(val.decode('utf-8'))
                except:
                    raise errors.InterfaceError(
                        "{0} ({1}:{2}).".format(errmsg, lbl, val))
        return res

    def read_text_result(self, sock, version, count=1):
        """Read MySQL text result

        Reads all or given number of rows from the socket.

        Returns a tuple with 2 elements: a list with all rows and
        the EOF packet.
        """
        rows = []
        eof = None
        rowdata = None
        i = 0
        while True:
            if eof or i == count:
                break
            packet = sock.recv()
            if packet.startswith(b'\xff\xff\xff'):
                datas = [packet[4:]]
                packet = sock.recv()
                while packet.startswith(b'\xff\xff\xff'):
                    datas.append(packet[4:])
                    packet = sock.recv()
                datas.append(packet[4:])
                rowdata = utils.read_lc_string_list(bytearray(b'').join(datas))
            elif packet[4] == 254 and packet[0] < 7:
                eof = self.parse_eof(packet)
                rowdata = None
            else:
                eof = None
                rowdata = utils.read_lc_string_list(packet[4:])
            if eof is None and rowdata is not None:
                rows.append(rowdata)
            elif eof is None and rowdata is None:
                raise get_exception(packet)
            i += 1
        return rows, eof

    def _parse_binary_integer(self, packet, field):
        """Parse an integer from a binary packet"""
        if field[1] == FieldType.TINY:
            format_ = '<b'
            length = 1
        elif field[1] == FieldType.SHORT:
            format_ = '<h'
            length = 2
        elif field[1] in (FieldType.INT24, FieldType.LONG):
            format_ = '<i'
            length = 4
        elif field[1] == FieldType.LONGLONG:
            format_ = '<q'
            length = 8

        if field[7] & FieldFlag.UNSIGNED:
            format_ = format_.upper()

        return (packet[length:], struct.unpack(format_, packet[0:length])[0])

    def _parse_binary_float(self, packet, field):
        """Parse a float/double from a binary packet"""
        if field[1] == FieldType.DOUBLE:
            length = 8
            format_ = '<d'
        else:
            length = 4
            format_ = '<f'

        return (packet[length:], struct.unpack(format_, packet[0:length])[0])

    def _parse_binary_new_decimal(self, packet, charset='utf8'):
        """Parse a New Decimal from a binary packet"""
        (packet, value) = utils.read_lc_string(packet)
        return (packet, Decimal(value.decode(charset)))

    def _parse_binary_timestamp(self, packet, field):
        """Parse a timestamp from a binary packet"""
        length = packet[0]
        value = None
        if length == 4:
            value = datetime.date(
                year=struct.unpack('<H', packet[1:3])[0],
                month=packet[3],
                day=packet[4])
        elif length >= 7:
            mcs = 0
            if length == 11:
                mcs = struct.unpack('<I', packet[8:length + 1])[0]
            value = datetime.datetime(
                year=struct.unpack('<H', packet[1:3])[0],
                month=packet[3],
                day=packet[4],
                hour=packet[5],
                minute=packet[6],
                second=packet[7],
                microsecond=mcs)

        return (packet[length + 1:], value)

    def _parse_binary_time(self, packet, field):
        """Parse a time value from a binary packet"""
        length = packet[0]
        data = packet[1:length + 1]
        mcs = 0
        if length > 8:
            mcs = struct.unpack('<I', data[8:])[0]
        days = struct.unpack('<I', data[1:5])[0]
        if data[0] == 1:
            days *= -1
        tmp = datetime.timedelta(days=days,
                                 seconds=data[7],
                                 microseconds=mcs,
                                 minutes=data[6],
                                 hours=data[5])

        return (packet[length + 1:], tmp)

    def _parse_binary_values(self, fields, packet, charset='utf-8'):
        """Parse values from a binary result packet"""
        null_bitmap_length = (len(fields) + 7 + 2) // 8
        null_bitmap = [int(i) for i in packet[0:null_bitmap_length]]
        packet = packet[null_bitmap_length:]

        values = []
        for pos, field in enumerate(fields):
            if null_bitmap[int((pos+2)/8)] & (1 << (pos + 2) % 8):
                values.append(None)
                continue
            elif field[1] in (FieldType.TINY, FieldType.SHORT,
                              FieldType.INT24,
                              FieldType.LONG, FieldType.LONGLONG):
                (packet, value) = self._parse_binary_integer(packet, field)
                values.append(value)
            elif field[1] in (FieldType.DOUBLE, FieldType.FLOAT):
                (packet, value) = self._parse_binary_float(packet, field)
                values.append(value)
            elif field[1] in (FieldType.DECIMAL, FieldType.NEWDECIMAL):
                (packet, value) = self._parse_binary_new_decimal(packet, charset)
                values.append(value)
            elif field[1] in (FieldType.DATETIME, FieldType.DATE,
                              FieldType.TIMESTAMP):
                (packet, value) = self._parse_binary_timestamp(packet, field)
                values.append(value)
            elif field[1] == FieldType.TIME:
                (packet, value) = self._parse_binary_time(packet, field)
                values.append(value)
            else:
                (packet, value) = utils.read_lc_string(packet)
                values.append(value.decode(charset))

        return tuple(values)

    def read_binary_result(self, sock, columns, count=1, charset='utf-8'):
        """Read MySQL binary protocol result

        Reads all or given number of binary resultset rows from the socket.
        """
        rows = []
        eof = None
        values = None
        i = 0
        while True:
            if eof is not None:
                break
            if i == count:
                break
            packet = sock.recv()
            if packet[4] == 254:
                eof = self.parse_eof(packet)
                values = None
            elif packet[4] == 0:
                eof = None
                values = self._parse_binary_values(columns, packet[5:], charset)
            if eof is None and values is not None:
                rows.append(values)
            elif eof is None and values is None:
                raise get_exception(packet)
            i += 1
        return (rows, eof)

    def parse_binary_prepare_ok(self, packet):
        """Parse a MySQL Binary Protocol OK packet"""
        if not packet[4] == 0:
            raise errors.InterfaceError("Failed parsing Binary OK packet")

        ok_pkt = {}
        try:
            (packet, ok_pkt['statement_id']) = utils.read_int(packet[5:], 4)
            (packet, ok_pkt['num_columns']) = utils.read_int(packet, 2)
            (packet, ok_pkt['num_params']) = utils.read_int(packet, 2)
            packet = packet[1:]  # Filler 1 * \x00
            (packet, ok_pkt['warning_count']) = utils.read_int(packet, 2)
        except ValueError:
            raise errors.InterfaceError("Failed parsing Binary OK packet")

        return ok_pkt

    def _prepare_binary_integer(self, value):
        """Prepare an integer for the MySQL binary protocol"""
        field_type = None
        flags = 0
        if value < 0:
            if value >= -128:
                format_ = '<b'
                field_type = FieldType.TINY
            elif value >= -32768:
                format_ = '<h'
                field_type = FieldType.SHORT
            elif value >= -2147483648:
                format_ = '<i'
                field_type = FieldType.LONG
            else:
                format_ = '<q'
                field_type = FieldType.LONGLONG
        else:
            flags = 128
            if value <= 255:
                format_ = '<B'
                field_type = FieldType.TINY
            elif value <= 65535:
                format_ = '<H'
                field_type = FieldType.SHORT
            elif value <= 4294967295:
                format_ = '<I'
                field_type = FieldType.LONG
            else:
                field_type = FieldType.LONGLONG
                format_ = '<Q'
        return (struct.pack(format_, value), field_type, flags)

    def _prepare_binary_timestamp(self, value):
        """Prepare a timestamp object for the MySQL binary protocol

        This method prepares a timestamp of type datetime.datetime or
        datetime.date for sending over the MySQL binary protocol.
        A tuple is returned with the prepared value and field type
        as elements.

        Raises ValueError when the argument value is of invalid type.

        Returns a tuple.
        """
        if isinstance(value, datetime.datetime):
            field_type = FieldType.DATETIME
        elif isinstance(value, datetime.date):
            field_type = FieldType.DATE
        else:
            raise ValueError(
                "Argument must a datetime.datetime or datetime.date")

        packed = (utils.int2store(value.year) +
                  utils.int1store(value.month) +
                  utils.int1store(value.day))

        if isinstance(value, datetime.datetime):
            packed = (packed + utils.int1store(value.hour) +
                      utils.int1store(value.minute) +
                      utils.int1store(value.second))
            if value.microsecond > 0:
                packed += utils.int4store(value.microsecond)

        packed = utils.int1store(len(packed)) + packed
        return (packed, field_type)

    def _prepare_binary_time(self, value):
        """Prepare a time object for the MySQL binary protocol

        This method prepares a time object of type datetime.timedelta or
        datetime.time for sending over the MySQL binary protocol.
        A tuple is returned with the prepared value and field type
        as elements.

        Raises ValueError when the argument value is of invalid type.

        Returns a tuple.
        """
        if not isinstance(value, (datetime.timedelta, datetime.time)):
            raise ValueError(
                "Argument must a datetime.timedelta or datetime.time")

        field_type = FieldType.TIME
        negative = 0
        mcs = None
        packed = b''

        if isinstance(value, datetime.timedelta):
            if value.days < 0:
                negative = 1
            (hours, remainder) = divmod(value.seconds, 3600)
            (mins, secs) = divmod(remainder, 60)
            packed += (utils.int4store(abs(value.days)) +
                       utils.int1store(hours) +
                       utils.int1store(mins) +
                       utils.int1store(secs))
            mcs = value.microseconds
        else:
            packed += (utils.int4store(0) +
                       utils.int1store(value.hour) +
                       utils.int1store(value.minute) +
                       utils.int1store(value.second))
            mcs = value.microsecond
        if mcs:
            packed += utils.int4store(mcs)

        packed = utils.int1store(negative) + packed
        packed = utils.int1store(len(packed)) + packed

        return (packed, field_type)

    def _prepare_stmt_send_long_data(self, statement, param, data):
        """Prepare long data for prepared statements

        Returns a string.
        """
        packet = (
            utils.int4store(statement) +
            utils.int2store(param) +
            data)
        return packet

    def make_stmt_execute(self, statement_id, data=(), parameters=(),
                          flags=0, long_data_used=None, charset='utf8',
                          query_attrs=None, converter_str_fallback=False):
        """Make a MySQL packet with the Statement Execute command"""
        iteration_count = 1
        null_bitmap = [0] * ((len(data) + 7) // 8)
        values = []
        types = []
        packed = b''
        data_len = len(data)
        query_attr_names = []
        flags = flags if not query_attrs else flags + PARAMETER_COUNT_AVAILABLE
        if charset == 'utf8mb4':
            charset = 'utf8'
        if long_data_used is None:
            long_data_used = {}
        if query_attrs:
            data = list(data)
            for _, attr_val in query_attrs:
                data.append(attr_val)
            null_bitmap = [0] * ((len(data) + 7) // 8)
        if parameters or data:
            if data_len != len(parameters):
                raise errors.InterfaceError(
                    "Failed executing prepared statement: data values does not"
                    " match number of parameters")
            for pos, _ in enumerate(data):
                value = data[pos]
                _flags = 0
                if value is None:
                    null_bitmap[(pos // 8)] |= 1 << (pos % 8)
                    types.append(utils.int1store(FieldType.NULL) +
                                 utils.int1store(_flags))
                    continue
                elif pos in long_data_used:
                    if long_data_used[pos][0]:
                        # We suppose binary data
                        field_type = FieldType.BLOB
                    else:
                        # We suppose text data
                        field_type = FieldType.STRING
                elif isinstance(value, int):
                    (packed, field_type,
                     _flags) = self._prepare_binary_integer(value)
                    values.append(packed)
                elif isinstance(value, str):
                    value = value.encode(charset)
                    values.append(utils.lc_int(len(value)) + value)
                    field_type = FieldType.VARCHAR
                elif isinstance(value, bytes):
                    values.append(utils.lc_int(len(value)) + value)
                    field_type = FieldType.BLOB
                elif isinstance(value, Decimal):
                    values.append(
                        utils.lc_int(len(str(value).encode(
                            charset))) + str(value).encode(charset))
                    field_type = FieldType.DECIMAL
                elif isinstance(value, float):
                    values.append(struct.pack('<d', value))
                    field_type = FieldType.DOUBLE
                elif isinstance(value, (datetime.datetime, datetime.date)):
                    (packed, field_type) = self._prepare_binary_timestamp(
                        value)
                    values.append(packed)
                elif isinstance(value, (datetime.timedelta, datetime.time)):
                    (packed, field_type) = self._prepare_binary_time(value)
                    values.append(packed)
                elif converter_str_fallback:
                    value = str(value).encode(charset)
                    values.append(utils.lc_int(len(value)) + value)
                    field_type = FieldType.STRING
                else:
                    raise errors.ProgrammingError(
                        "MySQL binary protocol can not handle "
                        "'{classname}' objects".format(
                            classname=value.__class__.__name__))
                types.append(utils.int1store(field_type) +
                             utils.int1store(_flags))
                if query_attrs and pos+1 > data_len:
                    name = query_attrs[pos - data_len][0].encode(charset)
                    query_attr_names.append(
                        utils.lc_int(len(name)) + name)
        packet = (
            utils.int4store(statement_id) +
            utils.int1store(flags) +
            utils.int4store(iteration_count))

        # if (num_params > 0 || (CLIENT_QUERY_ATTRIBUTES \
        #                        && (flags & PARAMETER_COUNT_AVAILABLE)) {
        if query_attrs is not None:
            parameter_count = data_len + len(query_attrs)
        else:
            parameter_count = data_len
        if parameter_count:
            # if CLIENT_QUERY_ATTRIBUTES is on
            if query_attrs is not None:
                packet += utils.lc_int(parameter_count)

            packet += (
                b''.join([struct.pack('B', bit) for bit in null_bitmap]) +
                utils.int1store(1))
            count = 0
            for a_type in types:
                packet += a_type
                # if CLIENT_QUERY_ATTRIBUTES is on {
                #    string<lenenc>    parameter_name    Name of the parameter
                # or empty if not present
                # } if CLIENT_QUERY_ATTRIBUTES is on
                if query_attrs is not None:
                    if count+1 > data_len:
                        packet += query_attr_names[count - data_len]
                    else:
                        packet += b'\x00'
                count+=1

            for a_value in values:
                packet += a_value

        return packet

    def parse_auth_switch_request(self, packet):
        """Parse a MySQL AuthSwitchRequest-packet"""
        if not packet[4] == 254:
            raise errors.InterfaceError(
                "Failed parsing AuthSwitchRequest packet")

        (packet, plugin_name) = utils.read_string(packet[5:], end=b'\x00')
        if packet and packet[-1] == 0:
            packet = packet[:-1]

        return plugin_name.decode('utf8'), packet

    def parse_auth_more_data(self, packet):
        """Parse a MySQL AuthMoreData-packet"""
        if not packet[4] == 1:
            raise errors.InterfaceError(
                "Failed parsing AuthMoreData packet")

        return packet[5:]
