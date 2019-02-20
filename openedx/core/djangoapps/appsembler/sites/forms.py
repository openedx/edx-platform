"""
Appsembler Sites Views.
"""
from django import forms
from openedx.core.djangoapps.appsembler.sites.utils import make_amc_admin, reset_tokens


class MakeAMCAdminForm(forms.Form):