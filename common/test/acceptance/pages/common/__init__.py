import os

# Get the URL of the instance under test
BASE_URL = os.environ.get('test_url', 'http://localhost:8003')

# The URL used for user auth in testing
AUTH_BASE_URL = os.environ.get('test_url', 'http://localhost:8031')
