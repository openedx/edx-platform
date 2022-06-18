# Copyright 2009-present MongoDB, Inc.
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

"""**DEPRECATED** Tools for creating `messages
<http://www.mongodb.org/display/DOCS/Mongo+Wire+Protocol>`_ to be sent to
MongoDB.

.. note:: This module is for internal use and is generally not needed by
   application developers.

.. versionchanged:: 3.12
  This module is deprecated and will be removed in PyMongo 4.0.
"""

import datetime
import random
import struct

import bson
from bson import (CodecOptions,
                  decode,
                  encode,
                  _decode_selective,
                  _dict_to_bson,
                  _make_c_string)
from bson.codec_options import DEFAULT_CODEC_OPTIONS
from bson.int64 import Int64
from bson.raw_bson import (_inflate_bson, DEFAULT_RAW_BSON_OPTIONS,
                           RawBSONDocument)
from bson.py3compat import b, StringIO
from bson.son import SON

try:
    from pymongo import _cmessage
    _use_c = True
except ImportError:
    _use_c = False
from pymongo.errors import (ConfigurationError,
                            CursorNotFound,
                            DocumentTooLarge,
                            ExecutionTimeout,
                            InvalidOperation,
                            NotPrimaryError,
                            OperationFailure,
                            ProtocolError)
from pymongo.hello_compat import HelloCompat
from pymongo.read_concern import DEFAULT_READ_CONCERN
from pymongo.read_preferences import ReadPreference
from pymongo.write_concern import WriteConcern


MAX_INT32 = 2147483647
MIN_INT32 = -2147483648

# Overhead allowed for encoded command documents.
_COMMAND_OVERHEAD = 16382

_INSERT = 0
_UPDATE = 1
_DELETE = 2

_EMPTY   = b''
_BSONOBJ = b'\x03'
_ZERO_8  = b'\x00'
_ZERO_16 = b'\x00\x00'
_ZERO_32 = b'\x00\x00\x00\x00'
_ZERO_64 = b'\x00\x00\x00\x00\x00\x00\x00\x00'
_SKIPLIM = b'\x00\x00\x00\x00\xff\xff\xff\xff'
_OP_MAP = {
    _INSERT: b'\x04documents\x00\x00\x00\x00\x00',
    _UPDATE: b'\x04updates\x00\x00\x00\x00\x00',
    _DELETE: b'\x04deletes\x00\x00\x00\x00\x00',
}
_FIELD_MAP = {
    'insert': 'documents',
    'update': 'updates',
    'delete': 'deletes'
}

_UJOIN = u"%s.%s"

_UNICODE_REPLACE_CODEC_OPTIONS = CodecOptions(
    unicode_decode_error_handler='replace')


def _randint():
    """Generate a pseudo random 32 bit integer."""
    return random.randint(MIN_INT32, MAX_INT32)


def _maybe_add_read_preference(spec, read_preference):
    """Add $readPreference to spec when appropriate."""
    mode = read_preference.mode
    document = read_preference.document
    # Only add $readPreference if it's something other than primary to avoid
    # problems with mongos versions that don't support read preferences. Also,
    # for maximum backwards compatibility, don't add $readPreference for
    # secondaryPreferred unless tags or maxStalenessSeconds are in use (setting
    # the secondaryOkay bit has the same effect).
    if mode and (
            mode != ReadPreference.SECONDARY_PREFERRED.mode or
            len(document) > 1):
        if "$query" not in spec:
            spec = SON([("$query", spec)])
        spec["$readPreference"] = document
    return spec


def _convert_exception(exception):
    """Convert an Exception into a failure document for publishing."""
    return {'errmsg': str(exception),
            'errtype': exception.__class__.__name__}


def _convert_write_result(operation, command, result):
    """Convert a legacy write result to write command format."""

    # Based on _merge_legacy from bulk.py
    affected = result.get("n", 0)
    res = {"ok": 1, "n": affected}
    errmsg = result.get("errmsg", result.get("err", ""))
    if errmsg:
        # The write was successful on at least the primary so don't return.
        if result.get("wtimeout"):
            res["writeConcernError"] = {"errmsg": errmsg,
                                        "code": 64,
                                        "errInfo": {"wtimeout": True}}
        else:
            # The write failed.
            error = {"index": 0,
                     "code": result.get("code", 8),
                     "errmsg": errmsg}
            if "errInfo" in result:
                error["errInfo"] = result["errInfo"]
            res["writeErrors"] = [error]
            return res
    if operation == "insert":
        # GLE result for insert is always 0 in most MongoDB versions.
        res["n"] = len(command['documents'])
    elif operation == "update":
        if "upserted" in result:
            res["upserted"] = [{"index": 0, "_id": result["upserted"]}]
        # Versions of MongoDB before 2.6 don't return the _id for an
        # upsert if _id is not an ObjectId.
        elif result.get("updatedExisting") is False and affected == 1:
            # If _id is in both the update document *and* the query spec
            # the update document _id takes precedence.
            update = command['updates'][0]
            _id = update["u"].get("_id", update["q"].get("_id"))
            res["upserted"] = [{"index": 0, "_id": _id}]
    return res


_OPTIONS = SON([
    ('tailable', 2),
    ('oplogReplay', 8),
    ('noCursorTimeout', 16),
    ('awaitData', 32),
    ('allowPartialResults', 128)])


_MODIFIERS = SON([
    ('$query', 'filter'),
    ('$orderby', 'sort'),
    ('$hint', 'hint'),
    ('$comment', 'comment'),
    ('$maxScan', 'maxScan'),
    ('$maxTimeMS', 'maxTimeMS'),
    ('$max', 'max'),
    ('$min', 'min'),
    ('$returnKey', 'returnKey'),
    ('$showRecordId', 'showRecordId'),
    ('$showDiskLoc', 'showRecordId'),  # <= MongoDb 3.0
    ('$snapshot', 'snapshot')])


def _gen_find_command(coll, spec, projection, skip, limit, batch_size, options,
                      read_concern, collation=None, session=None,
                      allow_disk_use=None):
    """Generate a find command document."""
    cmd = SON([('find', coll)])
    if '$query' in spec:
        cmd.update([(_MODIFIERS[key], val) if key in _MODIFIERS else (key, val)
                    for key, val in spec.items()])
        if '$explain' in cmd:
            cmd.pop('$explain')
        if '$readPreference' in cmd:
            cmd.pop('$readPreference')
    else:
        cmd['filter'] = spec

    if projection:
        cmd['projection'] = projection
    if skip:
        cmd['skip'] = skip
    if limit:
        cmd['limit'] = abs(limit)
        if limit < 0:
            cmd['singleBatch'] = True
    if batch_size:
        cmd['batchSize'] = batch_size
    if read_concern.level and not (session and session.in_transaction):
        cmd['readConcern'] = read_concern.document
    if collation:
        cmd['collation'] = collation
    if allow_disk_use is not None:
        cmd['allowDiskUse'] = allow_disk_use
    if options:
        cmd.update([(opt, True)
                    for opt, val in _OPTIONS.items()
                    if options & val])

    return cmd


def _gen_get_more_command(cursor_id, coll, batch_size, max_await_time_ms):
    """Generate a getMore command document."""
    cmd = SON([('getMore', cursor_id),
               ('collection', coll)])
    if batch_size:
        cmd['batchSize'] = batch_size
    if max_await_time_ms is not None:
        cmd['maxTimeMS'] = max_await_time_ms
    return cmd


class _Query(object):
    """A query operation."""

    __slots__ = ('flags', 'db', 'coll', 'ntoskip', 'spec',
                 'fields', 'codec_options', 'read_preference', 'limit',
                 'batch_size', 'name', 'read_concern', 'collation',
                 'session', 'client', 'allow_disk_use', '_as_command',
                 'exhaust')

    # For compatibility with the _GetMore class.
    sock_mgr = None
    cursor_id = None

    def __init__(self, flags, db, coll, ntoskip, spec, fields,
                 codec_options, read_preference, limit,
                 batch_size, read_concern, collation, session, client,
                 allow_disk_use, exhaust):
        self.flags = flags
        self.db = db
        self.coll = coll
        self.ntoskip = ntoskip
        self.spec = spec
        self.fields = fields
        self.codec_options = codec_options
        self.read_preference = read_preference
        self.read_concern = read_concern
        self.limit = limit
        self.batch_size = batch_size
        self.collation = collation
        self.session = session
        self.client = client
        self.allow_disk_use = allow_disk_use
        self.name = 'find'
        self._as_command = None
        self.exhaust = exhaust

    def namespace(self):
        return _UJOIN % (self.db, self.coll)

    def use_command(self, sock_info):
        use_find_cmd = False
        if sock_info.max_wire_version >= 4 and not self.exhaust:
            use_find_cmd = True
        elif sock_info.max_wire_version >= 8:
            # OP_MSG supports exhaust on MongoDB 4.2+
            use_find_cmd = True
        elif not self.read_concern.ok_for_legacy:
            raise ConfigurationError(
                'read concern level of %s is not valid '
                'with a max wire version of %d.'
                % (self.read_concern.level,
                   sock_info.max_wire_version))

        if sock_info.max_wire_version < 5 and self.collation is not None:
            raise ConfigurationError(
                'Specifying a collation is unsupported with a max wire '
                'version of %d.' % (sock_info.max_wire_version,))

        if sock_info.max_wire_version < 4 and self.allow_disk_use is not None:
            raise ConfigurationError(
                'Specifying allowDiskUse is unsupported with a max wire '
                'version of %d.' % (sock_info.max_wire_version,))

        sock_info.validate_session(self.client, self.session)

        return use_find_cmd

    def as_command(self, sock_info):
        """Return a find command document for this query."""
        # We use the command twice: on the wire and for command monitoring.
        # Generate it once, for speed and to avoid repeating side-effects.
        if self._as_command is not None:
            return self._as_command

        explain = '$explain' in self.spec
        cmd = _gen_find_command(
            self.coll, self.spec, self.fields, self.ntoskip,
            self.limit, self.batch_size, self.flags, self.read_concern,
            self.collation, self.session, self.allow_disk_use)
        if explain:
            self.name = 'explain'
            cmd = SON([('explain', cmd)])
        session = self.session
        sock_info.add_server_api(cmd)
        if session:
            session._apply_to(cmd, False, self.read_preference, sock_info)
            # Explain does not support readConcern.
            if not explain and not session.in_transaction:
                session._update_read_concern(cmd, sock_info)
        sock_info.send_cluster_time(cmd, session, self.client)
        # Support auto encryption
        client = self.client
        if (client._encrypter and
                not client._encrypter._bypass_auto_encryption):
            cmd = client._encrypter.encrypt(
                self.db, cmd, False, self.codec_options)
        self._as_command = cmd, self.db
        return self._as_command

    def get_message(self, set_secondary_ok, sock_info, use_cmd=False):
        """Get a query message, possibly setting the secondaryOk bit."""
        if set_secondary_ok:
            # Set the secondaryOk bit.
            flags = self.flags | 4
        else:
            flags = self.flags

        ns = self.namespace()
        spec = self.spec

        if use_cmd:
            spec = self.as_command(sock_info)[0]
            if sock_info.op_msg_enabled:
                request_id, msg, size, _ = _op_msg(
                    0, spec, self.db, self.read_preference,
                    set_secondary_ok, False, self.codec_options,
                    ctx=sock_info.compression_context)
                return request_id, msg, size
            ns = _UJOIN % (self.db, "$cmd")
            ntoreturn = -1  # All DB commands return 1 document
        else:
            # OP_QUERY treats ntoreturn of -1 and 1 the same, return
            # one document and close the cursor. We have to use 2 for
            # batch size if 1 is specified.
            ntoreturn = self.batch_size == 1 and 2 or self.batch_size
            if self.limit:
                if ntoreturn:
                    ntoreturn = min(self.limit, ntoreturn)
                else:
                    ntoreturn = self.limit

        if sock_info.is_mongos:
            spec = _maybe_add_read_preference(spec,
                                              self.read_preference)

        return query(flags, ns, self.ntoskip, ntoreturn,
                     spec, None if use_cmd else self.fields,
                     self.codec_options, ctx=sock_info.compression_context)


class _GetMore(object):
    """A getmore operation."""

    __slots__ = ('db', 'coll', 'ntoreturn', 'cursor_id', 'max_await_time_ms',
                 'codec_options', 'read_preference', 'session', 'client',
                 'sock_mgr', '_as_command', 'exhaust')

    name = 'getMore'

    def __init__(self, db, coll, ntoreturn, cursor_id, codec_options,
                 read_preference, session, client, max_await_time_ms,
                 sock_mgr, exhaust):
        self.db = db
        self.coll = coll
        self.ntoreturn = ntoreturn
        self.cursor_id = cursor_id
        self.codec_options = codec_options
        self.read_preference = read_preference
        self.session = session
        self.client = client
        self.max_await_time_ms = max_await_time_ms
        self.sock_mgr = sock_mgr
        self._as_command = None
        self.exhaust = exhaust

    def namespace(self):
        return _UJOIN % (self.db, self.coll)

    def use_command(self, sock_info):
        use_cmd = False
        if sock_info.max_wire_version >= 4 and not self.exhaust:
            use_cmd = True
        elif sock_info.max_wire_version >= 8:
            # OP_MSG supports exhaust on MongoDB 4.2+
            use_cmd = True

        sock_info.validate_session(self.client, self.session)
        return use_cmd

    def as_command(self, sock_info):
        """Return a getMore command document for this query."""
        # See _Query.as_command for an explanation of this caching.
        if self._as_command is not None:
            return self._as_command

        cmd = _gen_get_more_command(self.cursor_id, self.coll,
                                    self.ntoreturn,
                                    self.max_await_time_ms)

        if self.session:
            self.session._apply_to(cmd, False, self.read_preference, sock_info)
        sock_info.add_server_api(cmd)
        sock_info.send_cluster_time(cmd, self.session, self.client)
        # Support auto encryption
        client = self.client
        if (client._encrypter and
                not client._encrypter._bypass_auto_encryption):
            cmd = client._encrypter.encrypt(
                self.db, cmd, False, self.codec_options)
        self._as_command = cmd, self.db
        return self._as_command

    def get_message(self, dummy0, sock_info, use_cmd=False):
        """Get a getmore message."""

        ns = self.namespace()
        ctx = sock_info.compression_context

        if use_cmd:
            spec = self.as_command(sock_info)[0]
            if sock_info.op_msg_enabled:
                if self.sock_mgr:
                    flags = _OpMsg.EXHAUST_ALLOWED
                else:
                    flags = 0
                request_id, msg, size, _ = _op_msg(
                    flags, spec, self.db, None,
                    False, False, self.codec_options,
                    ctx=sock_info.compression_context)
                return request_id, msg, size
            ns = _UJOIN % (self.db, "$cmd")
            return query(0, ns, 0, -1, spec, None, self.codec_options, ctx=ctx)

        return get_more(ns, self.ntoreturn, self.cursor_id, ctx)


class _RawBatchQuery(_Query):
    def use_command(self, sock_info):
        # Compatibility checks.
        super(_RawBatchQuery, self).use_command(sock_info)
        if sock_info.max_wire_version >= 8:
            # MongoDB 4.2+ supports exhaust over OP_MSG
            return True
        elif sock_info.op_msg_enabled and not self.exhaust:
            return True
        return False


class _RawBatchGetMore(_GetMore):
    def use_command(self, sock_info):
        # Compatibility checks.
        super(_RawBatchGetMore, self).use_command(sock_info)
        if sock_info.max_wire_version >= 8:
            # MongoDB 4.2+ supports exhaust over OP_MSG
            return True
        elif sock_info.op_msg_enabled and not self.exhaust:
            return True
        return False


class _CursorAddress(tuple):
    """The server address (host, port) of a cursor, with namespace property."""

    def __new__(cls, address, namespace):
        self = tuple.__new__(cls, address)
        self.__namespace = namespace
        return self

    @property
    def namespace(self):
        """The namespace this cursor."""
        return self.__namespace

    def __hash__(self):
        # Two _CursorAddress instances with different namespaces
        # must not hash the same.
        return (self + (self.__namespace,)).__hash__()

    def __eq__(self, other):
        if isinstance(other, _CursorAddress):
            return (tuple(self) == tuple(other)
                    and self.namespace == other.namespace)
        return NotImplemented

    def __ne__(self, other):
        return not self == other


_pack_compression_header = struct.Struct("<iiiiiiB").pack
_COMPRESSION_HEADER_SIZE = 25

def _compress(operation, data, ctx):
    """Takes message data, compresses it, and adds an OP_COMPRESSED header."""
    compressed = ctx.compress(data)
    request_id = _randint()

    header = _pack_compression_header(
        _COMPRESSION_HEADER_SIZE + len(compressed), # Total message length
        request_id, # Request id
        0, # responseTo
        2012, # operation id
        operation, # original operation id
        len(data), # uncompressed message length
        ctx.compressor_id) # compressor id
    return request_id, header + compressed


def __last_error(namespace, args):
    """Data to send to do a lastError.
    """
    cmd = SON([("getlasterror", 1)])
    cmd.update(args)
    splitns = namespace.split('.', 1)
    return query(0, splitns[0] + '.$cmd', 0, -1, cmd,
                 None, DEFAULT_CODEC_OPTIONS)


_pack_header = struct.Struct("<iiii").pack


def __pack_message(operation, data):
    """Takes message data and adds a message header based on the operation.

    Returns the resultant message string.
    """
    rid = _randint()
    message = _pack_header(16 + len(data), rid, 0, operation)
    return rid, message + data


_pack_int = struct.Struct("<i").pack


def _insert(collection_name, docs, check_keys, flags, opts):
    """Get an OP_INSERT message"""
    encode = _dict_to_bson  # Make local. Uses extensions.
    if len(docs) == 1:
        encoded = encode(docs[0], check_keys, opts)
        return b"".join([
            b"\x00\x00\x00\x00",  # Flags don't matter for one doc.
            _make_c_string(collection_name),
            encoded]), len(encoded)

    encoded = [encode(doc, check_keys, opts) for doc in docs]
    if not encoded:
        raise InvalidOperation("cannot do an empty bulk insert")
    return b"".join([
        _pack_int(flags),
        _make_c_string(collection_name),
        b"".join(encoded)]), max(map(len, encoded))


def _insert_compressed(
        collection_name, docs, check_keys, continue_on_error, opts, ctx):
    """Internal compressed unacknowledged insert message helper."""
    op_insert, max_bson_size = _insert(
        collection_name, docs, check_keys, continue_on_error, opts)
    rid, msg = _compress(2002, op_insert, ctx)
    return rid, msg, max_bson_size


def _insert_uncompressed(collection_name, docs, check_keys,
            safe, last_error_args, continue_on_error, opts):
    """Internal insert message helper."""
    op_insert, max_bson_size = _insert(
        collection_name, docs, check_keys, continue_on_error, opts)
    rid, msg = __pack_message(2002, op_insert)
    if safe:
        rid, gle, _ = __last_error(collection_name, last_error_args)
        return rid, msg + gle, max_bson_size
    return rid, msg, max_bson_size
if _use_c:
    _insert_uncompressed = _cmessage._insert_message


def insert(collection_name, docs, check_keys,
           safe, last_error_args, continue_on_error, opts, ctx=None):
    """**DEPRECATED** Get an **insert** message.

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    if ctx:
        return _insert_compressed(
            collection_name, docs, check_keys, continue_on_error, opts, ctx)
    return _insert_uncompressed(collection_name, docs, check_keys, safe,
                                last_error_args, continue_on_error, opts)


def _update(collection_name, upsert, multi, spec, doc, check_keys, opts):
    """Get an OP_UPDATE message."""
    flags = 0
    if upsert:
        flags += 1
    if multi:
        flags += 2
    encode = _dict_to_bson  # Make local. Uses extensions.
    encoded_update = encode(doc, check_keys, opts)
    return b"".join([
        _ZERO_32,
        _make_c_string(collection_name),
        _pack_int(flags),
        encode(spec, False, opts),
        encoded_update]), len(encoded_update)


def _update_compressed(
        collection_name, upsert, multi, spec, doc, check_keys, opts, ctx):
    """Internal compressed unacknowledged update message helper."""
    op_update, max_bson_size = _update(
        collection_name, upsert, multi, spec, doc, check_keys, opts)
    rid, msg = _compress(2001, op_update, ctx)
    return rid, msg, max_bson_size


def _update_uncompressed(collection_name, upsert, multi, spec,
                         doc, safe, last_error_args, check_keys, opts):
    """Internal update message helper."""
    op_update, max_bson_size = _update(
        collection_name, upsert, multi, spec, doc, check_keys, opts)
    rid, msg = __pack_message(2001, op_update)
    if safe:
        rid, gle, _ = __last_error(collection_name, last_error_args)
        return rid, msg + gle, max_bson_size
    return rid, msg, max_bson_size
if _use_c:
    _update_uncompressed = _cmessage._update_message


def update(collection_name, upsert, multi, spec,
           doc, safe, last_error_args, check_keys, opts, ctx=None):
    """**DEPRECATED** Get an **update** message.

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    if ctx:
        return _update_compressed(
            collection_name, upsert, multi, spec, doc, check_keys, opts, ctx)
    return _update_uncompressed(collection_name, upsert, multi, spec,
                                doc, safe, last_error_args, check_keys, opts)


_pack_op_msg_flags_type = struct.Struct("<IB").pack
_pack_byte = struct.Struct("<B").pack


def _op_msg_no_header(flags, command, identifier, docs, check_keys, opts):
    """Get a OP_MSG message.

    Note: this method handles multiple documents in a type one payload but
    it does not perform batch splitting and the total message size is
    only checked *after* generating the entire message.
    """
    # Encode the command document in payload 0 without checking keys.
    encoded = _dict_to_bson(command, False, opts)
    flags_type = _pack_op_msg_flags_type(flags, 0)
    total_size = len(encoded)
    max_doc_size = 0
    if identifier:
        type_one = _pack_byte(1)
        cstring = _make_c_string(identifier)
        encoded_docs = [_dict_to_bson(doc, check_keys, opts) for doc in docs]
        size = len(cstring) + sum(len(doc) for doc in encoded_docs) + 4
        encoded_size = _pack_int(size)
        total_size += size
        max_doc_size = max(len(doc) for doc in encoded_docs)
        data = ([flags_type, encoded, type_one, encoded_size, cstring] +
                encoded_docs)
    else:
        data = [flags_type, encoded]
    return b''.join(data), total_size, max_doc_size


def _op_msg_compressed(flags, command, identifier, docs, check_keys, opts,
                       ctx):
    """Internal OP_MSG message helper."""
    msg, total_size, max_bson_size = _op_msg_no_header(
        flags, command, identifier, docs, check_keys, opts)
    rid, msg = _compress(2013, msg, ctx)
    return rid, msg, total_size, max_bson_size


def _op_msg_uncompressed(flags, command, identifier, docs, check_keys, opts):
    """Internal compressed OP_MSG message helper."""
    data, total_size, max_bson_size = _op_msg_no_header(
        flags, command, identifier, docs, check_keys, opts)
    request_id, op_message = __pack_message(2013, data)
    return request_id, op_message, total_size, max_bson_size
if _use_c:
    _op_msg_uncompressed = _cmessage._op_msg


def _op_msg(flags, command, dbname, read_preference, secondary_ok, check_keys,
            opts, ctx=None):
    """Get a OP_MSG message."""
    command['$db'] = dbname
    # getMore commands do not send $readPreference.
    if read_preference is not None and "$readPreference" not in command:
        if secondary_ok and not read_preference.mode:
            command["$readPreference"] = (
                ReadPreference.PRIMARY_PREFERRED.document)
        else:
            command["$readPreference"] = read_preference.document
    name = next(iter(command))
    try:
        identifier = _FIELD_MAP.get(name)
        docs = command.pop(identifier)
    except KeyError:
        identifier = ""
        docs = None
    try:
        if ctx:
            return _op_msg_compressed(
                flags, command, identifier, docs, check_keys, opts, ctx)
        return _op_msg_uncompressed(
            flags, command, identifier, docs, check_keys, opts)
    finally:
        # Add the field back to the command.
        if identifier:
            command[identifier] = docs


def _query(options, collection_name, num_to_skip,
           num_to_return, query, field_selector, opts, check_keys):
    """Get an OP_QUERY message."""
    encoded = _dict_to_bson(query, check_keys, opts)
    if field_selector:
        efs = _dict_to_bson(field_selector, False, opts)
    else:
        efs = b""
    max_bson_size = max(len(encoded), len(efs))
    return b"".join([
        _pack_int(options),
        _make_c_string(collection_name),
        _pack_int(num_to_skip),
        _pack_int(num_to_return),
        encoded,
        efs]), max_bson_size


def _query_compressed(options, collection_name, num_to_skip,
                      num_to_return, query, field_selector,
                      opts, check_keys=False, ctx=None):
    """Internal compressed query message helper."""
    op_query, max_bson_size = _query(
        options,
        collection_name,
        num_to_skip,
        num_to_return,
        query,
        field_selector,
        opts,
        check_keys)
    rid, msg = _compress(2004, op_query, ctx)
    return rid, msg, max_bson_size


def _query_uncompressed(options, collection_name, num_to_skip,
          num_to_return, query, field_selector, opts, check_keys=False):
    """Internal query message helper."""
    op_query, max_bson_size = _query(
        options,
        collection_name,
        num_to_skip,
        num_to_return,
        query,
        field_selector,
        opts,
        check_keys)
    rid, msg = __pack_message(2004, op_query)
    return rid, msg, max_bson_size
if _use_c:
    _query_uncompressed = _cmessage._query_message


def query(options, collection_name, num_to_skip, num_to_return,
          query, field_selector, opts, check_keys=False, ctx=None):
    """**DEPRECATED** Get a **query** message.

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    if ctx:
        return _query_compressed(options, collection_name, num_to_skip,
                                 num_to_return, query, field_selector,
                                 opts, check_keys, ctx)
    return _query_uncompressed(options, collection_name, num_to_skip,
                               num_to_return, query, field_selector, opts,
                               check_keys)


_pack_long_long = struct.Struct("<q").pack


def _get_more(collection_name, num_to_return, cursor_id):
    """Get an OP_GET_MORE message."""
    return b"".join([
        _ZERO_32,
        _make_c_string(collection_name),
        _pack_int(num_to_return),
        _pack_long_long(cursor_id)])


def _get_more_compressed(collection_name, num_to_return, cursor_id, ctx):
    """Internal compressed getMore message helper."""
    return _compress(
        2005, _get_more(collection_name, num_to_return, cursor_id), ctx)


def _get_more_uncompressed(collection_name, num_to_return, cursor_id):
    """Internal getMore message helper."""
    return __pack_message(
        2005, _get_more(collection_name, num_to_return, cursor_id))
if _use_c:
    _get_more_uncompressed = _cmessage._get_more_message


def get_more(collection_name, num_to_return, cursor_id, ctx=None):
    """**DEPRECATED** Get a **getMore** message.

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    if ctx:
        return _get_more_compressed(
            collection_name, num_to_return, cursor_id, ctx)
    return _get_more_uncompressed(collection_name, num_to_return, cursor_id)


def _delete(collection_name, spec, opts, flags):
    """Get an OP_DELETE message."""
    encoded = _dict_to_bson(spec, False, opts)  # Uses extensions.
    return b"".join([
        _ZERO_32,
        _make_c_string(collection_name),
        _pack_int(flags),
        encoded]), len(encoded)


def _delete_compressed(collection_name, spec, opts, flags, ctx):
    """Internal compressed unacknowledged delete message helper."""
    op_delete, max_bson_size = _delete(collection_name, spec, opts, flags)
    rid, msg = _compress(2006, op_delete, ctx)
    return rid, msg, max_bson_size


def _delete_uncompressed(
        collection_name, spec, safe, last_error_args, opts, flags=0):
    """Internal delete message helper."""
    op_delete, max_bson_size = _delete(collection_name, spec, opts, flags)
    rid, msg = __pack_message(2006, op_delete)
    if safe:
        rid, gle, _ = __last_error(collection_name, last_error_args)
        return rid, msg + gle, max_bson_size
    return rid, msg, max_bson_size


def delete(
        collection_name, spec, safe, last_error_args, opts, flags=0, ctx=None):
    """**DEPRECATED** Get a **delete** message.

    `opts` is a CodecOptions. `flags` is a bit vector that may contain
    the SingleRemove flag or not:

    http://docs.mongodb.org/meta-driver/latest/legacy/mongodb-wire-protocol/#op-delete

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    if ctx:
        return _delete_compressed(collection_name, spec, opts, flags, ctx)
    return _delete_uncompressed(
        collection_name, spec, safe, last_error_args, opts, flags)


def kill_cursors(cursor_ids):
    """**DEPRECATED** Get a **killCursors** message.

    .. versionchanged:: 3.12
      This function is deprecated and will be removed in PyMongo 4.0.
    """
    num_cursors = len(cursor_ids)
    pack = struct.Struct("<ii" + ("q" * num_cursors)).pack
    op_kill_cursors = pack(0, num_cursors, *cursor_ids)
    return __pack_message(2007, op_kill_cursors)


class _BulkWriteContext(object):
    """A wrapper around SocketInfo for use with write splitting functions."""

    __slots__ = ('db_name', 'sock_info', 'op_id',
                 'name', 'field', 'publish', 'start_time', 'listeners',
                 'session', 'compress', 'op_type', 'codec', 'cmd_legacy')

    def __init__(self, database_name, cmd_name, sock_info, operation_id,
                 listeners, session, op_type, codec, cmd_legacy=None):
        self.db_name = database_name
        self.sock_info = sock_info
        self.op_id = operation_id
        self.listeners = listeners
        self.publish = listeners.enabled_for_commands
        self.name = cmd_name
        self.field = _FIELD_MAP[self.name]
        self.start_time = datetime.datetime.now() if self.publish else None
        self.session = session
        self.compress = True if sock_info.compression_context else False
        self.op_type = op_type
        self.codec = codec
        self.cmd_legacy = cmd_legacy

    def _batch_command(self, cmd, docs):
        namespace = self.db_name + '.$cmd'
        request_id, msg, to_send = _do_bulk_write_command(
            namespace, self.op_type, cmd, docs, self.check_keys,
            self.codec, self)
        if not to_send:
            raise InvalidOperation("cannot do an empty bulk write")
        return request_id, msg, to_send

    def execute(self, cmd, docs, client):
        request_id, msg, to_send = self._batch_command(cmd, docs)
        result = self.write_command(cmd, request_id, msg, to_send)
        client._process_response(result, self.session)
        return result, to_send

    def execute_unack(self, cmd, docs, client):
        request_id, msg, to_send = self._batch_command(cmd, docs)
        # Though this isn't strictly a "legacy" write, the helper
        # handles publishing commands and sending our message
        # without receiving a result. Send 0 for max_doc_size
        # to disable size checking. Size checking is handled while
        # the documents are encoded to BSON.
        self.legacy_write(cmd, request_id, msg, 0, False, to_send)
        return to_send

    @property
    def check_keys(self):
        """Should we check keys for this operation type?"""
        return False

    @property
    def max_bson_size(self):
        """A proxy for SockInfo.max_bson_size."""
        return self.sock_info.max_bson_size

    @property
    def max_message_size(self):
        """A proxy for SockInfo.max_message_size."""
        if self.compress:
            # Subtract 16 bytes for the message header.
            return self.sock_info.max_message_size - 16
        return self.sock_info.max_message_size

    @property
    def max_write_batch_size(self):
        """A proxy for SockInfo.max_write_batch_size."""
        return self.sock_info.max_write_batch_size

    @property
    def max_split_size(self):
        """The maximum size of a BSON command before batch splitting."""
        return self.max_bson_size

    def legacy_bulk_insert(
            self, request_id, msg, max_doc_size, acknowledged, docs, compress):
        if compress:
            request_id, msg = _compress(
                2002, msg, self.sock_info.compression_context)
        return self.legacy_write(
            self.cmd_legacy.copy(), request_id, msg, max_doc_size,
            acknowledged, docs)

    def legacy_write(self, cmd, request_id, msg, max_doc_size, acknowledged,
                     docs):
        """A proxy for SocketInfo.legacy_write that handles event publishing.
        """
        if self.publish:
            duration = datetime.datetime.now() - self.start_time
            cmd = self._start(cmd, request_id, docs)
            start = datetime.datetime.now()
        try:
            result = self.sock_info.legacy_write(
                request_id, msg, max_doc_size, acknowledged)
            if self.publish:
                duration = (datetime.datetime.now() - start) + duration
                if result is not None:
                    reply = _convert_write_result(self.name, cmd, result)
                else:
                    # Comply with APM spec.
                    reply = {'ok': 1}
                self._succeed(request_id, reply, duration)
        except Exception as exc:
            if self.publish:
                duration = (datetime.datetime.now() - start) + duration
                if isinstance(exc, OperationFailure):
                    failure = _convert_write_result(
                        self.name, cmd, exc.details)
                elif isinstance(exc, NotPrimaryError):
                    failure = exc.details
                else:
                    failure = _convert_exception(exc)
                self._fail(request_id, failure, duration)
            raise
        finally:
            self.start_time = datetime.datetime.now()
        return result

    def write_command(self, cmd, request_id, msg, docs):
        """A proxy for SocketInfo.write_command that handles event publishing.
        """
        if self.publish:
            duration = datetime.datetime.now() - self.start_time
            self._start(cmd, request_id, docs)
            start = datetime.datetime.now()
        try:
            reply = self.sock_info.write_command(request_id, msg)
            if self.publish:
                duration = (datetime.datetime.now() - start) + duration
                self._succeed(request_id, reply, duration)
        except Exception as exc:
            if self.publish:
                duration = (datetime.datetime.now() - start) + duration
                if isinstance(exc, (NotPrimaryError, OperationFailure)):
                    failure = exc.details
                else:
                    failure = _convert_exception(exc)
                self._fail(request_id, failure, duration)
            raise
        finally:
            self.start_time = datetime.datetime.now()
        return reply

    def _start(self, cmd, request_id, docs):
        """Publish a CommandStartedEvent."""
        cmd[self.field] = docs
        self.listeners.publish_command_start(
            cmd, self.db_name,
            request_id, self.sock_info.address, self.op_id,
            self.sock_info.service_id)
        return cmd

    def _succeed(self, request_id, reply, duration):
        """Publish a CommandSucceededEvent."""
        self.listeners.publish_command_success(
            duration, reply, self.name,
            request_id, self.sock_info.address, self.op_id,
            self.sock_info.service_id)

    def _fail(self, request_id, failure, duration):
        """Publish a CommandFailedEvent."""
        self.listeners.publish_command_failure(
            duration, failure, self.name,
            request_id, self.sock_info.address, self.op_id,
            self.sock_info.service_id)


# From the Client Side Encryption spec:
# Because automatic encryption increases the size of commands, the driver
# MUST split bulk writes at a reduced size limit before undergoing automatic
# encryption. The write payload MUST be split at 2MiB (2097152).
_MAX_SPLIT_SIZE_ENC = 2097152


class _EncryptedBulkWriteContext(_BulkWriteContext):
    __slots__ = ()

    def _batch_command(self, cmd, docs):
        namespace = self.db_name + '.$cmd'
        msg, to_send = _encode_batched_write_command(
            namespace, self.op_type, cmd, docs, self.check_keys,
            self.codec, self)
        if not to_send:
            raise InvalidOperation("cannot do an empty bulk write")

        # Chop off the OP_QUERY header to get a properly batched write command.
        cmd_start = msg.index(b"\x00", 4) + 9
        cmd = _inflate_bson(memoryview(msg)[cmd_start:],
                            DEFAULT_RAW_BSON_OPTIONS)
        return cmd, to_send

    def execute(self, cmd, docs, client):
        batched_cmd, to_send = self._batch_command(cmd, docs)
        result = self.sock_info.command(
            self.db_name, batched_cmd,
            codec_options=_UNICODE_REPLACE_CODEC_OPTIONS,
            session=self.session, client=client)
        return result, to_send

    def execute_unack(self, cmd, docs, client):
        batched_cmd, to_send = self._batch_command(cmd, docs)
        self.sock_info.command(
            self.db_name, batched_cmd, write_concern=WriteConcern(w=0),
            session=self.session, client=client)
        return to_send

    @property
    def max_split_size(self):
        """Reduce the batch splitting size."""
        return _MAX_SPLIT_SIZE_ENC


def _raise_document_too_large(operation, doc_size, max_size):
    """Internal helper for raising DocumentTooLarge."""
    if operation == "insert":
        raise DocumentTooLarge("BSON document too large (%d bytes)"
                               " - the connected server supports"
                               " BSON document sizes up to %d"
                               " bytes." % (doc_size, max_size))
    else:
        # There's nothing intelligent we can say
        # about size for update and delete
        raise DocumentTooLarge("%r command document too large" % (operation,))


def _do_batched_insert(collection_name, docs, check_keys,
                       safe, last_error_args, continue_on_error, opts,
                       ctx):
    """Insert `docs` using multiple batches.
    """
    def _insert_message(insert_message, send_safe):
        """Build the insert message with header and GLE.
        """
        request_id, final_message = __pack_message(2002, insert_message)
        if send_safe:
            request_id, error_message, _ = __last_error(collection_name,
                                                        last_error_args)
            final_message += error_message
        return request_id, final_message

    send_safe = safe or not continue_on_error
    last_error = None
    data = StringIO()
    data.write(struct.pack("<i", int(continue_on_error)))
    data.write(_make_c_string(collection_name))
    message_length = begin_loc = data.tell()
    has_docs = False
    to_send = []
    encode = _dict_to_bson  # Make local
    compress = ctx.compress and not (safe or send_safe)
    for doc in docs:
        encoded = encode(doc, check_keys, opts)
        encoded_length = len(encoded)
        too_large = (encoded_length > ctx.max_bson_size)

        message_length += encoded_length
        if message_length < ctx.max_message_size and not too_large:
            data.write(encoded)
            to_send.append(doc)
            has_docs = True
            continue

        if has_docs:
            # We have enough data, send this message.
            try:
                if compress:
                    rid, msg = None, data.getvalue()
                else:
                    rid, msg = _insert_message(data.getvalue(), send_safe)
                ctx.legacy_bulk_insert(
                    rid, msg, 0, send_safe, to_send, compress)
            # Exception type could be OperationFailure or a subtype
            # (e.g. DuplicateKeyError)
            except OperationFailure as exc:
                # Like it says, continue on error...
                if continue_on_error:
                    # Store exception details to re-raise after the final batch.
                    last_error = exc
                # With unacknowledged writes just return at the first error.
                elif not safe:
                    return
                # With acknowledged writes raise immediately.
                else:
                    raise

        if too_large:
            _raise_document_too_large(
                "insert", encoded_length, ctx.max_bson_size)

        message_length = begin_loc + encoded_length
        data.seek(begin_loc)
        data.truncate()
        data.write(encoded)
        to_send = [doc]

    if not has_docs:
        raise InvalidOperation("cannot do an empty bulk insert")

    if compress:
        request_id, msg = None, data.getvalue()
    else:
        request_id, msg = _insert_message(data.getvalue(), safe)
    ctx.legacy_bulk_insert(request_id, msg, 0, safe, to_send, compress)

    # Re-raise any exception stored due to continue_on_error
    if last_error is not None:
        raise last_error
if _use_c:
    _do_batched_insert = _cmessage._do_batched_insert

# OP_MSG -------------------------------------------------------------


_OP_MSG_MAP = {
    _INSERT: b'documents\x00',
    _UPDATE: b'updates\x00',
    _DELETE: b'deletes\x00',
}


def _batched_op_msg_impl(
        operation, command, docs, check_keys, ack, opts, ctx, buf):
    """Create a batched OP_MSG write."""
    max_bson_size = ctx.max_bson_size
    max_write_batch_size = ctx.max_write_batch_size
    max_message_size = ctx.max_message_size

    flags = b"\x00\x00\x00\x00" if ack else b"\x02\x00\x00\x00"
    # Flags
    buf.write(flags)

    # Type 0 Section
    buf.write(b"\x00")
    buf.write(_dict_to_bson(command, False, opts))

    # Type 1 Section
    buf.write(b"\x01")
    size_location = buf.tell()
    # Save space for size
    buf.write(b"\x00\x00\x00\x00")
    try:
        buf.write(_OP_MSG_MAP[operation])
    except KeyError:
        raise InvalidOperation('Unknown command')

    if operation in (_UPDATE, _DELETE):
        check_keys = False

    to_send = []
    idx = 0
    for doc in docs:
        # Encode the current operation
        value = _dict_to_bson(doc, check_keys, opts)
        doc_length = len(value)
        new_message_size = buf.tell() + doc_length
        # Does first document exceed max_message_size?
        doc_too_large = (idx == 0 and (new_message_size > max_message_size))
        # When OP_MSG is used unacknowleged we have to check
        # document size client side or applications won't be notified.
        # Otherwise we let the server deal with documents that are too large
        # since ordered=False causes those documents to be skipped instead of
        # halting the bulk write operation.
        unacked_doc_too_large = (not ack and (doc_length > max_bson_size))
        if doc_too_large or unacked_doc_too_large:
            write_op = list(_FIELD_MAP.keys())[operation]
            _raise_document_too_large(
                write_op, len(value), max_bson_size)
        # We have enough data, return this batch.
        if new_message_size > max_message_size:
            break
        buf.write(value)
        to_send.append(doc)
        idx += 1
        # We have enough documents, return this batch.
        if idx == max_write_batch_size:
            break

    # Write type 1 section size
    length = buf.tell()
    buf.seek(size_location)
    buf.write(_pack_int(length - size_location))

    return to_send, length


def _encode_batched_op_msg(
        operation, command, docs, check_keys, ack, opts, ctx):
    """Encode the next batched insert, update, or delete operation
    as OP_MSG.
    """
    buf = StringIO()

    to_send, _ = _batched_op_msg_impl(
        operation, command, docs, check_keys, ack, opts, ctx, buf)
    return buf.getvalue(), to_send
if _use_c:
    _encode_batched_op_msg = _cmessage._encode_batched_op_msg


def _batched_op_msg_compressed(
        operation, command, docs, check_keys, ack, opts, ctx):
    """Create the next batched insert, update, or delete operation
    with OP_MSG, compressed.
    """
    data, to_send = _encode_batched_op_msg(
        operation, command, docs, check_keys, ack, opts, ctx)

    request_id, msg = _compress(
        2013,
        data,
        ctx.sock_info.compression_context)
    return request_id, msg, to_send


def _batched_op_msg(
        operation, command, docs, check_keys, ack, opts, ctx):
    """OP_MSG implementation entry point."""
    buf = StringIO()

    # Save space for message length and request id
    buf.write(_ZERO_64)
    # responseTo, opCode
    buf.write(b"\x00\x00\x00\x00\xdd\x07\x00\x00")

    to_send, length = _batched_op_msg_impl(
        operation, command, docs, check_keys, ack, opts, ctx, buf)

    # Header - request id and message length
    buf.seek(4)
    request_id = _randint()
    buf.write(_pack_int(request_id))
    buf.seek(0)
    buf.write(_pack_int(length))

    return request_id, buf.getvalue(), to_send
if _use_c:
    _batched_op_msg = _cmessage._batched_op_msg


def _do_batched_op_msg(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Create the next batched insert, update, or delete operation
    using OP_MSG.
    """
    command['$db'] = namespace.split('.', 1)[0]
    if 'writeConcern' in command:
        ack = bool(command['writeConcern'].get('w', 1))
    else:
        ack = True
    if ctx.sock_info.compression_context:
        return _batched_op_msg_compressed(
            operation, command, docs, check_keys, ack, opts, ctx)
    return _batched_op_msg(
        operation, command, docs, check_keys, ack, opts, ctx)


# End OP_MSG -----------------------------------------------------


def _batched_write_command_compressed(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Create the next batched insert, update, or delete command, compressed.
    """
    data, to_send = _encode_batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx)

    request_id, msg = _compress(
        2004,
        data,
        ctx.sock_info.compression_context)
    return request_id, msg, to_send


def _encode_batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Encode the next batched insert, update, or delete command.
    """
    buf = StringIO()

    to_send, _ = _batched_write_command_impl(
        namespace, operation, command, docs, check_keys, opts, ctx, buf)
    return buf.getvalue(), to_send
if _use_c:
    _encode_batched_write_command = _cmessage._encode_batched_write_command


def _batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Create the next batched insert, update, or delete command.
    """
    buf = StringIO()

    # Save space for message length and request id
    buf.write(_ZERO_64)
    # responseTo, opCode
    buf.write(b"\x00\x00\x00\x00\xd4\x07\x00\x00")

    # Write OP_QUERY write command
    to_send, length = _batched_write_command_impl(
        namespace, operation, command, docs, check_keys, opts, ctx, buf)

    # Header - request id and message length
    buf.seek(4)
    request_id = _randint()
    buf.write(_pack_int(request_id))
    buf.seek(0)
    buf.write(_pack_int(length))

    return request_id, buf.getvalue(), to_send
if _use_c:
    _batched_write_command = _cmessage._batched_write_command


def _do_batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Batched write commands entry point."""
    if ctx.sock_info.compression_context:
        return _batched_write_command_compressed(
            namespace, operation, command, docs, check_keys, opts, ctx)
    return _batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx)


def _do_bulk_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx):
    """Bulk write commands entry point."""
    if ctx.sock_info.max_wire_version > 5:
        return _do_batched_op_msg(
            namespace, operation, command, docs, check_keys, opts, ctx)
    return _do_batched_write_command(
        namespace, operation, command, docs, check_keys, opts, ctx)


def _batched_write_command_impl(
        namespace, operation, command, docs, check_keys, opts, ctx, buf):
    """Create a batched OP_QUERY write command."""
    max_bson_size = ctx.max_bson_size
    max_write_batch_size = ctx.max_write_batch_size
    # Max BSON object size + 16k - 2 bytes for ending NUL bytes.
    # Server guarantees there is enough room: SERVER-10643.
    max_cmd_size = max_bson_size + _COMMAND_OVERHEAD
    max_split_size = ctx.max_split_size

    # No options
    buf.write(_ZERO_32)
    # Namespace as C string
    buf.write(b(namespace))
    buf.write(_ZERO_8)
    # Skip: 0, Limit: -1
    buf.write(_SKIPLIM)

    # Where to write command document length
    command_start = buf.tell()
    buf.write(encode(command))

    # Start of payload
    buf.seek(-1, 2)
    # Work around some Jython weirdness.
    buf.truncate()
    try:
        buf.write(_OP_MAP[operation])
    except KeyError:
        raise InvalidOperation('Unknown command')

    if operation in (_UPDATE, _DELETE):
        check_keys = False

    # Where to write list document length
    list_start = buf.tell() - 4
    to_send = []
    idx = 0
    for doc in docs:
        # Encode the current operation
        key = b(str(idx))
        value = encode(doc, check_keys, opts)
        # Is there enough room to add this document? max_cmd_size accounts for
        # the two trailing null bytes.
        doc_too_large = len(value) > max_cmd_size
        if doc_too_large:
            write_op = list(_FIELD_MAP.keys())[operation]
            _raise_document_too_large(
                write_op, len(value), max_bson_size)
        enough_data = (idx >= 1 and
                       (buf.tell() + len(key) + len(value)) >= max_split_size)
        enough_documents = (idx >= max_write_batch_size)
        if enough_data or enough_documents:
            break
        buf.write(_BSONOBJ)
        buf.write(key)
        buf.write(_ZERO_8)
        buf.write(value)
        to_send.append(doc)
        idx += 1

    # Finalize the current OP_QUERY message.
    # Close list and command documents
    buf.write(_ZERO_16)

    # Write document lengths and request id
    length = buf.tell()
    buf.seek(list_start)
    buf.write(_pack_int(length - list_start - 1))
    buf.seek(command_start)
    buf.write(_pack_int(length - command_start))

    return to_send, length


class _OpReply(object):
    """A MongoDB OP_REPLY response message."""

    __slots__ = ("flags", "cursor_id", "number_returned", "documents")

    UNPACK_FROM = struct.Struct("<iqii").unpack_from
    OP_CODE = 1

    def __init__(self, flags, cursor_id, number_returned, documents):
        self.flags = flags
        self.cursor_id = Int64(cursor_id)
        self.number_returned = number_returned
        self.documents = documents

    def raw_response(self, cursor_id=None, user_fields=None):
        """Check the response header from the database, without decoding BSON.

        Check the response for errors and unpack.

        Can raise CursorNotFound, NotPrimaryError, ExecutionTimeout, or
        OperationFailure.

        :Parameters:
          - `cursor_id` (optional): cursor_id we sent to get this response -
            used for raising an informative exception when we get cursor id not
            valid at server response.
        """
        if self.flags & 1:
            # Shouldn't get this response if we aren't doing a getMore
            if cursor_id is None:
                raise ProtocolError("No cursor id for getMore operation")

            # Fake a getMore command response. OP_GET_MORE provides no
            # document.
            msg = "Cursor not found, cursor id: %d" % (cursor_id,)
            errobj = {"ok": 0, "errmsg": msg, "code": 43}
            raise CursorNotFound(msg, 43, errobj)
        elif self.flags & 2:
            error_object = bson.BSON(self.documents).decode()
            # Fake the ok field if it doesn't exist.
            error_object.setdefault("ok", 0)
            if error_object["$err"].startswith(HelloCompat.LEGACY_ERROR):
                raise NotPrimaryError(error_object["$err"], error_object)
            elif error_object.get("code") == 50:
                raise ExecutionTimeout(error_object.get("$err"),
                                       error_object.get("code"),
                                       error_object)
            raise OperationFailure("database error: %s" %
                                   error_object.get("$err"),
                                   error_object.get("code"),
                                   error_object)
        if self.documents:
            return [self.documents]
        return []

    def unpack_response(self, cursor_id=None,
                        codec_options=_UNICODE_REPLACE_CODEC_OPTIONS,
                        user_fields=None, legacy_response=False):
        """Unpack a response from the database and decode the BSON document(s).

        Check the response for errors and unpack, returning a dictionary
        containing the response data.

        Can raise CursorNotFound, NotPrimaryError, ExecutionTimeout, or
        OperationFailure.

        :Parameters:
          - `cursor_id` (optional): cursor_id we sent to get this response -
            used for raising an informative exception when we get cursor id not
            valid at server response
          - `codec_options` (optional): an instance of
            :class:`~bson.codec_options.CodecOptions`
        """
        self.raw_response(cursor_id)
        if legacy_response:
            return bson.decode_all(self.documents, codec_options)
        return bson._decode_all_selective(
            self.documents, codec_options, user_fields)

    def command_response(self):
        """Unpack a command response."""
        docs = self.unpack_response()
        assert self.number_returned == 1
        return docs[0]

    def raw_command_response(self):
        """Return the bytes of the command response."""
        # This should never be called on _OpReply.
        raise NotImplementedError

    @property
    def more_to_come(self):
        """Is the moreToCome bit set on this response?"""
        return False

    @classmethod
    def unpack(cls, msg):
        """Construct an _OpReply from raw bytes."""
        # PYTHON-945: ignore starting_from field.
        flags, cursor_id, _, number_returned = cls.UNPACK_FROM(msg)

        # Convert Python 3 memoryview to bytes. Note we should call
        # memoryview.tobytes() if we start using memoryview in Python 2.7.
        documents = bytes(msg[20:])
        return cls(flags, cursor_id, number_returned, documents)


class _OpMsg(object):
    """A MongoDB OP_MSG response message."""

    __slots__ = ("flags", "cursor_id", "number_returned", "payload_document")

    UNPACK_FROM = struct.Struct("<IBi").unpack_from
    OP_CODE = 2013

    # Flag bits.
    CHECKSUM_PRESENT = 1
    MORE_TO_COME = 1 << 1
    EXHAUST_ALLOWED = 1 << 16  # Only present on requests.

    def __init__(self, flags, payload_document):
        self.flags = flags
        self.payload_document = payload_document

    def raw_response(self, cursor_id=None, user_fields={}):
        """
        cursor_id is ignored
        user_fields is used to determine which fields must not be decoded
        """
        inflated_response = _decode_selective(
            RawBSONDocument(self.payload_document), user_fields,
            DEFAULT_RAW_BSON_OPTIONS)
        return [inflated_response]

    def unpack_response(self, cursor_id=None,
                        codec_options=_UNICODE_REPLACE_CODEC_OPTIONS,
                        user_fields=None, legacy_response=False):
        """Unpack a OP_MSG command response.

        :Parameters:
          - `cursor_id` (optional): Ignored, for compatibility with _OpReply.
          - `codec_options` (optional): an instance of
            :class:`~bson.codec_options.CodecOptions`
        """
        # If _OpMsg is in-use, this cannot be a legacy response.
        assert not legacy_response
        return bson._decode_all_selective(
            self.payload_document, codec_options, user_fields)

    def command_response(self):
        """Unpack a command response."""
        return self.unpack_response()[0]

    def raw_command_response(self):
        """Return the bytes of the command response."""
        return self.payload_document

    @property
    def more_to_come(self):
        """Is the moreToCome bit set on this response?"""
        return self.flags & self.MORE_TO_COME

    @classmethod
    def unpack(cls, msg):
        """Construct an _OpMsg from raw bytes."""
        flags, first_payload_type, first_payload_size = cls.UNPACK_FROM(msg)
        if flags != 0:
            if flags & cls.CHECKSUM_PRESENT:
                raise ProtocolError(
                    "Unsupported OP_MSG flag checksumPresent: "
                    "0x%x" % (flags,))

            if flags ^ cls.MORE_TO_COME:
                raise ProtocolError(
                    "Unsupported OP_MSG flags: 0x%x" % (flags,))
        if first_payload_type != 0:
            raise ProtocolError(
                "Unsupported OP_MSG payload type: "
                "0x%x" % (first_payload_type,))

        if len(msg) != first_payload_size + 5:
            raise ProtocolError("Unsupported OP_MSG reply: >1 section")

        # Convert Python 3 memoryview to bytes. Note we should call
        # memoryview.tobytes() if we start using memoryview in Python 2.7.
        payload_document = bytes(msg[5:])
        return cls(flags, payload_document)


_UNPACK_REPLY = {
    _OpReply.OP_CODE: _OpReply.unpack,
    _OpMsg.OP_CODE: _OpMsg.unpack,
}


def _first_batch(sock_info, db, coll, query, ntoreturn,
                 secondary_ok, codec_options, read_preference, cmd, listeners):
    """Simple query helper for retrieving a first (and possibly only) batch."""
    query = _Query(
        0, db, coll, 0, query, None, codec_options,
        read_preference, ntoreturn, 0, DEFAULT_READ_CONCERN, None, None,
        None, None, False)

    name = next(iter(cmd))
    publish = listeners.enabled_for_commands
    if publish:
        start = datetime.datetime.now()

    request_id, msg, max_doc_size = query.get_message(secondary_ok, sock_info)

    if publish:
        encoding_duration = datetime.datetime.now() - start
        listeners.publish_command_start(
            cmd, db, request_id, sock_info.address,
            service_id=sock_info.service_id)
        start = datetime.datetime.now()

    sock_info.send_message(msg, max_doc_size)
    reply = sock_info.receive_message(request_id)
    try:
        docs = reply.unpack_response(None, codec_options)
    except Exception as exc:
        if publish:
            duration = (datetime.datetime.now() - start) + encoding_duration
            if isinstance(exc, (NotPrimaryError, OperationFailure)):
                failure = exc.details
            else:
                failure = _convert_exception(exc)
            listeners.publish_command_failure(
                duration, failure, name, request_id, sock_info.address,
                service_id=sock_info.service_id)
        raise
    # listIndexes
    if 'cursor' in cmd:
        result = {
            u'cursor': {
                u'firstBatch': docs,
                u'id': reply.cursor_id,
                u'ns': u'%s.%s' % (db, coll)
            },
            u'ok': 1.0
        }
    # fsyncUnlock, currentOp
    else:
        result = docs[0] if docs else {}
        result[u'ok'] = 1.0
    if publish:
        duration = (datetime.datetime.now() - start) + encoding_duration
        listeners.publish_command_success(
            duration, result, name, request_id, sock_info.address,
            service_id=sock_info.service_id)

    return result
