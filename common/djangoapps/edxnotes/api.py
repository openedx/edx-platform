from uuid import uuid4
from xmodule.modulestore.exceptions import ItemNotFoundError

from .notes_list import LIST


FORMAT = {
    "id": "39fc339cf058bd22176771b3e3187329",  # unique id (added by backend)
    "annotator_schema_version": "v1.0",        # schema version: default v1.0
    "created": "2011-05-24T18:52:08.036814",   # created datetime in iso8601 format (added by backend)
    "updated": "2011-05-26T12:17:05.012544",   # updated datetime in iso8601 format (added by backend)
    "text": "A note I wrote",                  # content of annotation
    "quote": "the text that was annotated",    # the annotated text (added by frontend)
    "uri": "http://example.com",               # URI of annotated document (added by frontend)
    "ranges": [                                # list of ranges covered by annotation (usually only one entry)
        {
            "start": "/p[1]",                  # (relative) XPath to start element
            "end": "/p[1]",                    # (relative) XPath to end element
            "startOffset": 52,                 # character offset within start element
            "endOffset": 54                    # character offset within end element
        }
    ],
    "user": "user",                            # user id of annotation owner (can also be an object with an 'id' property)
    "usage_id": "usage_id",                    # usage id of a component (added by frontend)
    "consumer": "annotateit",                  # consumer key of backend
    "permissions": {                           # annotation permissions (from Permissions/AnnotateItPermissions plugin)
        "read": ["user"],
        "admin": ["user"],
        "update": ["user"],
        "delete": ["user"]
    }
}


class EdxNotes(object):
    """docstring for EdxNotes"""
    def __init__(self):
        super(EdxNotes, self).__init__()

    @staticmethod
    def create(note_info):
        note_info['id'] = uuid4().hex
        LIST.append(note_info)
        return note_info

    @staticmethod
    def read(note_id, user):
        result = filter(lambda note: note.get('id') == note_id, LIST)
        if result:
            return result
        else:
            raise ItemNotFoundError()

    @staticmethod
    def update(note_id, note_info):
        result = filter(lambda note: note.get('id') == note_id, LIST)
        if result:
            return result
        else:
            raise ItemNotFoundError()

    @staticmethod
    def delete(note_id):
        result = filter(lambda note: note.get('id') == note_id, LIST)
        if not result:
            raise ItemNotFoundError()

    @staticmethod
    def search(user, usage_id):
        results = filter(lambda note: note.get('user') == user, LIST)
        return {
            'total': len(results),
            'rows': results
        }
