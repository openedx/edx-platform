"""
Envirement Setup for fixtures.
"""


import os

HOSTNAME = os.environ.get('BOK_CHOY_HOSTNAME', 'localhost')
CMS_PORT = os.environ.get('BOK_CHOY_CMS_PORT', '8031')
LMS_PORT = os.environ.get('BOK_CHOY_LMS_PORT', '8003')

# Get the URL of the Studio instance under test
STUDIO_BASE_URL = os.environ.get('studio_url', 'http://{}:{}'.format(HOSTNAME, CMS_PORT))

# Get the URL of the LMS instance under test
LMS_BASE_URL = os.environ.get('lms_url', 'http://{}:{}'.format(HOSTNAME, LMS_PORT))

# Get the URL of the XQueue stub used in the test
XQUEUE_STUB_URL = os.environ.get('xqueue_url', 'http://localhost:8040')

# Get the URL of the Ora stub used in the test
ORA_STUB_URL = os.environ.get('ora_url', 'http://localhost:8041')

# Get the URL of the comments service stub used in the test
COMMENTS_STUB_URL = os.environ.get('comments_url', 'http://{}:4567'.format(HOSTNAME))

# Get the URL of the EdxNotes service stub used in the test
EDXNOTES_STUB_URL = os.environ.get('edxnotes_url', 'http://{}:8042'.format(HOSTNAME))

# Get the URL of the Catalog service stub used in the test
CATALOG_STUB_URL = os.environ.get('catalog_url', 'http://localhost:8091')
