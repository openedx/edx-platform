"""
Constants for all the tests in webinars app
"""
from datetime import datetime

DUMMY_TITLE = "test webinar"
DUMMY_DESCRIPTION = "test webinar description"
DUMMY_START_DATE = datetime.now()
DUMMY_EMAIL_ADDRESSES = ["test1@example.com", "test2@example.com"]
DUMMY_CONTEXT = {
    'webinar_title': DUMMY_TITLE,
    'webinar_description': DUMMY_DESCRIPTION,
    'webinar_start_time': DUMMY_START_DATE.strftime("%B %d, %Y %I:%M %p %Z")
}
