import os

# Get the URL of the instance under test
STUDIO_BASE_URL = os.environ.get('studio_url', 'http://localhost:8031')

# Get the URL of the XQueue stub used in the test
XQUEUE_STUB_URL = os.environ.get('xqueue_url', 'http://localhost:8040')
