import hashlib
import json

from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.settings import extensions_api_settings


class KeyConstructor:
    def __init__(self, memoize_for_request=None, params=None):
        if memoize_for_request is None:
            self.memoize_for_request = extensions_api_settings.DEFAULT_KEY_CONSTRUCTOR_MEMOIZE_FOR_REQUEST
        else:
            self.memoize_for_request = memoize_for_request
        if params is None:
            self.params = {}
        else:
            self.params = params
        self.bits = self.get_bits()

    def get_bits(self):
        _bits = {}
        for attr in dir(self.__class__):
            attr_value = getattr(self.__class__, attr)
            if isinstance(attr_value, bits.KeyBitBase):
                _bits[attr] = attr_value
        return _bits

    def __call__(self, **kwargs):
        return self.get_key(**kwargs)

    def get_key(self, view_instance, view_method, request, args, kwargs):
        if self.memoize_for_request:
            memoization_key = self._get_memoization_key(
                view_instance=view_instance,
                view_method=view_method,
                args=args,
                kwargs=kwargs
            )
            if not hasattr(request, '_key_constructor_cache'):
                request._key_constructor_cache = {}
        if self.memoize_for_request and memoization_key in request._key_constructor_cache:
            return request._key_constructor_cache.get(memoization_key)
        else:
            value = self._get_key(
                view_instance=view_instance,
                view_method=view_method,
                request=request,
                args=args,
                kwargs=kwargs
            )
            if self.memoize_for_request:
                request._key_constructor_cache[memoization_key] = value
            return value

    def _get_memoization_key(self, view_instance, view_method, args, kwargs):
        from rest_framework_extensions.utils import get_unique_method_id
        return json.dumps({
            'unique_method_id': get_unique_method_id(view_instance=view_instance, view_method=view_method),
            'args': args,
            'kwargs': kwargs,
            'instance_id': id(self)
        })

    def _get_key(self, view_instance, view_method, request, args, kwargs):
        _kwargs = {
            'view_instance': view_instance,
            'view_method': view_method,
            'request': request,
            'args': args,
            'kwargs': kwargs,
        }
        return self.prepare_key(
            self.get_data_from_bits(**_kwargs)
        )

    def prepare_key(self, key_dict):
        return hashlib.md5(json.dumps(key_dict, sort_keys=True).encode('utf-8')).hexdigest()

    def get_data_from_bits(self, **kwargs):
        result_dict = {}
        for bit_name, bit_instance in self.bits.items():
            if bit_name in self.params:
                params = self.params[bit_name]
            else:
                try:
                    params = bit_instance.params
                except AttributeError:
                    params = None
            result_dict[bit_name] = bit_instance.get_data(
                params=params, **kwargs)
        return result_dict


class DefaultKeyConstructor(KeyConstructor):
    unique_method_id = bits.UniqueMethodIdKeyBit()
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()


class DefaultObjectKeyConstructor(DefaultKeyConstructor):
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()


class DefaultListKeyConstructor(DefaultKeyConstructor):
    list_sql_query = bits.ListSqlQueryKeyBit()
    pagination = bits.PaginationKeyBit()


class DefaultAPIModelInstanceKeyConstructor(KeyConstructor):
    """
    Use this constructor when the values of the model instance are required
    to identify the resource.
    """
    retrieve_model_values = bits.RetrieveModelKeyBit()


class DefaultAPIModelListKeyConstructor(KeyConstructor):
    """
    Use this constructor when the values of the model instance are required
    to identify many resources.
    """
    list_model_values = bits.ListModelKeyBit()
