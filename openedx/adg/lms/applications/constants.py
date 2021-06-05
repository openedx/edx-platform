"""
Constants related to applications.
"""
from collections import namedtuple
from datetime import datetime

from django.utils.translation import gettext_lazy as _

MINIMUM_YEAR_OPTION = 1900
MAXIMUM_YEAR_OPTION = datetime.today().year
LOGO_IMAGE_MAX_SIZE = 200 * 1024
ALLOWED_LOGO_EXTENSIONS = ('png', 'jpg', 'svg')
MAXIMUM_AGE_LIMIT = 60
MINIMUM_AGE_LIMIT = 21
FILE_MAX_SIZE = 4 * 1024 * 1024

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

ADG_ADMIN_GROUP_NAME = 'ADG Admins'

COURSE_GROUP_PREREQ_VALIDATION_ERROR = _(
    'A Course Group can either be a prerequisite for the program, a specific business line or common for all business '
    'lines'
)

WRITTEN_APPLICATION_COMPLETION_CONGRATS = _('Congratulations! You have completed the written application.')
WRITTEN_APPLICATION_COMPLETION_MSG = _(
    'Get started on the Omnipreneurship Courses in order to move forward with your application.'
)
WRITTEN_APPLICATION_COMPLETION_INSTRUCTION = _(
    'Finish up the Omnipreneurship Courses in order to complete your application.'
)
PREREQUISITE_COURSES_COMPLETION_CONGRATS = _('Congratulations! You have completed the Omnipreneurship Courses!')
PREREQUISITE_COURSES_COMPLETION_MSG = _(
    'Get started on the Business Line Courses in order to move forward with your application.'
)
PREREQUISITE_COURSES_COMPLETION_INSTRUCTION = _(
    'Finish up the Business Line Courses in order to complete your application.'
)
APPLICATION_SUBMISSION_CONGRATS = _(
    'Congratulations! You have completed all of the requirements and submitted your application. '
)
APPLICATION_SUBMISSION_INSTRUCTION = _(
    'Your application is now under review by an admin. If you are selected for the program, they will be in contact '
    'with you to begin the process of establishing your business. This will involve legal documentation and on-the-job '
    'training. More details regarding this will be provided later. '
)

RETAKE_COURSE_MESSAGE = _(
    'Please take the assessments in this course again in order to obtain a passing grade and complete your application!'
)
LOCKED_COURSE_MESSAGE = _('This course will unlock when you have completed and received a passing grade in')

LOCKED = _('Locked')
NOT_STARTED = _('Not Started')
IN_PROGRESS = _('In Progress')
RETAKE = _('Re-Take Course')
COMPLETED = _('Completed')
