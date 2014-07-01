import re
from django.conf import settings


def can_execute_unsafe_code(course_id):
    """
    Determine if this course is allowed to run unsafe code.

    For use from the ModuleStore.  Checks the `course_id` against a list of whitelisted
    regexes.

    Returns a boolean, true if the course can run outside the sandbox.

    """
    # To decide if we can run unsafe code, we check the course id against
    # a list of regexes configured on the server.
    # If this is not defined in the environment variables then default to the most restrictive, which
    # is 'no unsafe courses'
    # TODO: This should be a database configuration, where we can mark individual courses as being
    # safe/unsafe. Someone in the future should switch us over to that rather than using regexes
    # in a settings file
    # To others using this: the code as-is is brittle and likely to be changed in the future,
    # as per the TODO, so please consider carefully before adding more values to COURSES_WITH_UNSAFE_CODE
    for regex in getattr(settings, 'COURSES_WITH_UNSAFE_CODE', []):
        if re.match(regex, unicode(course_id)):
            return True
    return False
