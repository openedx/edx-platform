from django_filters import rest_framework as filters

from entitlements.models import CourseEntitlement


class CharListFilter(filters.CharFilter):
    """ Filters a field via a comma-delimited list of values. """

    def filter(self, qs, value):  # pylint: disable=method-hidden
        if value not in (None, ''):
            value = value.split(',')

        return super(CharListFilter, self).filter(qs, value)


class UUIDListFilter(CharListFilter):
    """ Filters a field via a comma-delimited list of UUIDs. """

    def __init__(self, name='uuid', label=None, widget=None, method=None, lookup_expr='in', required=False,
                 distinct=False, exclude=False, **kwargs):
        super(UUIDListFilter, self).__init__(
            name=name,
            label=label,
            widget=widget,
            method=method,
            lookup_expr=lookup_expr,
            required=required,
            distinct=distinct,
            exclude=exclude,
            **kwargs
        )


class CourseEntitlementFilter(filters.FilterSet):

    uuid = UUIDListFilter()
    user = filters.CharFilter(name='user__username')

    class Meta:
        model = CourseEntitlement
        fields = ('uuid', 'user')
