"""
Field Descriptions
"""
from django.conf import settings
from django.utils.translation import gettext as _

from common.djangoapps.student.models import UserProfile
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api import accounts
from openedx.core.djangoapps.user_authn.api.constants import SUPPORTED_FIELDS_TYPES


def _add_field_with_configurable_select_options(field_name, field_label, error_message=''):
    """
    Returns a field description
        If select options are given for this field in EXTRA_FIELD_OPTIONS, it
        will be a select type otherwise it will be a text type.
    """
    field_attributes = {
        'name': field_name,
        'label': field_label,
        'error_message': error_message,
    }
    extra_field_options = configuration_helpers.get_value('EXTRA_FIELD_OPTIONS')
    if extra_field_options is None or extra_field_options.get(field_name) is None:
        field_attributes.update({
            'type': SUPPORTED_FIELDS_TYPES['TEXT'],
        })
    else:
        field_options = extra_field_options.get(field_name)
        options = [(str(option.lower()), option) for option in field_options]
        field_attributes.update({
            'type': SUPPORTED_FIELDS_TYPES['SELECT'],
            'options': options
        })

    return field_attributes


def add_level_of_education_field():
    """
    Returns the level of education field description
    """
    # Translators: This label appears above a dropdown menu used to select
    # the user's highest completed level of education.
    education_level_label = _("Highest level of education completed")

    # pylint: disable=translation-of-non-string
    options = [(name, _(label)) for name, label in UserProfile.LEVEL_OF_EDUCATION_CHOICES]

    if settings.ENABLE_COPPA_COMPLIANCE:
        options = list(filter(lambda op: op[0] != 'el', options))

    return {
        'name': 'level_of_education',
        'type': SUPPORTED_FIELDS_TYPES['SELECT'],
        'label': education_level_label,
        'error_message': accounts.REQUIRED_FIELD_LEVEL_OF_EDUCATION_MSG,
        'options': options,
    }


def add_gender_field():
    """
    Returns the gender field description
    """
    # Translators: This label appears above a dropdown menu used to select
    # the user's gender.
    gender_label = _("Gender")

    # pylint: disable=translation-of-non-string
    options = [(name, _(label)) for name, label in UserProfile.GENDER_CHOICES]
    return {
        'name': 'gender',
        'type': SUPPORTED_FIELDS_TYPES['SELECT'],
        'label': gender_label,
        'error_message': accounts.REQUIRED_FIELD_GENDER_MSG,
        'options': options,
    }


def add_year_of_birth_field():
    """
    Returns the year of birth field description
    """
    # Translators: This label appears above a dropdown menu on the form
    # used to select the user's year of birth.
    year_of_birth_label = _("Year of birth")

    options = [(str(year), str(year)) for year in UserProfile.VALID_YEARS]
    return {
        'name': 'year_of_birth',
        'type': SUPPORTED_FIELDS_TYPES['SELECT'],
        'label': year_of_birth_label,
        'error_message': accounts.REQUIRED_FIELD_YEAR_OF_BIRTH_MSG,
        'options': options,
    }


def add_goals_field():
    """
    Returns the goals field description
    """
    # Translators: This phrase appears above a field meant to hold
    # the user's reasons for registering with edX.
    goals_label = _("Tell us why you're interested in {platform_name}").format(
        platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME)
    )

    return {
        'name': 'goals',
        'type': SUPPORTED_FIELDS_TYPES['TEXTAREA'],
        'label': goals_label,
        'error_message': accounts.REQUIRED_FIELD_GOALS_MSG,
    }


def add_profession_field():
    """
    Returns the profession field description
    """
    # Translators: This label appears above a dropdown menu to select
    # the user's profession
    profession_label = _("Profession")
    return _add_field_with_configurable_select_options('profession', profession_label)


def add_specialty_field():
    """
    Returns the user speciality field description
    """
    # Translators: This label appears above a dropdown menu to select
    # the user's specialty
    specialty_label = _("Specialty")
    return _add_field_with_configurable_select_options('specialty', specialty_label)


def add_company_field():
    """
    Returns the company field descriptions
    """
    # Translators: This label appears above a field which allows the
    # user to input the Company
    company_label = _("Company")
    return _add_field_with_configurable_select_options('company', company_label)


def add_title_field():
    """
    Returns the title field description
    """
    # Translators: This label appears above a field which allows the
    # user to input the Title
    title_label = _("Title")
    return _add_field_with_configurable_select_options('title', title_label)


def add_job_title_field():
    """
    Returns the title field description
    """
    # Translators: This label appears above a field which allows the
    # user to input the Job Title
    job_title_label = _("Job Title")
    return _add_field_with_configurable_select_options('job_title', job_title_label)
