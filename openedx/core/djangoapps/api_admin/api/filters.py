"""
Filters for api_admin api
"""


from rest_framework import filters


class IsOwnerOrStaffFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows users to see their own objects or all objects if it is staff user.
    """
    def filter_queryset(self, request, queryset, view):
        if request.user.is_staff:
            return queryset
        else:
            return queryset.filter(user=request.user)
