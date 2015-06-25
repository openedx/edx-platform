"""
keyword_substitution.py

Contains utility functions to help substitute keywords in a text body with
the appropriate user / course data.

Supported:
    LMS and CMS (email on enrollment):
        - %%USER_ID%% => anonymous user id
        - %%USER_FULLNAME%% => User's full name
        - %%COURSE_DISPLAY_NAME%% => display name of the course
        - %%COURSE_ID%% => course identifier
        - %%COURSE_START_DATE%% => start date of the course
        - %%COURSE_END_DATE%% => end date of the course

Usage:
    Call substitute_keywords_with_data where substitution is
    needed. Currently called in:
        - LMS:
            - Bulk email
            - emails on enrollment
            - course announcements
            - HTML components
        - CMS:
            - Test emails on enrollment
"""

from collections import namedtuple

from django.contrib.auth.models import User
from student.models import anonymous_id_for_user
from date_utils import get_default_time_display

Keyword = namedtuple('Keyword', 'func desc')

# do this lazily to avoid unneeded database hits
KEYWORD_FUNCTION_MAP = {
    '%%USER_ID%%': Keyword(
        lambda context: anonymous_id_from_user_id(context.get('user_id')),
        'anonymous_user_id (for use in survey links)'
    ),
    '%%USER_FULLNAME%%': Keyword(
        lambda context: context.get('name'),
        'user profile name'
    ),
    '%%COURSE_DISPLAY_NAME%%': Keyword(
        lambda context: context.get('course_title'),
        'display name of the course'
    ),
    '%%COURSE_ID%%': Keyword(
        lambda context: unicode(context.get('course_id')),
        'course identifier'
    ),
    '%%COURSE_START_DATE%%': Keyword(
        lambda context: get_default_time_display(context.get('course_start_date')),
        'start date of the course'
    ),
    '%%COURSE_END_DATE%%': Keyword(
        lambda context: get_default_time_display(context.get('course_end_date')),
        'end date of the course'
    ),
}


def get_keywords_supported():
    """
    Returns supported keywords as a list of dicts with name and description
    """
    return [
        {
            'name': keyword,
            'desc': value.desc,
        }
        for keyword, value in KEYWORD_FUNCTION_MAP.iteritems()
    ]


def anonymous_id_from_user_id(user_id):
    """
    Gets a user's anonymous id from their user id
    """
    user = User.objects.get(id=user_id)
    return anonymous_id_for_user(user, None)


def substitute_keywords(string, context):
    """
    Replaces all %%-encoded words using KEYWORD_FUNCTION_MAP mapping functions

    Iterates through all keywords that must be substituted and replaces
    them by calling the corresponding functions stored in KEYWORD_FUNCTION_MAP.

    Functions stored in KEYWORD_FUNCTION_MAP must return a replacement string.
    """
    for key in KEYWORD_FUNCTION_MAP.keys():
        if key in string:
            substitutor = KEYWORD_FUNCTION_MAP[key].func
            string = string.replace(key, substitutor(context))

    return string


def substitute_keywords_with_data(string, context):
    """
    Given an email context, replaces all %%-encoded words in the given string
    `context` is a dictionary that should include `user_id`, `name`, `course_title`,
    `course_id`, `course_start_date`, and `course_end_date` keys
    """

    # Do not proceed without parameters: Compatibility check with existing tests
    # that do not supply these parameters
    user_id = context.get('user_id')
    course_title = context.get('course_title')

    if user_id is None or course_title is None:
        return string

    return substitute_keywords(string, context)
