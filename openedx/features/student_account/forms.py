"""
Utility functions for validating custom form
"""
import json

import requests
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from lms.djangoapps.onboarding.models import Organization, OrgSector, TotalEmployee
from student.forms import AccountCreationForm


class AccountCreationFormCustom(AccountCreationForm):
    """
    A custom form for account creation data. It is currently only used for
    validation, not rendering.
    """

    _OPT_IN_REQUIRED_MSG = _('Email opt in is a required field, and can only be set to true or false')

    first_name = forms.CharField(
        required=True
    )

    last_name = forms.CharField(
        required=True
    )

    organization_size = forms.CharField(
        required=False
    )

    organization_type = forms.CharField(
        required=False
    )

    is_organization_registered = forms.CharField(
        required=False
    )

    # field to check if organization is selected from dropdown or not
    is_org_selected = forms.BooleanField(
        required=False
    )

    organization_name = forms.CharField(
        max_length=255,
        required=False
    )

    opt_in = forms.CharField(
        error_messages={
            'required': _OPT_IN_REQUIRED_MSG,
        }
    )

    recaptcha = forms.CharField(
        required=True
    )

    def __init__(self, data=None, extended_profile_fields=None, do_third_party_auth=True):
        super(AccountCreationFormCustom, self).__init__(data, tos_required=False)
        self.extended_profile_fields = extended_profile_fields or {}
        self.do_third_party_auth = do_third_party_auth

    def clean_opt_in(self):
        """
        Verifies a opt_in is valid only either 'yes', or 'no',
        raises a ValidationError otherwise.
        """
        cleaned_opt_in = self.cleaned_data.get('opt_in')
        if cleaned_opt_in not in ['yes', 'no']:
            raise forms.ValidationError(_('Invalid email opt in option provided'))
        return cleaned_opt_in

    def clean_organization_name(self):
        """
        Validates organization name
        """
        org_name = self.cleaned_data.get('organization_name')
        is_org_selected = self.cleaned_data.get('is_org_selected')

        if not is_org_selected:
            try:
                Organization.objects.get(label=org_name)
                raise forms.ValidationError(_('Organization already exists, either select existing from list '
                                              'or try a different name'))
            except Organization.DoesNotExist:
                return org_name
        return org_name

    def clean_recaptcha(self):
        """
        Validates recaptcha result
        """
        recaptcha = self.cleaned_data.get('recaptcha')
        response = requests.post(
            settings.CAPTCHA_VERIFY_URL,
            data={
                'secret': settings.CAPTCHA_SECRET_KEY,
                'response': recaptcha
            }).content
        response_json = json.loads(response)

        if not response_json['success']:
            raise forms.ValidationError(_('The reCaptcha response is invalid. Please try again.'))

        return recaptcha

    def clean(self):
        """ Enforce organization related field conditions """
        cleaned_org_name = self.cleaned_data.get('organization_name')
        cleaned_org_size = self.cleaned_data.get('organization_size')
        cleaned_org_type = self.cleaned_data.get('organization_type')
        cleaned_is_organization_registered = self.cleaned_data.get('is_organization_registered')

        valid_org_type = OrgSector.objects.filter(code=cleaned_org_type).exists()
        valid_org_size = TotalEmployee.objects.filter(code=cleaned_org_size).exists()

        if cleaned_org_type and not valid_org_type:
            self.errors.update({'organization_type': [_('Invalid organization type option provided'), ]})

        if cleaned_org_size and not valid_org_size:
            self.errors.update({'organization_size': [_('Invalid organization size option provided'), ]})

        if (
            cleaned_is_organization_registered and
            cleaned_is_organization_registered not in ['No', 'Yes', 'I don\'t Know']
        ):
            self.errors.update({'is_organization_registered': [_('Invalid option provided'), ]})

        # User is affiliated with some organization
        if cleaned_org_name:
            # Check if organization already exists and does have a size populated
            existing_org = Organization.objects.filter(label=cleaned_org_name).first()

            if existing_org:
                existing_org_size = existing_org.total_employees
                existing_org_type = existing_org.org_type
                if not existing_org_size and not cleaned_org_size:
                    self.errors.update({'organization_size': [_('Organization size not provided.'), ]})
                elif existing_org_size and cleaned_org_size:
                    self.errors.update(
                        {'organization_size': [_('Organization size provided for existing organization'), ]}
                    )

                if not existing_org_type and not cleaned_org_type:
                    self.errors.update({'organization_type': [_('Organization type not provided.'), ]})
                elif existing_org_type and cleaned_org_type:
                    self.errors.update(
                        {'organization_type': [_('Organization type provided for existing organization'), ]}
                    )

            else:
                if not cleaned_org_size:
                    self.errors.update(
                        {'organization_size': [_('Organization size not provided for new organization'), ]}
                    )
                if not cleaned_org_type:
                    self.errors.update(
                        {'organization_type': [_('Organization type not provided for new organization'), ]}
                    )
                if not cleaned_is_organization_registered:
                    self.errors.update(
                        {'is_organization_registered': ['Organization registration not provided for new organization', ]}
                    )

        return self.cleaned_data
