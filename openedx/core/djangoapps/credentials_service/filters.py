"""
Reusable queryset filters for the REST API.
"""
from rest_framework import filters

from django.contrib.contenttypes.models import ContentType
from openedx.core.djangoapps.credentials_service.models import ProgramCertificate, UserCredential


class BaseQueryFilterBackend(filters.BaseFilterBackend):
    """
    A reusable base class for filtering querysets based on a GET parameter.
    """
    query_parameter = None  # specify the query parameter name.
    lookup_filter = None  # specify the model lookup to filter upon, using the value of the query parameter.


    def filter_queryset(self, request, queryset, view):
        if request.method == 'GET' and self.query_parameter in request.query_params:
            filter_kwargs = {self.lookup_filter: request.query_params[self.query_parameter]}
            return queryset.filter(**filter_kwargs)
        else:
            return queryset

class CredentialStatusQueryFilterBackend(BaseQueryFilterBackend):
    """
    Allows for filtering credentials by their status using a query string argument.
    """
    query_parameter = 'status'
    lookup_filter = 'status'


class CredentialIdQueryFilterBackend(BaseQueryFilterBackend):
    """
    Allows for filtering credentials by their ID using a query string argument.
    """
    query_parameter = 'id'
    lookup_filter = 'id'



