import os

# Get the URL of the Studio instance under test
STUDIO_BASE_URL = os.environ.get('studio_url', 'http://localhost:8031')

# Get the URL of the LMS instance under test
LMS_BASE_URL = os.environ.get('lms_url', 'http://localhost:8003')

# Get the URL of the XQueue stub used in the test
XQUEUE_STUB_URL = os.environ.get('xqueue_url', 'http://localhost:8040')

# Get the URL of the Ora stub used in the test
ORA_STUB_URL = os.environ.get('ora_url', 'http://localhost:8041')

# Get the URL of the comments service stub used in the test
COMMENTS_STUB_URL = os.environ.get('comments_url', 'http://localhost:4567')

# Get the URL of the EdxNotes service stub used in the test
EDXNOTES_STUB_URL = os.environ.get('edxnotes_url', 'http://localhost:8042')

# Get the URL of the EdxNotes service stub used in the test
PROGRAMS_STUB_URL = os.environ.get('programs_url', 'http://localhost:8090')
