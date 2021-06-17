"""
Constants for all the tests.
"""
from datetime import date

from dateutil.relativedelta import relativedelta
from django.urls import reverse

ADMIN_TYPE_SUPER_ADMIN = 'super_admin'
ADMIN_TYPE_ADG_ADMIN = 'adg_admin'

TITLE_BUSINESS_LINE_1 = 'test_business_line1'
TITLE_BUSINESS_LINE_2 = 'test_business_line2'

USERNAME = 'test'
EMAILS = ['test1@example.com', 'test2@example.com']
PASSWORD = 'edx'

NOTE = 'Test note'
LINKED_IN_URL = 'Test LinkedIn URL'

ALL_FIELDSETS = (
    'preliminary_info_fieldset',
    'applicant_info_fieldset',
    'background_question_fieldset',
    'interest_fieldset',
    'scores_fieldset',
)

TEST_INTEREST_IN_BUSINESS = 'Test Interest in Business'
TEST_HEAR_ABOUT_OMNI = 'Test Hear about Omni'
TEST_BACKGROUND_QUESTION = 'Test background question'

TEST_TEXT_INPUT = 'Test '

FORMSET = 'test_formset'

BUSINESS_LINE_INTEREST_REDIRECT_URL = '{register}?next={next}'.format(
    register=reverse('register_user'),
    next=reverse('application_business_line_interest')
)
MOCK_FILE_PATH = 'dummy_file.pdf'

TEST_MESSAGE_FOR_APPLICANT = 'Test message for the applicant'

VALID_USER_BIRTH_DATE_FOR_APPLICATION = date.today() - relativedelta(years=30)

PROGRAM_PRE_REQ = 'program_pre_req'
BUSINESS_LINE_PRE_REQ = 'business_line_pre_req'
