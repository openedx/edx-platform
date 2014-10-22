"""
Allow Unicode in Admin and LMS.
"""
from django.contrib.auth.admin import UserAdmin
from django import forms
from ratelimitbackend import admin
import re
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

unicode_username_re = re.compile(ur'^[\w .@_+-]+$', re.UNICODE)

unicode_username_field = forms.RegexField(label=_("Username"),
                                          max_length=30,
                                          regex=unicode_username_re,
                                          help_text=_("Required. 30 characters or fewer. Letters, digits and "
                                                      "@/./+/-/_ only."),
                                          error_messages={
                                              'invalid': _("This value may contain only letters, numbers and"
                                                           " @/./+/-/_ characters.")
                                          })


class UnicodeUserCreationForm(UserCreationForm):
    username = unicode_username_field


class UnicodeUserChangeForm(UserChangeForm):
    username = unicode_username_field


class UnicodeUserAdmin(UserAdmin):
    form = UnicodeUserChangeForm
    add_form = UnicodeUserCreationForm


validate_username = RegexValidator(
    unicode_username_re,
    _("Enter a valid 'username' consisting of letters, numbers, spaces, underscores or hyphens."),
    'invalid'
)
