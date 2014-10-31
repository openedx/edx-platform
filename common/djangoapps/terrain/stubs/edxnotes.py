"""
Stub implementation of EdXNotes for acceptance tests
"""

import json
import re
from uuid import uuid4
from datetime import datetime
from copy import deepcopy

from .http import StubHttpRequestHandler, StubHttpService


class StubEdXNotesServiceHandler(StubHttpRequestHandler):
    """
    Handler for EdXNotes requests.
    """
    URL_HANDLERS = {
        "GET": {
            "/api/v1/annotations$": "_collection",
            "/api/v1/annotations/(?P<note_id>[0-9A-Fa-f]+)$": "_read",
            "/api/v1/search$": "_search",
        },
        "POST": {
            "/api/v1/annotations$": "_create",
            "/create_notes": "_create_notes",
        },
        "PUT": {
            "/api/v1/annotations/(?P<note_id>[0-9A-Fa-f]+)$": "_update",
            "/cleanup$": "_cleanup",
        },
        "DELETE": {
            "/api/v1/annotations/(?P<note_id>[0-9A-Fa-f]+)$": "_delete",
        },
    }

    def _match_pattern(self, pattern_handlers):
        for pattern in pattern_handlers:
            match = re.match(pattern, self.path_only)
            if match:
                handler = getattr(self, pattern_handlers[pattern], None)
                if handler:
                    handler(**match.groupdict())
                    return True
        return None

    def _send_handler_response(self, method):
        """
        Delegate response to handler methods.
        If no handler defined, send a 404 response.
        """
        # Choose the list of handlers based on the HTTP method
        if method in self.URL_HANDLERS:
            handlers_list = self.URL_HANDLERS[method]
        else:
            self.log_error('Unrecognized method "{method}"'.format(method=method))
            return

        # Check the path (without querystring params) against our list of handlers
        if self._match_pattern(handlers_list):
            return
        # If we don't have a handler for this URL and/or HTTP method,
        # respond with a 404.
        else:
            self.send_response(404, content="404 Not Found")

    def do_GET(self):
        """
        Handle GET methods to the EdXNotes API stub.
        """
        self._send_handler_response('GET')

    def do_POST(self):
        """
        Handle POST methods to the EdXNotes API stub.
        """
        self._send_handler_response('POST')

    def do_PUT(self):
        """
        Handle PUT methods to the EdXNotes API stub.
        """
        if self.path.startswith('/set_config'):
            return StubHttpRequestHandler.do_PUT(self)

        self._send_handler_response('PUT')

    def do_DELETE(self):
        """
        Handle DELETE methods to the EdXNotes API stub.
        """
        self._send_handler_response('DELETE')

    def _create(self):
        """
        Create a note, assign id, annotator_schema_version, created and updated dates.
        """
        note = json.loads(self.request_content)
        note['id'] = uuid4().hex
        note['annotator_schema_version'] = "v1.0"
        note['created'] = datetime.utcnow().isoformat()
        note['updated'] = datetime.utcnow().isoformat()
        self.server.add_notes(note)
        self.send_json_response(note)

    def _create_notes(self):
        """
        The same as self._create, but it works a list of notes.
        """
        try:
            notes = json.loads(self.request_content)
        except ValueError:
            self.send_response(400, content="Bad Request")
            return

        if not isinstance(notes, list):
            self.send_response(400, content="Bad Request")
            return

        for note in notes:
            note['id'] = uuid4().hex
            note['annotator_schema_version'] = "v1.0"
            note['created'] = datetime.utcnow().isoformat()
            note['updated'] = datetime.utcnow().isoformat()
            self.server.add_notes(note)

        self.send_json_response(notes)

    def _read(self, note_id):
        """
        Return the note by note id.
        """
        result = self.server.filter_by_id(note_id)
        if result:
            self.send_json_response(result[0])
        else:
            self.send_response(404, content="404 Not Found")

    def _update(self, note_id):
        """
        Update the note by note id.
        """
        result = self.server.filter_by_id(note_id)
        if result:
            result[0].update(json.loads(self.request_content))
            self.send_json_response(result)
        else:
            self.send_response(404, content="404 Not Found")

    def _delete(self, note_id):
        """
        Delete the note by note id.
        """
        if self.server.delete_note(note_id):
            self.send_response(204, "No Content")
        else:
            self.send_response(404, content="404 Not Found")

    def _search(self):
        """
        Search for a notes by user id.
        """
        user = self.get_params.get("user", None)
        if user is None:
            self.send_response(400, content="Bad Request")
            return

        results = self.server.filter_by_user(user)
        self.send_json_response({
            "total": len(results),
            "rows": results,
        })

    def _collection(self):
        """
        Return all notes for the user.
        """
        user = self.get_params.get("user", None)
        if user is None:
            self.send_response(400, content="Bad Request")
            return
        self.send_json_response(self.server.filter_by_user(user))

    def _cleanup(self):
        """
        Helper method that removes all notes for the stub EdXNotes service.
        """
        self.server.cleanup()
        self.send_response(200)


class StubEdXNotesService(StubHttpService):
    HANDLER_CLASS = StubEdXNotesServiceHandler

    def __init__(self, *args, **kwargs):
        super(StubEdXNotesService, self).__init__(*args, **kwargs)
        self.notes = list()

    def get_all_notes(self):
        return deepcopy(self.notes)

    def add_notes(self, notes):
        if not isinstance(notes, list):
            notes = [notes]

        for note in notes:
            self.notes.append(note)

    def delete_note(self, note_id):
        note = self.filter_by_id(note_id)
        if note:
            index = self.notes.index(note[0])
            self.notes.pop(index)
            return True
        else:
            return False

    def cleanup(self):
        self.notes = list()

    def filter_by_id(self, note_id):
        return self.filter_by('id', note_id)

    def filter_by_user(self, user):
        return self.filter_by('user', user)

    def filter_by(self, field_name, value):
        return filter(lambda note: note.get(field_name) == value, self.notes)
