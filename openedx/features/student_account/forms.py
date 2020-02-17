"""
Utility functions for validating custom form
"""
from django import forms
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

    org_size = forms.CharField(
        required=False
    )

    org_type = forms.CharField(
        required=False
    )

    org_name = forms.CharField(
        max_length=255,
        required=False
    )

    opt_in = forms.CharField(
        error_messages={
            'required': _OPT_IN_REQUIRED_MSG,
        }
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

    def clean(self):
        """ Enforce organization related field conditions """
        cleaned_org_name = self.cleaned_data.get('org_name')
        cleaned_org_size = self.cleaned_data.get('org_size')
        cleaned_org_type = self.cleaned_data.get('org_type')

        valid_org_type = OrgSector.objects.filter(code=cleaned_org_type).exists()
        valid_org_size = TotalEmployee.objects.filter(code=cleaned_org_size).exists()

        if cleaned_org_type and not valid_org_type:
            self.errors.update({'org_type': [_('Invalid organization type option provided'), ]})

        if cleaned_org_size and not valid_org_size:
            self.errors.update({'org_size': [_('Invalid organization size option provided'), ]})

        # User is affiliated with some organization
        if cleaned_org_name:
            # Check if organization already exists and does have a size populated
            existing_org = Organization.objects.filter(label=cleaned_org_name).first()

            if existing_org:
                existing_org_size = existing_org.total_employees
                existing_org_type = existing_org.org_type
                if not existing_org_size and not cleaned_org_size:
                    self.errors.update({'org_size': [_('Organization size not provided.'), ]})
                elif existing_org_size and cleaned_org_size:
                    self.errors.update({'org_size': [_('Organization size provided for existing organization'), ]})

                if not existing_org_type and not cleaned_org_type:
                    self.errors.update({'org_type': [_('Organization type not provided.'), ]})
                elif existing_org_type and cleaned_org_type:
                    self.errors.update({'org_type': [_('Organization type provided for existing organization'), ]})

            else:
                if not cleaned_org_size:
                    self.errors.update({'org_size': [_('Organization size not provided for new organization'), ]})
                if not cleaned_org_type:
                    self.errors.update({'org_type': [_('Organization type not provided for new organization'), ]})

        return self.cleaned_data

