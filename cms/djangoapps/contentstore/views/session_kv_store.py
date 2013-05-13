from xblock.runtime import KeyValueStore, InvalidScopeError


class SessionKeyValueStore(KeyValueStore):
    def __init__(self, request, model_data):
        self._model_data = model_data
        self._session = request.session

    def get(self, key):
        try:
            return self._model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            return self._session[tuple(key)]

    def set(self, key, value):
        try:
            self._model_data[key.field_name] = value
        except (KeyError, InvalidScopeError):
            self._session[tuple(key)] = value

    def delete(self, key):
        try:
            del self._model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            del self._session[tuple(key)]

    def has(self, key):
        return key in self._model_data or key in self._session
