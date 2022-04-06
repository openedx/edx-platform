"""
Registration Fields View used by optional and required fields view.
"""
import copy

from django.conf import settings

from rest_framework.views import APIView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.api import form_fields
from openedx.core.djangoapps.user_authn.views.registration_form import get_registration_extension_form


class RegistrationFieldsContext(APIView):
    """
    Registration Fields View used by optional and required fields view.
    """
    FIELD_TYPE = None

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

        self.valid_fields = [
            field for field in ordered_extra_fields if self._fields_setting.get(field) == self.FIELD_TYPE
        ]

        custom_form = get_registration_extension_form()
        if custom_form:
            for field_name, field in custom_form.fields.items():
                # If the FIELD_TYPE is required make sure the custom field is required in the form and if the
                # FIELD_TYPE is optional only add field if it is not required. This is to make sure field is
                # added only once either on Registration Page or Progressive Profiling page.
                if (
                    field.required and self.FIELD_TYPE == 'required' or
                    not field.required and self.FIELD_TYPE == 'optional'
                ):
                    self.valid_fields.append(field_name)

    def _get_fields(self):
        """
        Returns the required or optional fields configured in REGISTRATION_EXTRA_FIELDS settings.
        """
        # Custom form fields can be added via the form set in settings.REGISTRATION_EXTENSION_FORM
        custom_form = get_registration_extension_form() or {}
        response = {}
        for field in self.valid_fields:
            if custom_form and field in custom_form.fields:
                response[field] = form_fields.add_extension_form_field(
                    field, custom_form, custom_form.fields[field], self.FIELD_TYPE
                )
            else:
                field_handler = getattr(form_fields, f'add_{field}_field', None)
                if field_handler:
                    if field == 'honor_code':
                        terms_of_services = self._fields_setting.get('terms_of_service')
                        if terms_of_services in ['required', 'optional', 'optional-exposed']:
                            response[field] = field_handler(self.FIELD_TYPE == 'required', bool(terms_of_services))
                            continue
                    response[field] = field_handler(self.FIELD_TYPE == 'required')

        return response
