"""
Constants related to applications.
"""

# TODO: Convert all these constants into a dictionary

from collections import namedtuple
from datetime import datetime

from django.utils.translation import gettext_lazy as _

MINIMUM_YEAR_OPTION = 1900
MAXIMUM_YEAR_OPTION = datetime.today().year
LOGO_IMAGE_MAX_SIZE = 200 * 1024
ALLOWED_LOGO_EXTENSIONS = ('png', 'jpg', 'svg')
MAXIMUM_AGE_LIMIT = 65
MINIMUM_AGE_LIMIT = 18
FILE_MAX_SIZE = 4 * 1024 * 1024

# Fieldset titles for application review admin page

APPLICANT_INFO = _('APPLICANT INFORMATION')

INTEREST = _('INTEREST IN BUSINESS LINE')

SCORES = _('SCORES')

# Fieldnames for application review fields

EMAIL = 'email'
LOCATION = 'location'
LINKED_IN_PROFILE = 'linked_in_profile'
IS_SAUDI_NATIONAL = 'is_saudi_national'
GENDER = 'gender'
PHONE_NUMBER = 'phone_number'
DATE_OF_BIRTH = 'date_of_birth'
ORGANIZATION = 'organization'
APPLYING_TO = 'applying_to'
INTEREST_IN_BUSINESS = 'interest_in_business'
PREREQUISITES = 'prerequisites'

# Application listing page titles

ALL_APPLICATIONS_TITLE = _('APPLICATIONS')
OPEN_APPLICATIONS_TITLE = _('OPEN APPLICATIONS')
WAITLISTED_APPLICATIONS_TITLE = _('WAITLISTED APPLICATIONS')
ACCEPTED_APPLICATIONS_TITLE = _('ACCEPTED APPLICATIONS')

STATUS_PARAM = 'status__exact'

EMAIL_ADDRESS_HTML_FORMAT = '<a href="mailto:{email_address}">{email_address}</a>'
LINKED_IN_PROFILE_HTML_FORMAT = '<a href={url}>{url}</a>'

GENDER_MAP = {
    'm': _('Male'),
    'f': _('Female'),
    'o': _('Prefer not to answer')
}

DAY_MONTH_YEAR_FORMAT = '%d %B %Y'
MONTH_NAME_DAY_YEAR_FORMAT = '%B %d, %Y'

CourseScore = namedtuple('CourseScore', 'course_name course_percentage')

APPLICATION_REVIEW_ERROR_MSG = _('Please make a decision before submitting.')

ADG_ADMIN_GROUP_NAME = 'ADG Admins'

COURSE_GROUP_PREREQ_VALIDATION_ERROR = _(
    'A Course Group can either be a prerequisite for the program, a specific business line or common for all business '
    'lines'
)

MAX_NUMBER_OF_WORDS_ALLOWED_IN_TEXT_INPUT = 200
