import re
from django.conf import settings


def can_execute_unsafe_code(course_id):
    # To decide if we can run unsafe code, we check the course id against
    # a list of regexes configured on the server.
    for regex in settings.COURSES_WITH_UNSAFE_CODE:
        if re.match(regex, course_id):
            return True
    return False
