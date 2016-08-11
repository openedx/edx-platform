"""
Voucher Forms.
"""

from django import forms
from django.core.validators import RegexValidator


VOUCHER_CODE_PATTERN = r'[A-Z0-9]{10}'


class ValidationForm(forms.Form):
    """
    Form is used to validate the given voucher.
    """
    code = forms.CharField(
        label="Code",
        validators=[RegexValidator('^' + VOUCHER_CODE_PATTERN + '$')],
    )
