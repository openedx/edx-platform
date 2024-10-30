"""
URL pattern converters
https://docs.djangoproject.com/en/5.1/topics/http/urls/#registering-custom-path-converters
"""
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKeyV2

from ..api import LatestVersion


class UsageKeyV2Converter:
    """
    Converter that matches V2 usage keys like:
        lb:Org:LIB:drag-and-drop-v2:91c2b1d5
    """
    regex = r'[\w-]+(:[\w\-.]+)+'

    def to_python(self, value: str) -> UsageKeyV2:
        try:
            return UsageKeyV2.from_string(value)
        except InvalidKeyError as exc:
            raise ValueError from exc

    def to_url(self, value: UsageKeyV2) -> str:
        return str(value)


class VersionConverter:
    """
    Converter that matches a version string like "draft", "published", or a
    number, and converts it to either an 'int' or a LatestVersion enum value.
    """
    regex = r'(draft|published|\d+)'

    def to_python(self, value: str | None) -> LatestVersion | int:
        """ Convert from string to LatestVersion or integer version spec """
        if value is None:
            return LatestVersion.AUTO  # AUTO = published if we're in the LMS, draft if we're in Studio.
        if value == "draft":
            return LatestVersion.DRAFT
        if value == "published":
            return LatestVersion.PUBLISHED
        return int(value)  # May raise ValueError, which Django will convert to 404

    def to_url(self, value: LatestVersion | int | None) -> str:
        """
        Convert from LatestVersion or integer version spec to URL path string.

        Note that if you provide any value at all, django won't be able to
        match the paths that don't have a version in the URL, so if you want
        LatestVersion.AUTO, don't pass any value for 'version' to reverse(...).
        """
        if value is None or value == LatestVersion.AUTO:
            raise ValueError  # This default value does not need to be in the URL
        if isinstance(value, int):
            return str(value)
        return value.value  # LatestVersion.DRAFT or PUBLISHED
