LIST = [
    {
        "id": "39fc339cf058bd22176771b3e3187329",  # unique id (added by backend)
        "annotator_schema_version": "v1.0",        # schema version: default v1.0
        "created": "2011-05-24T18:52:08.036814",   # created datetime in iso8601 format (added by backend)
        "updated": "2011-05-26T12:17:05.012544",   # updated datetime in iso8601 format (added by backend)
        "text": "A note I wrote",                  # content of annotation
        "quote": "the basics",                     # the annotated text (added by frontend)
        "uri": "http://example.com",               # URI of annotated document (added by frontend)
        "ranges": [                                # list of ranges covered by annotation (usually only one entry)
            {
                "start": "/p[1]",                  # (relative) XPath to start element
                "end": "/p[1]",                    # (relative) XPath to end element
                "startOffset": 81,                 # character offset within start element
                "endOffset": 91                    # character offset within end element
            }
        ],
        "user": "user",                           # user id of annotation owner (can also be an object with an 'id' property)
        "consumer": "annotateit",                  # consumer key of backend
        "permissions": {                           # annotation permissions (from Permissions/AnnotateItPermissions plugin)
            "read": ["user"],
            "admin": ["user"],
            "update": ["user"],
            "delete": ["user"]
        }
    },
    {
        "id": "39fc339cf058bd22176771b3e3187330",  # unique id (added by backend)
        "annotator_schema_version": "v1.0",        # schema version: default v1.0
        "created": "2014-05-24T18:52:08.036814",   # created datetime in iso8601 format (added by backend)
        "updated": "2014-05-26T12:17:05.012544",   # updated datetime in iso8601 format (added by backend)
        "text": "Test note",                  # content of annotation
        "quote": "We",    # the annotated text (added by frontend)
        "uri": "http://example.com",               # URI of annotated document (added by frontend)
        "ranges": [                                # list of ranges covered by annotation (usually only one entry)
            {
                "start": "/p[1]",                  # (relative) XPath to start element
                "end": "/p[1]",                    # (relative) XPath to end element
                "startOffset": 52,                 # character offset within start element
                "endOffset": 54                    # character offset within end element
            }
        ],
        "user": "edx_user",                           # user id of annotation owner (can also be an object with an 'id' property)
        "consumer": "annotateit",                  # consumer key of backend
        "permissions": {                           # annotation permissions (from Permissions/AnnotateItPermissions plugin)
            "read": ["edx_user"],
            "admin": ["edx_user"],
            "update": ["edx_user"],
            "delete": ["edx_user"]
        }
    }

]
