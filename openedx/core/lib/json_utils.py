"""
Helpers for json serialization
"""


import datetime
from django.core.serializers.json import DjangoJSONEncoder
from opaque_keys.edx.keys import CourseKey, UsageKey
import six


class EdxJSONEncoder(DjangoJSONEncoder):
    """
    Custom JSONEncoder that handles `Location` and `datetime.datetime` objects.

    `Location`s are encoded as their url string form, and `datetime`s as
    ISO date strings
    """
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, (CourseKey, UsageKey)):
            return six.text_type(o)
        elif isinstance(o, datetime.datetime):
            if o.tzinfo is not None:
                if o.utcoffset() is None:
                    return o.isoformat() + 'Z'
                else:
                    return o.isoformat()
            else:
                return o.isoformat()
        else:
            return super(EdxJSONEncoder, self).default(o)
