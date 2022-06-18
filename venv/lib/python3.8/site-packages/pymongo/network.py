# Copyright 2015-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Internal network layer helper methods."""

import datetime
import errno
import socket
import struct


from bson import _decode_all_selective
from bson.py3compat import PY3

from pymongo import helpers, message
from pymongo.common import MAX_MESSAGE_SIZE
from pymongo.compression_support import decompress, _NO_COMPRESSION
from pymongo.errors import (AutoReconnect,
                            NotPrimaryError,
                            OperationFailure,
                            ProtocolError,
                            NetworkTimeout,
                            _OperationCancelled)
from pymongo.message import _UNPACK_REPLY, _OpMsg
from pymongo.monitoring import _is_speculative_authenticate
from pymongo.monotonic import time
from pymongo.socket_checker import _errno_from_exception


_UNPACK_HEADER = struct.Struct("<iiii").unpack


def command(sock_info, dbname, spec, secondary_ok, is_mongos,
            read_preference, codec_options, session, client, check=True,
            allowable_errors=None, address=None,
            check_keys=False, listeners=None, max_bson_size=None,
            read_concern=None,
            parse_write_concern_error=False,
            collation=None,
            compression_ctx=None,
            use_op_msg=False,
            unacknowledged=False,
            user_fields=None,
            exhaust_allowed=False):
    """Execute a command over the socket, or raise socket.error.

    :Parameters:
      - `sock`: a raw socket instance
      - `dbname`: name of the database on which to run the command
      - `spec`: a command document as an ordered dict type, eg SON.
      - `secondary_ok`: whether to set the secondaryOkay wire protocol bit
      - `is_mongos`: are we connected to a mongos?
      - `read_preference`: a read preference
      - `codec_options`: a CodecOptions instance
      - `session`: optional ClientSession instance.
      - `client`: optional MongoClient instance for updating $clusterTime.
      - `check`: raise OperationFailure if there are errors
      - `allowable_errors`: errors to ignore if `check` is True
      - `address`: the (host, port) of `sock`
      - `check_keys`: if True, check `spec` for invalid keys
      - `listeners`: An instance of :class:`~pymongo.monitoring.EventListeners`
      - `max_bson_size`: The maximum encoded bson size for this server
      - `read_concern`: The read concern for this command.
      - `parse_write_concern_error`: Whether to parse the ``writeConcernError``
        field in the command response.
      - `collation`: The collation for this command.
      - `compression_ctx`: optional compression Context.
      - `use_op_msg`: True if we should use OP_MSG.
      - `unacknowledged`: True if this is an unacknowledged command.
      - `user_fields` (optional): Response fields that should be decoded
        using the TypeDecoders from codec_options, passed to
        bson._decode_all_selective.
      - `exhaust_allowed`: True if we should enable OP_MSG exhaustAllowed.
    """
    name = next(iter(spec))
    ns = dbname + '.$cmd'
    flags = 4 if secondary_ok else 0
    speculative_hello = False

    # Publish the original command document, perhaps with lsid and $clusterTime.
    orig = spec
    if is_mongos and not use_op_msg:
        spec = message._maybe_add_read_preference(spec, read_preference)
    if read_concern and not (session and session.in_transaction):
        if read_concern.level:
            spec['readConcern'] = read_concern.document
        if session:
            session._update_read_concern(spec, sock_info)
    if collation is not None:
        spec['collation'] = collation

    publish = listeners is not None and listeners.enabled_for_commands
    if publish:
        start = datetime.datetime.now()
        speculative_hello = _is_speculative_authenticate(name, spec)

    if compression_ctx and name.lower() in _NO_COMPRESSION:
        compression_ctx = None

    if (client and client._encrypter and
            not client._encrypter._bypass_auto_encryption):
        spec = orig = client._encrypter.encrypt(
            dbname, spec, check_keys, codec_options)
        # We already checked the keys, no need to do it again.
        check_keys = False

    if use_op_msg:
        flags = _OpMsg.MORE_TO_COME if unacknowledged else 0
        flags |= _OpMsg.EXHAUST_ALLOWED if exhaust_allowed else 0
        request_id, msg, size, max_doc_size = message._op_msg(
            flags, spec, dbname, read_preference, secondary_ok, check_keys,
            codec_options, ctx=compression_ctx)
        # If this is an unacknowledged write then make sure the encoded doc(s)
        # are small enough, otherwise rely on the server to return an error.
        if (unacknowledged and max_bson_size is not None and
                max_doc_size > max_bson_size):
            message._raise_document_too_large(name, size, max_bson_size)
    else:
        request_id, msg, size = message.query(
            flags, ns, 0, -1, spec, None, codec_options, check_keys,
            compression_ctx)

    if (max_bson_size is not None
            and size > max_bson_size + message._COMMAND_OVERHEAD):
        message._raise_document_too_large(
            name, size, max_bson_size + message._COMMAND_OVERHEAD)

    if publish:
        encoding_duration = datetime.datetime.now() - start
        listeners.publish_command_start(orig, dbname, request_id, address,
                                        service_id=sock_info.service_id)
        start = datetime.datetime.now()

    try:
        sock_info.sock.sendall(msg)
        if use_op_msg and unacknowledged:
            # Unacknowledged, fake a successful command response.
            reply = None
            response_doc = {"ok": 1}
        else:
            reply = receive_message(sock_info, request_id)
            sock_info.more_to_come = reply.more_to_come
            unpacked_docs = reply.unpack_response(
                codec_options=codec_options, user_fields=user_fields)

            response_doc = unpacked_docs[0]
            if client:
                client._process_response(response_doc, session)
            if check:
                helpers._check_command_response(
                    response_doc, sock_info.max_wire_version, allowable_errors,
                    parse_write_concern_error=parse_write_concern_error)
    except Exception as exc:
        if publish:
            duration = (datetime.datetime.now() - start) + encoding_duration
            if isinstance(exc, (NotPrimaryError, OperationFailure)):
                failure = exc.details
            else:
                failure = message._convert_exception(exc)
            listeners.publish_command_failure(
                duration, failure, name, request_id, address,
                service_id=sock_info.service_id)
        raise
    if publish:
        duration = (datetime.datetime.now() - start) + encoding_duration
        listeners.publish_command_success(
            duration, response_doc, name, request_id, address,
            service_id=sock_info.service_id,
            speculative_hello=speculative_hello)

    if client and client._encrypter and reply:
        decrypted = client._encrypter.decrypt(reply.raw_command_response())
        response_doc = _decode_all_selective(decrypted, codec_options,
                                             user_fields)[0]

    return response_doc

_UNPACK_COMPRESSION_HEADER = struct.Struct("<iiB").unpack

def receive_message(sock_info, request_id, max_message_size=MAX_MESSAGE_SIZE):
    """Receive a raw BSON message or raise socket.error."""
    timeout = sock_info.sock.gettimeout()
    if timeout:
        deadline = time() + timeout
    else:
        deadline = None
    # Ignore the response's request id.
    length, _, response_to, op_code = _UNPACK_HEADER(
        _receive_data_on_socket(sock_info, 16, deadline))
    # No request_id for exhaust cursor "getMore".
    if request_id is not None:
        if request_id != response_to:
            raise ProtocolError("Got response id %r but expected "
                                "%r" % (response_to, request_id))
    if length <= 16:
        raise ProtocolError("Message length (%r) not longer than standard "
                            "message header size (16)" % (length,))
    if length > max_message_size:
        raise ProtocolError("Message length (%r) is larger than server max "
                            "message size (%r)" % (length, max_message_size))
    if op_code == 2012:
        op_code, _, compressor_id = _UNPACK_COMPRESSION_HEADER(
            _receive_data_on_socket(sock_info, 9, deadline))
        data = decompress(
            _receive_data_on_socket(sock_info, length - 25, deadline),
            compressor_id)
    else:
        data = _receive_data_on_socket(sock_info, length - 16, deadline)

    try:
        unpack_reply = _UNPACK_REPLY[op_code]
    except KeyError:
        raise ProtocolError("Got opcode %r but expected "
                            "%r" % (op_code, _UNPACK_REPLY.keys()))
    return unpack_reply(data)


_POLL_TIMEOUT = 0.5


def wait_for_read(sock_info, deadline):
    """Block until at least one byte is read, or a timeout, or a cancel."""
    context = sock_info.cancel_context
    # Only Monitor connections can be cancelled.
    if context:
        sock = sock_info.sock
        while True:
            # SSLSocket can have buffered data which won't be caught by select.
            if hasattr(sock, 'pending') and sock.pending() > 0:
                readable = True
            else:
                # Wait up to 500ms for the socket to become readable and then
                # check for cancellation.
                if deadline:
                    timeout = max(min(deadline - time(), _POLL_TIMEOUT), 0.001)
                else:
                    timeout = _POLL_TIMEOUT
                readable = sock_info.socket_checker.select(
                    sock, read=True, timeout=timeout)
            if context.cancelled:
                raise _OperationCancelled('hello cancelled')
            if readable:
                return
            if deadline and time() > deadline:
                raise socket.timeout("timed out")

# memoryview was introduced in Python 2.7 but we only use it on Python 3
# because before 2.7.4 the struct module did not support memoryview:
# https://bugs.python.org/issue10212.
# In Jython, using slice assignment on a memoryview results in a
# NullPointerException.
if not PY3:
    def _receive_data_on_socket(sock_info, length, deadline):
        buf = bytearray(length)
        i = 0
        while length:
            try:
                wait_for_read(sock_info, deadline)
                chunk = sock_info.sock.recv(length)
            except (IOError, OSError) as exc:
                if _errno_from_exception(exc) == errno.EINTR:
                    continue
                raise
            if chunk == b"":
                raise AutoReconnect("connection closed")

            buf[i:i + len(chunk)] = chunk
            i += len(chunk)
            length -= len(chunk)

        return bytes(buf)
else:
    def _receive_data_on_socket(sock_info, length, deadline):
        buf = bytearray(length)
        mv = memoryview(buf)
        bytes_read = 0
        while bytes_read < length:
            try:
                wait_for_read(sock_info, deadline)
                chunk_length = sock_info.sock.recv_into(mv[bytes_read:])
            except (IOError, OSError) as exc:
                if _errno_from_exception(exc) == errno.EINTR:
                    continue
                raise
            if chunk_length == 0:
                raise AutoReconnect("connection closed")

            bytes_read += chunk_length

        return mv
