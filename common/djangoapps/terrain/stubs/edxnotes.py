"""
Stub implementation of EdxNotes for acceptance tests
"""

import json
import re
from uuid import uuid4
from datetime import datetime
from copy import deepcopy

from .http import StubHttpRequestHandler, StubHttpService


# pylint: disable=invalid-name
class StubEdxNotesServiceHandler(StubHttpRequestHandler):
    """
    Handler for EdxNotes requests.
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
        """
        Finds handler by the provided handler patterns and delegate response to
        the matched handler.
        """
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
            self.log_error("Unrecognized method '{method}'".format(method=method))
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
        Handle GET methods to the EdxNotes API stub.
        """
        self._send_handler_response("GET")

    def do_POST(self):
        """
        Handle POST methods to the EdxNotes API stub.
        """
        self._send_handler_response("POST")

    def do_PUT(self):
        """
        Handle PUT methods to the EdxNotes API stub.
        """
        if self.path.startswith("/set_config"):
            return StubHttpRequestHandler.do_PUT(self)

        self._send_handler_response("PUT")

    def do_DELETE(self):
        """
        Handle DELETE methods to the EdxNotes API stub.
        """
        self._send_handler_response("DELETE")

    def do_OPTIONS(self):
        """
        Handle OPTIONS methods to the EdxNotes API stub.
        """
        self.send_response(200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Length, Content-Type, X-Annotator-Auth-Token, X-Requested-With, X-Annotator-Auth-Token, X-Requested-With, X-CSRFToken",
        })

    def respond(self, status_code=200, content=None):
        """
        Send a response back to the client with the HTTP `status_code` (int),
        the given content serialized as JSON (str), and the headers set appropriately.
        """
        headers = {
            "Access-Control-Allow-Origin": "*",
        }
        if status_code < 400 and content:
            headers["Content-Type"] = "application/json"
            content = json.dumps(content)
        else:
            headers["Content-Type"] = "text/html"

        self.send_response(status_code, content, headers)

    def _create(self):
        """
        Create a note, assign id, annotator_schema_version, created and updated dates.
        """
        note = json.loads(self.request_content)
        note["id"] = uuid4().hex
        note["annotator_schema_version"] = "v1.0"
        note["created"] = datetime.utcnow().isoformat()
        note["updated"] = datetime.utcnow().isoformat()
        self.server.add_notes(note)
        self.respond(content=note)

    def _create_notes(self):
        """
        The same as self._create, but it works a list of notes.
        """
        try:
            notes = json.loads(self.request_content)
        except ValueError:
            self.respond(400, "Bad Request")
            return

        if not isinstance(notes, list):
            self.respond(400, "Bad Request")
            return

        for note in notes:
            note["id"] = uuid4().hex
            note["annotator_schema_version"] = "v1.0"
            note["created"] = datetime.utcnow().isoformat()
            note["updated"] = datetime.utcnow().isoformat()
            self.server.add_notes(note)

        self.respond(content=notes)

    def _read(self, note_id):
        """
        Return the note by note id.
        """
        notes = self.server.get_notes()
        result = self.server.filter_by_id(notes, note_id)
        if result:
            self.respond(content=result[0])
        else:
            self.respond(404, "404 Not Found")

    def _update(self, note_id):
        """
        Update the note by note id.
        """
        note = self.server.update_note(note_id, json.loads(self.request_content))
        if note:
            self.respond(content=note)
        else:
            self.respond(404, "404 Not Found")

    def _delete(self, note_id):
        """
        Delete the note by note id.
        """
        if self.server.delete_note(note_id):
            self.respond(204, "No Content")
        else:
            self.respond(404, "404 Not Found")

    def _search(self):
        """
        Search for a notes by user id, course_id and usage_id.
        """
        user = self.get_params.get("user", None)
        usage_id = self.get_params.get("usage_id", None)
        course_id = self.get_params.get("course_id", None)
        if user is None or course_id is None:
            self.respond(400, "Bad Request")
            return

        notes = self.server.get_notes()
        results = self.server.filter_by_user(notes, user)
        results = self.server.filter_by_course_id(results, course_id)
        if usage_id is not None:
            results = self.server.filter_by_usage_id(results, usage_id)
        self.respond(content={
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
        notes = self.server.get_notes()
        self.respond(content=self.server.filter_by_user(notes, user))

    def _cleanup(self):
        """
        Helper method that removes all notes to the stub EdxNotes service.
        """
        self.server.cleanup()
        self.respond()


class StubEdxNotesService(StubHttpService):
    """
    Stub EdxNotes service.
    """
    HANDLER_CLASS = StubEdxNotesServiceHandler

    def __init__(self, *args, **kwargs):
        super(StubEdxNotesService, self).__init__(*args, **kwargs)
        self.notes = list()

    def get_notes(self):
        """
        Returns a list of all notes.
        """
        return deepcopy(self.notes)

    def add_notes(self, notes):
        """
        Adds `notes(list)` to the stub EdxNotes service.
        """
        if not isinstance(notes, list):
            notes = [notes]

        for note in notes:
            self.notes.append(note)

    def update_note(self, note_id, note_info):
        """
        Updates the note with `note_id(str)` by the `note_info(dict)` to the
        stub EdxNotes service.
        """
        note = self.filter_by_id(self.notes, note_id)
        if note:
            note[0].update(note_info)
            return note
        else:
            return None

    def delete_note(self, note_id):
        """
        Removes the note with `note_id(str)` to the stub EdxNotes service.
        """
        note = self.filter_by_id(self.notes, note_id)
        if note:
            index = self.notes.index(note[0])
            self.notes.pop(index)
            return True
        else:
            return False

    def cleanup(self):
        """
        Removes all notes to the stub EdxNotes service.
        """
        self.notes = list()

    def filter_by_id(self, data, note_id):
        """
        Filters provided `data(list)` by the `note_id(str)`.
        """
        return self.filter_by(data, "id", note_id)

    def filter_by_user(self, data, user):
        """
        Filters provided `data(list)` by the `user(str)`.
        """
        return self.filter_by(data, "user", user)

    def filter_by_usage_id(self, data, usage_id):
        """
        Filters provided `data(list)` by the `usage_id(str)`.
        """
        return self.filter_by(data, "usage_id", usage_id)

    def filter_by_course_id(self, data, course_id):
        """
        Filters provided `data(list)` by the `course_id(str)`.
        """
        return self.filter_by(data, "course_id", course_id)

    def filter_by(self, data, field_name, value):
        """
        Filters provided `data(list)` by the `field_name(str)` with `value`.
        """
        return [note for note in data if note.get(field_name) == value]
