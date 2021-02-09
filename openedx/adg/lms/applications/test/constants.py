"""
Constants for all the tests.
"""
from django.urls import reverse


USERNAME = 'test'
EMAIL = 'test@example.com'
PASSWORD = 'edx'
COVER_LETTER_REDIRECT_URL = '{register}?next={next}'.format(
    register=reverse('register_user'),
    next=reverse('application_cover_letter')
)
MOCK_FILE_PATH = 'dummy_file.pdf'
