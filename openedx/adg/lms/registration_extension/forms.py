"""
Forms for custom registration form app.
"""
from django.forms import ModelChoiceField, ModelForm
from django.utils.translation import ugettext as _

from common.djangoapps.edxmako.shortcuts import marketing_link
from openedx.adg.lms.applications.models import BusinessLine
from openedx.adg.lms.registration_extension.constants import CITIES, REQUIRED_FIELD_CITY_MSG, REQUIRED_FIELD_COMPANY_MSG
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_authn.views.registration_form import \
    RegistrationFormFactory as CoreRegistrationFormFactory
from openedx.core.djangolib.markup import HTML, Text


class RegistrationFormFactory(CoreRegistrationFormFactory):
    """
    Overridden openedx RegistrationFormFactory to avoid core changes.
    """

    DEFAULT_FIELDS = ['name', 'email', 'username', 'password']
    EXTRA_FIELDS = CoreRegistrationFormFactory.EXTRA_FIELDS + ['is_adg_employee']

    def _add_is_adg_employee_field(self, form_desc, required=False):
        """
        Add an is adg employee checkbox field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """

        is_adg_employee_label = _(u'I am a current Al-Dabbagh Group employee.')
        form_desc.add_field(
            'is_adg_employee',
            label=is_adg_employee_label,
            required=required,
            default=False,
            field_type='checkbox'
        )

    def _add_city_field(self, form_desc, required=True):
        """
        Add a city field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """

        # Translators: This label appears above a field on the registration form
        # which allows the user to input the city in which they live.
        city_label = _(u'City')

        form_desc.add_field(
            'city',
            label=city_label,
            field_type='select',
            options=CITIES['KSA'],
            include_default_option=True,
            required=required,
            error_messages={
                'required': REQUIRED_FIELD_CITY_MSG
            }
        )

    def _add_username_field(self, form_desc, required=True):
        """
        Add a username field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """

        # Translators: This label appears above a field on the registration form
        # meant to hold the user's public username.
        username_label = _(u'Username')

        username_instructions = _(
            # Translators: These instructions appear on the registration form, immediately
            # below a field meant to hold the user's public username.
            u'The name that will identify you in your courses. '
            u'It cannot be changed later.'
        )
        form_desc.add_field(
            'username',
            label=username_label,
            instructions=username_instructions,
            restrictions={
                'min_length': accounts.USERNAME_MIN_LENGTH,
                'max_length': accounts.USERNAME_MAX_LENGTH,
            },
            required=required
        )

    def _add_honor_code_field(self, form_desc, required=True):
        """
        Add an honor code field to a form description.

        Arguments:
            form_desc: A form description

        Keyword Arguments:
            required (bool): Whether this field is required; defaults to True
        """

        # Translators: 'Terms of Service' is a legal document users must agree to
        # in order to register a new account.

        terms_field_label = Text(_("""
        By continuing, you confirm that you are at least 16 years of age and agree to
        Al-Dabbagh Group’s {terms_of_service_link_start}{terms_of_service}{terms_of_service_link_end}.
        """)).format(
            terms_of_service=_(u'Terms of Use'),
            terms_of_service_link_start=HTML(u'<a href="{terms_url}" rel="noopener" target="_blank">').format(
                terms_url=marketing_link('HONOR')
            ),
            terms_of_service_link_end=HTML('</a>')
        )

        form_desc.add_field(
            'honor_code',
            label=terms_field_label,
            field_type='plaintext',
            default=False,
            required=required
        )


class ExtendedProfileForm(ModelForm):
    """
    Form for adg extended user profile.
    """
    company = ModelChoiceField(
        queryset=BusinessLine.objects.all(),
        to_field_name='title',
        label=_(u'Al-Dabbagh Group Company'),
        required=False,
        error_messages={
            'required': REQUIRED_FIELD_COMPANY_MSG
        }
    )

    class Meta(object):
        model = ExtendedUserProfile
        fields = ('company',)
