"""
URL pattern converters
https://docs.djangoproject.com/en/5.1/topics/http/urls/#registering-custom-path-converters
"""
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryContainerLocator


class LibraryContainerLocatorConverter:
    """
    Converter that matches library container IDs like:
        lct:CL-TEST:containers:unit:u1
    """
    regex = r'[\w-]+(:[\w\-.]+)+'

    def to_python(self, value: str) -> LibraryContainerLocator:
        try:
            return LibraryContainerLocator.from_string(value)
        except InvalidKeyError as exc:
            raise ValueError from exc

    def to_url(self, value: LibraryContainerLocator) -> str:
        return str(value)
