"""
Constants for all the tests.
"""
ADMIN_TYPE_SUPER_ADMIN = 'super_admin'
ADMIN_TYPE_ADG_ADMIN = 'adg_admin'

TITLE_BUSINESS_LINE_1 = 'test_business_line1'
TITLE_BUSINESS_LINE_2 = 'test_business_line2'

USERNAME = 'test'
EMAIL = 'test@example.com'
PASSWORD = 'edx'

NOTE = 'Test note'
LINKED_IN_URL = 'Test LinkedIn URL'

ALL_FIELDSETS = (
    'preliminary_info_fieldset', 'applicant_info_fieldset', 'resume_cover_letter_fieldset', 'scores_fieldset'
)

FIELDSETS_WITHOUT_RESUME_OR_COVER_LETTER = (ALL_FIELDSETS[0], ALL_FIELDSETS[1], ALL_FIELDSETS[3])

TEST_RESUME = 'Test Resume'
TEST_COVER_LETTER_FILE = 'Test Cover Letter File'
TEST_COVER_LETTER_TEXT = 'Test Cover Letter Text'

FORMSET = 'test_formset'

TEST_MESSAGE_FOR_APPLICANT = 'Test message for the applicant'
