"""
Package of lms page objects for acceptance tests
"""


import os

# Get the URL of the instance under test
HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')
LMS_PORT = os.environ.get('BOK_CHOY_LMS_PORT', 8003)
BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(HOSTNAME, LMS_PORT))
