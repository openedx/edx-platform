# Copyright 2014-present MongoDB, Inc.
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

"""Communicate with one MongoDB server in a topology."""

from datetime import datetime

from bson import _decode_all_selective

from pymongo.errors import NotPrimaryError, OperationFailure
from pymongo.helpers import _check_command_response
from pymongo.message import _convert_exception, _OpMsg
from pymongo.response import Response, PinnedResponse
from pymongo.server_type import SERVER_TYPE

_CURSOR_DOC_FIELDS = {'cursor': {'firstBatch': 1, 'nextBatch': 1}}


class Server(object):
    def __init__(self, server_description, pool, monitor, topology_id=None,
                 listeners=None, events=None):
        """Represent one MongoDB server."""
        self._description = server_description
        self._pool = pool
        self._monitor = monitor
        self._topology_id = topology_id
        self._publish = listeners is not None and listeners.enabled_for_server
        self._listener = listeners
        self._events = None
        if self._publish:
            self._events = events()

    def open(self):
        """Start monitoring, or restart after a fork.

        Multiple calls have no effect.
        """
        if not self._pool.opts.load_balanced:
            self._monitor.open()

    def reset(self, service_id=None):
        """Clear the connection pool."""
        self.pool.reset(service_id)

    def close(self):
        """Clear the connection pool and stop the monitor.

        Reconnect with open().
        """
        if self._publish:
            self._events.put((self._listener.publish_server_closed,
                              (self._description.address, self._topology_id)))
        self._monitor.close()
        self._pool.reset()

    def request_check(self):
        """Check the server's state soon."""
        self._monitor.request_check()

    def run_operation(
            self, sock_info, operation,
            set_secondary_okay, listeners, unpack_res):
        """Run a _Query or _GetMore operation and return a Response object.

        This method is used only to run _Query/_GetMore operations from
        cursors.
        Can raise ConnectionFailure, OperationFailure, etc.

        :Parameters:
          - `operation`: A _Query or _GetMore object.
          - `set_secondary_okay`: Pass to operation.get_message.
          - `all_credentials`: dict, maps auth source to MongoCredential.
          - `listeners`: Instance of _EventListeners or None.
          - `unpack_res`: A callable that decodes the wire protocol response.
        """
        duration = None
        publish = listeners.enabled_for_commands
        if publish:
            start = datetime.now()

        use_cmd = operation.use_command(sock_info)
        more_to_come = (operation.sock_mgr
                        and operation.sock_mgr.more_to_come)
        if more_to_come:
            request_id = 0
        else:
            message = operation.get_message(
                set_secondary_okay, sock_info, use_cmd)
            request_id, data, max_doc_size = self._split_message(message)

        if publish:
            cmd, dbn = operation.as_command(sock_info)
            listeners.publish_command_start(
                cmd, dbn, request_id, sock_info.address,
                service_id=sock_info.service_id)
            start = datetime.now()

        try:
            if more_to_come:
                reply = sock_info.receive_message(None)
            else:
                sock_info.send_message(data, max_doc_size)
                reply = sock_info.receive_message(request_id)

            # Unpack and check for command errors.
            if use_cmd:
                user_fields = _CURSOR_DOC_FIELDS
                legacy_response = False
            else:
                user_fields = None
                legacy_response = True
            docs = unpack_res(reply, operation.cursor_id,
                              operation.codec_options,
                              legacy_response=legacy_response,
                              user_fields=user_fields)
            if use_cmd:
                first = docs[0]
                operation.client._process_response(first, operation.session)
                _check_command_response(first, sock_info.max_wire_version)
        except Exception as exc:
            if publish:
                duration = datetime.now() - start
                if isinstance(exc, (NotPrimaryError, OperationFailure)):
                    failure = exc.details
                else:
                    failure = _convert_exception(exc)
                listeners.publish_command_failure(
                    duration, failure, operation.name,
                    request_id, sock_info.address,
                    service_id=sock_info.service_id)
            raise

        if publish:
            duration = datetime.now() - start
            # Must publish in find / getMore / explain command response
            # format.
            if use_cmd:
                res = docs[0]
            elif operation.name == "explain":
                res = docs[0] if docs else {}
            else:
                res = {"cursor": {"id": reply.cursor_id,
                                  "ns": operation.namespace()},
                       "ok": 1}
                if operation.name == "find":
                    res["cursor"]["firstBatch"] = docs
                else:
                    res["cursor"]["nextBatch"] = docs
            listeners.publish_command_success(
                duration, res, operation.name, request_id,
                sock_info.address, service_id=sock_info.service_id)

        # Decrypt response.
        client = operation.client
        if client and client._encrypter:
            if use_cmd:
                decrypted = client._encrypter.decrypt(
                    reply.raw_command_response())
                docs = _decode_all_selective(
                    decrypted, operation.codec_options, user_fields)

        if client._should_pin_cursor(operation.session) or operation.exhaust:
            sock_info.pin_cursor()
            if isinstance(reply, _OpMsg):
                # In OP_MSG, the server keeps sending only if the
                # more_to_come flag is set.
                more_to_come = reply.more_to_come
            else:
                # In OP_REPLY, the server keeps sending until cursor_id is 0.
                more_to_come = bool(operation.exhaust and reply.cursor_id)
            if operation.sock_mgr:
                operation.sock_mgr.update_exhaust(more_to_come)
            response = PinnedResponse(
                data=reply,
                address=self._description.address,
                socket_info=sock_info,
                duration=duration,
                request_id=request_id,
                from_command=use_cmd,
                docs=docs,
                more_to_come=more_to_come)
        else:
            response = Response(
                data=reply,
                address=self._description.address,
                duration=duration,
                request_id=request_id,
                from_command=use_cmd,
                docs=docs)

        return response

    def get_socket(self, all_credentials, handler=None):
        return self.pool.get_socket(all_credentials, handler)

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, server_description):
        assert server_description.address == self._description.address
        self._description = server_description

    @property
    def pool(self):
        return self._pool

    def _split_message(self, message):
        """Return request_id, data, max_doc_size.

        :Parameters:
          - `message`: (request_id, data, max_doc_size) or (request_id, data)
        """
        if len(message) == 3:
            return message
        else:
            # get_more and kill_cursors messages don't include BSON documents.
            request_id, data = message
            return request_id, data, 0

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self._description)
