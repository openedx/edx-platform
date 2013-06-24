from xblock.runtime import KeyValueStore, InvalidScopeError


class SessionKeyValueStore(KeyValueStore):
    def __init__(self, request, descriptor_model_data):
        self._descriptor_model_data = descriptor_model_data
        self._session = request.session

    def get(self, key):
        try:
            return self._descriptor_model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            return self._session[tuple(key)]

    def set(self, key, value):
        try:
            self._descriptor_model_data[key.field_name] = value
        except (KeyError, InvalidScopeError):
            self._session[tuple(key)] = value

    def delete(self, key):
        try:
            del self._descriptor_model_data[key.field_name]
        except (KeyError, InvalidScopeError):
            del self._session[tuple(key)]

    def has(self, key):
        return key.field_name in self._descriptor_model_data or tuple(key) in self._session

class StaticPreviewKeyValueStore(KeyValueStore):
    '''Like the SessionKeyValueStore but session independent (this breaks randomization)'''
    def __init__(self, model_data):
        self._model_data = model_data

    def get(self, key):
        try:
            return self._model_data[key.field_name]
        except:
            raise KeyError

    def set(self, key, value):
        try:
            self._model_data[key.field_name] = value
        except (KeyError, InvalidScopeError):
            pass

    def delete(self, key):
        try:
            del self._model_data[key.field_name]
        except:
            raise KeyError

    def has(self, key):
        return key.field_name in self._model_data