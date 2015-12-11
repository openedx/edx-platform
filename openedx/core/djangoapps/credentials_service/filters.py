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


class ProgramSearchFilterBackend(filters.BaseFilterBackend):
    """
    Depending on the group membership of the requesting user, filter program
    results according to their status:

      - ADMINS can see programs with any status other than 'deleted'
      - LEARNERS can see programs with any status other than 'deleted' or 'unpublished'
    """

    def filter_queryset(self, request, queryset, view):
        #from nose.tools import set_trace; set_trace()
        #program_id = request.__dict__['parser_context']['kwargs']['program_id']
        # from nose.tools import set_trace; set_trace()
        program = queryset.filter(program_id=int(200))
        return UserCredential.objects.filter(
            credential_content_type=ContentType.objects.get_for_model(
                ProgramCertificate
            ),
            credential_id=program[0].id
        )

#
# class ProgramStatusQueryFilterBackend(ProgramStatusRoleFilterBackend):
#     """
#     Allows for filtering programs by their status using a query string argument.
#     """
#     query_parameter = 'username'
#     lookup_filter = 'username'
