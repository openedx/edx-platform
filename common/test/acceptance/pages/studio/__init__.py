import os

# Get the URL of the instance under test
HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')
CMS_PORT = os.environ.get('BOK_CHOY_CMS_PORT', 8031)
BASE_URL = os.environ.get('test_url', 'http://{}:{}'.format(HOSTNAME, CMS_PORT))
