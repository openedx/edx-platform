"""
URL pattern converters
https://docs.djangoproject.com/en/5.1/topics/http/urls/#registering-custom-path-converters
"""
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKeyV2


class UsageKeyV2Converter:
    """
    Converter that matches V2 usage keys like:
        lb:Org:LIB:drag-and-drop-v2:91c2b1d5
    """
    regex = r'[\w-]+(:[\w\-.]+)+'

    def to_python(self, value):
        try:
            return UsageKeyV2.from_string(value)
        except InvalidKeyError as exc:
            raise ValueError from exc

    def to_url(self, value):
        return str(value)
