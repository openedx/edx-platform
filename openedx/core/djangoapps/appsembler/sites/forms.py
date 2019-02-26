"""
Appsembler Sites Views.
"""
from django import forms


class MakeAMCAdminForm(forms.Form):
    organization_name = forms.CharField(
        required=True,
        help_text='The name or short name of the organization',
    )
