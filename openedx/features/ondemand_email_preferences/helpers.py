"""
Helper functions for ondemand_email_preferences app
"""
from datetime import datetime

from crum import get_current_request
from django.conf import settings
from django.core.urlresolvers import reverse
from pytz import utc

from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.module_render import toc_for_course
from openedx.features.course_card.helpers import get_course_open_date
from openedx.features.ondemand_email_preferences.utils import get_next_date

DEFAULT_DAYS_MODULE_COMPLETION = 7
ON_DEMAND_MODULE_TEXT = "<li> {module_name}: Complete by {module_comp_date}</li>"


def get_chapters_text(course_id, user):
    """
    Returns module name and suggested completion date for that module in `ON_DEMAND_MODULE_TEXT` format.

    Arguments:
        course_id (string): Id of the course
        user (User): Django User object

    Returns:
        string: String in `ON_DEMAND_MODULE_TEXT` format that contains module name and suggested completion date.
    """
    course = get_course_with_access(user, 'load', course_id, depth=2)
    # We don't need 'chapter_url_name', 'section_url_name' and 'field_
    # data_cache' to get list of modules so we passing None for these arguments.
    table_of_contents = toc_for_course(user, get_current_request(), course, None, None, None, )

    today = datetime.now(utc).date()
    course_start_date = get_course_open_date(course).date()
    delta_date = today - course_start_date

    if delta_date.days > 0:
        course_start_date = today

    chapters_text = ''
    module_comp_days = DEFAULT_DAYS_MODULE_COMPLETION
    for chapter in table_of_contents['chapters']:
        module_text = ON_DEMAND_MODULE_TEXT.format(
            module_name=chapter['display_name'],
            module_comp_date=get_next_date(course_start_date, module_comp_days)
        )
        chapters_text = chapters_text + module_text
        module_comp_days = module_comp_days + DEFAULT_DAYS_MODULE_COMPLETION
    return chapters_text


def get_my_account_link(course_id):
    """
    Append a course id with the link to user account settings and return it.

    Arguments:
        course_id (string): Id of the course

    Returns:
        string: User account settings link in string format.
    """
    my_account_url = reverse('update_account_settings')
    url_target = '{my_account_url}?course_id={course_id}'.format(my_account_url=my_account_url, course_id=course_id)
    base_url = settings.LMS_ROOT_URL
    return base_url + url_target
