"""
Allow Unicode in Admin and LMS.
"""
from django import forms
import re
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

unicode_username_re = re.compile(settings.USERNAME_REGEX, re.UNICODE)

unicode_username_field = forms.RegexField(label=_("Username"),
                                          max_length=30,
                                          regex=unicode_username_re,
                                          help_text=_("Required. 30 characters or fewer. Letters, digits and "
                                                      "@/./+/-/_ only."),
                                          error_messages={
                                              'invalid': _("This value may contain only letters, numbers and"
                                                           " @/./+/-/_ characters.")
                                          })


validate_username = RegexValidator(
    unicode_username_re,
    _("Enter a valid 'username' consisting of letters, numbers, spaces, underscores or hyphens."),
    'invalid'
)
