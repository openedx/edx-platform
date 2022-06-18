from django.utils.translation import get_language
from django.db.models.query import EmptyQuerySet
from django.core.exceptions import EmptyResultSet

from django.utils.encoding import force_str

from rest_framework_extensions import compat


class AllArgsMixin:

    def __init__(self, params='*'):
        super().__init__(params)


class KeyBitBase:
    def __init__(self, params=None):
        self.params = params

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        """
        @rtype: dict
        """
        raise NotImplementedError()


class KeyBitDictBase(KeyBitBase):
    """Base class for dict-like source data processing.

    Look at HeadersKeyBit and QueryParamsKeyBit

    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        data = {}

        if params is not None:
            source_dict = self.get_source_dict(
                params=params,
                view_instance=view_instance,
                view_method=view_method,
                request=request,
                args=args,
                kwargs=kwargs
            )

            if params == '*':
                params = source_dict.keys()

            for key in params:
                value = source_dict.get(
                    self.prepare_key_for_value_retrieving(key))
                if value is not None:
                    data[self.prepare_key_for_value_assignment(
                        key)] = force_str(value)

        return data

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        raise NotImplementedError()

    def prepare_key_for_value_retrieving(self, key):
        return key

    def prepare_key_for_value_assignment(self, key):
        return key


class UniqueViewIdKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return '.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__
        ])


class UniqueMethodIdKeyBit(KeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return '.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__,
            view_method.__name__
        ])


class LanguageKeyBit(KeyBitBase):
    """
    Return example:
        'en'

    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return force_str(get_language())


class FormatKeyBit(KeyBitBase):
    """
    Return example for json:
        u'json'

    Return example for html:
        u'html'
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        return force_str(request.accepted_renderer.format)


class UserKeyBit(KeyBitBase):
    """
    Return example for anonymous:
        u'anonymous'

    Return example for authenticated (value is user id):
        u'10'
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            return force_str(self._get_id_from_user(request.user))
        else:
            return 'anonymous'

    def _get_id_from_user(self, user):
        return user.id


class HeadersKeyBit(KeyBitDictBase):
    """
    Return example:
        {'accept-language': u'ru', 'x-geobase-id': '123'}

    """

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.META

    def prepare_key_for_value_retrieving(self, key):
        from rest_framework_extensions.utils import prepare_header_name

        # Accept-Language => http_accept_language
        return prepare_header_name(key.lower())

    def prepare_key_for_value_assignment(self, key):
        return key.lower()  # Accept-Language => accept-language


class RequestMetaKeyBit(KeyBitDictBase):
    """
    Return example:
        {'REMOTE_ADDR': u'127.0.0.2', 'REMOTE_HOST': u'yandex.ru'}

    """

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.META


class QueryParamsKeyBit(AllArgsMixin, KeyBitDictBase):
    """
    Return example:
        {'part': 'Londo', 'callback': 'jquery_callback'}

    """

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return request.GET


class PaginationKeyBit(QueryParamsKeyBit):
    """
    Return example:
        {'page_size': 100, 'page': '1'}

    """
    paginator_attrs = [
        'page_query_param', 'page_size_query_param',
        'limit_query_param', 'offset_query_param',
        'cursor_query_param',
    ]

    def get_data(self, **kwargs):
        kwargs['params'] = []
        paginator = getattr(kwargs['view_instance'], 'paginator', None)

        if paginator:
            for attr in self.paginator_attrs:
                param = getattr(paginator, attr, None)
                if param:
                    kwargs['params'].append(param)

        return super().get_data(**kwargs)


class SqlQueryKeyBitBase(KeyBitBase):
    def _get_queryset_query_string(self, queryset):
        if isinstance(queryset, EmptyQuerySet):
            return None
        else:
            try:
                return force_str(queryset.query.__str__())
            except EmptyResultSet:
                return None


class ModelInstanceKeyBitBase(KeyBitBase):
    """
    Return the actual contents of the query set.
    This class is similar to the `SqlQueryKeyBitBase`.
    """

    def _get_queryset_query_values(self, queryset):
        if isinstance(queryset, EmptyQuerySet) or queryset.count() == 0:
            return None
        else:
            try:
                # run through the instances and collect all values in ordered fashion
                return compat.queryset_to_value_list(force_str(queryset.values_list()))
            except EmptyResultSet:
                return None


class ListSqlQueryKeyBit(SqlQueryKeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        queryset = view_instance.filter_queryset(view_instance.get_queryset())
        return self._get_queryset_query_string(queryset)


class RetrieveSqlQueryKeyBit(SqlQueryKeyBitBase):
    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        lookup_value = view_instance.kwargs[view_instance.lookup_field]
        try:
            queryset = view_instance.filter_queryset(view_instance.get_queryset()).filter(
                **{view_instance.lookup_field: lookup_value}
            )
        except ValueError:
            return None
        else:
            return self._get_queryset_query_string(queryset)


class RetrieveModelKeyBit(ModelInstanceKeyBitBase):
    """
    A key bit reflecting the contents of the model instance.
    Return example:
        u"[(3, False)]"
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        lookup_value = view_instance.kwargs[view_instance.lookup_field]
        try:
            queryset = view_instance.filter_queryset(view_instance.get_queryset()).filter(
                **{view_instance.lookup_field: lookup_value}
            )
        except ValueError:
            return None
        else:
            return self._get_queryset_query_values(queryset)


class ListModelKeyBit(ModelInstanceKeyBitBase):
    """
    A key bit reflecting the contents of a list of model instances.
    Return example:
        u"[(1, True), (2, True), (3, False)]"
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        queryset = view_instance.filter_queryset(view_instance.get_queryset())
        return self._get_queryset_query_values(queryset)


class ArgsKeyBit(AllArgsMixin, KeyBitBase):

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        if params == '*':
            return args
        elif params is not None:
            return [args[i] for i in params]
        else:
            return []


class KwargsKeyBit(AllArgsMixin, KeyBitDictBase):

    def get_source_dict(self, params, view_instance, view_method, request, args, kwargs):
        return kwargs
