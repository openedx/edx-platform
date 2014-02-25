"""
An :class:`~xblock.runtime.KeyValueStore` that stores data in the django session
"""
from __future__ import absolute_import

from xblock.runtime import KeyValueStore

class SessionKeyValueStore(KeyValueStore):
    def __init__(self, request):
        self._session = request.session

    def get(self, key):
        return self._session[tuple(key)]

    def set(self, key, value):
        self._session[tuple(key)] = value

    def delete(self, key):
        del self._session[tuple(key)]

    def has(self, key):
        return tuple(key) in self._session
