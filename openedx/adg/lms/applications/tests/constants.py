"""
Constants for all the tests.
"""
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
