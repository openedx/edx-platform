import uuid
from xmodule.modulestore.exceptions import ItemNotFoundError


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
            "start": "/p[69]/span/span",           # (relative) XPath to start element
            "end": "/p[70]/span/span",             # (relative) XPath to end element
            "startOffset": 0,                      # character offset within start element
            "endOffset": 120                       # character offset within end element
        }
    ],
    "user": "user",                           # user id of annotation owner (can also be an object with an 'id' property)
    "consumer": "annotateit",                  # consumer key of backend
    "tags": [],             # list of tags (from Tags plugin)
    "permissions": {                           # annotation permissions (from Permissions/AnnotateItPermissions plugin)
        "read": [],
        "admin": [],
        "update": [],
        "delete": []
    }
}


class EdxNotes(object):
    """docstring for EdxNotes"""
    def __init__(self):
        super(EdxNotes, self).__init__()

    @staticmethod
    def create(note_info):
        note_info['id'] = uuid.uuid4().hex
        return note_info

    @staticmethod
    def read(note_id):
        if not note_id:
            raise ItemNotFoundError()
        return FORMAT

    @staticmethod
    def update(note_id, note_info):
        if not note_id:
            raise ItemNotFoundError()
        return note_info

    @staticmethod
    def delete(note_id):
        if not note_id:
            raise ItemNotFoundError()
        pass

    @staticmethod
    def search(args):
        return {
            'total': 1,
            'rows': [FORMAT]
        }
