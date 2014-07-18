from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore

"""
keyword_substitution.py

Contains utility functions to help substitute keywords in a text body with
the appropriate user / course data.

Supported:
    LMS:
        - %%USER_ID%% => anonymous user id
        - %%USER_FULLNAME%% => User's full name
        - %%COURSE_DISPLAY_NAME%% => display name of the course
        - %%COURSE_END_DATE%% => end date of the course

Usage:
    KEYWORD_FUNCTION_MAP must be supplied in startup.py, so that it lives
    above other modules in the dependency tree and acts like a global var.
    Then we can call substitute_keywords_with_data where substitution is
    needed. Currently called in:
        - LMS: Announcements + Bulk emails
        - CMS: Not called
"""

KEYWORD_FUNCTION_MAP = {}

def add_keyword_function_map(mapping):
    """
    Attaches the given keyword-function map to the existing one
    """
    KEYWORD_FUNCTION_MAP.update(mapping)

def add_keyword_function_pair(keyword, func):
    """
    Attach one keyword, func pair to the map
    """
    KEYWORD_FUNCTION_MAP[keyword] = func

def substitute_keywords_with_data(string, user_id=None, course_id=None):
    """
    Iterates through all keywords that must be substituted and replaces
    them by calling the corresponding functions stored in KEYWORD_FUNCTION_MAP.

    Function stored in KEYWORD_FUNCTION_MAP must return a string to replace with.
    Also, functions imported from other modules must be wrapped around in a
    new function if they don't take in user_id and course_id. This is to simplify
    the forloop below, and eliminate the possibility of unnecessarily piling up
    if elif else statements when the keyword pool grows.
    """

    # Do not proceed without parameters: Compatibility check with existing tests
    # That do not supply these parameters
    if user_id is None or course_id is None:
        return string

    # Memoize user objects
    user = User.objects.get(id=user_id)
    course = modulestore().get_course(course_id, depth=0)

    for key, func in KEYWORD_FUNCTION_MAP.iteritems():
        if key in string:
            substitutor = func(user, course)
            string = string.replace(key, substitutor)

    return string
