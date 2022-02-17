"""
Optional Fields API used by Authn MFE to populate progressive profiling form
"""
import copy

from django.conf import settings
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.api import form_fields
from openedx.core.lib.api.authentication import BearerAuthentication


class OptionalFieldsThrottle(UserRateThrottle):
    """
    Setting rate limit for OptionalFieldsData API
    """
    rate = settings.OPTIONAL_FIELD_API_RATELIMIT


class OptionalFieldsView(APIView):
    """
    Construct Registration forms and associated fields.
    """
    throttle_classes = [OptionalFieldsThrottle]
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    EXTRA_FIELDS = [
        'confirm_email',
        'first_name',
        'last_name',
        'city',
        'state',
        'country',
        'gender',
        'year_of_birth',
        'level_of_education',
        'company',
        'job_title',
        'title',
        'mailing_address',
        'goals',
        'honor_code',
        'terms_of_service',
        'profession',
        'specialty',
        'marketing_emails_opt_in',
    ]

    def _get_field_order(self):
        """
        Returns the order in which fields must appear on registration form
        """
        field_order = configuration_helpers.get_value('REGISTRATION_FIELD_ORDER')
        if not field_order:
            field_order = settings.REGISTRATION_FIELD_ORDER or self.EXTRA_FIELDS

        # Check that all of the EXTRA_FIELDS are in the field order and vice versa,
        # if not append missing fields at end of field order
        if set(self.EXTRA_FIELDS) != set(field_order):
            difference = set(self.EXTRA_FIELDS).difference(set(field_order))
            # sort the additional fields so we have could have a deterministic result
            # when presenting them
            field_order.extend(sorted(difference))

        return field_order

    def __init__(self):
        super().__init__()
        self._fields_setting = copy.deepcopy(configuration_helpers.get_value('REGISTRATION_EXTRA_FIELDS'))
        if not self._fields_setting:
            self._fields_setting = copy.deepcopy(settings.REGISTRATION_EXTRA_FIELDS)

        ordered_extra_fields = self._get_field_order()

        if settings.ENABLE_COPPA_COMPLIANCE and 'year_of_birth' in ordered_extra_fields:
            ordered_extra_fields.remove('year_of_birth')

        self.valid_fields = [field for field in ordered_extra_fields if self._fields_setting.get(field) == 'optional']

    def get(self, request):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns the optional fields configured in REGISTRATION_EXTRA_FIELDS settings.
        """
        response = {}
        for field in self.valid_fields:
            field_handler = getattr(form_fields, f'add_{field}_field', None)
            if field_handler:
                response[field] = field_handler()

        if not self.valid_fields or not response:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error_code': 'optional_fields_configured_incorrectly'}
            )

        return Response(
            status=status.HTTP_200_OK,
            data={
                'fields': response,
                'extended_profile': configuration_helpers.get_value('extended_profile_fields', []),
            },
        )
