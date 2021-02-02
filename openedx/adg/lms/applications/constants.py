"""
Constants related to applications.
"""
from collections import namedtuple
from datetime import datetime

from django.utils.translation import ugettext_lazy as _

MINIMUM_YEAR_OPTION = 1900
MAXIMUM_YEAR_OPTION = datetime.today().year
LOGO_IMAGE_MAX_SIZE = 200 * 1024
ALLOWED_LOGO_EXTENSIONS = ('png', 'jpg', 'svg')
MAXIMUM_AGE_LIMIT = 60
MINIMUM_AGE_LIMIT = 21
RESUME_FILE_MAX_SIZE = 4 * 1024 * 1024

# Fieldset titles for application review admin page

APPLICANT_INFO = _('APPLICANT INFORMATION')

RESUME_AND_COVER_LETTER = _('RESUME & COVER LETTER')
RESUME_ONLY = _('RESUME')
COVER_LETTER_ONLY = _('COVER LETTER')

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
RESUME = 'resume'
COVER_LETTER_FILE = 'cover_letter_file'
COVER_LETTER_FILE_DISPLAY = 'cover_letter_file_display'
RESUME_DISPLAY = 'resume_display'
COVER_LETTER_TEXT = 'cover_letter'
PREREQUISITES = 'prerequisites'

APPLICATION_RECEPTION_DATE_FORMAT = ''

# Application listing page titles

ALL_APPLICATIONS_TITLE = _('APPLICATIONS')
OPEN_APPLICATIONS_TITLE = _('OPEN APPLICATIONS')
WAITLISTED_APPLICATIONS_TITLE = _('WAITLISTED APPLICATIONS')
ACCEPTED_APPLICATIONS_TITLE = _('ACCEPTED APPLICATIONS')

STATUS_PARAM = 'status__exact'

EMAIL_ADDRESS_HTML_FORMAT = '<a href="mailto:{email_address}">{email_address}</a>'
LINKED_IN_PROFILE_HTML_FORMAT = '<a href={url}>{url}</a>'

GENDER_MAP = {
    'm': _('Man'),
    'f': _('Woman'),
    'o': _('Prefer not to answer')
}

DAY_MONTH_YEAR_FORMAT = '%d %B %Y'
MONTH_NAME_DAY_YEAR_FORMAT = '%B %d, %Y'

CourseScore = namedtuple('CourseScore', 'course_name course_percentage')

APPLICATION_REVIEW_ERROR_MSG = _('Please make a decision before submitting.')

HTML_FOR_EMBEDDED_FILE_VIEW = '<iframe src="{path_to_file}" style="width:889px; height:393px;"></iframe>'
