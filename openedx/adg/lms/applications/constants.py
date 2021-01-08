"""
Constants related to applications.
"""
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
