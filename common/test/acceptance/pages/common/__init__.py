"""
Package of common page objects for acceptance tests
"""


import os

HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')
CMS_PORT = os.environ.get('BOK_CHOY_CMS_PORT', 8031)
LMS_PORT = os.environ.get('BOK_CHOY_LMS_PORT', 8003)

# Get the URL of the instance under test
BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(HOSTNAME, LMS_PORT))

# The URL used for user auth in testing
AUTH_BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(HOSTNAME, CMS_PORT))
