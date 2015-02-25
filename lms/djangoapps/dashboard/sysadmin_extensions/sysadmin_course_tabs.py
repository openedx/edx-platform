"""Helper module that processes edit_course_tabs requests"""
from django.utils.translation import ugettext as _

from courseware.courses import get_course_by_id
from opaque_keys.edx import locator
from opaque_keys import InvalidKeyError
from xmodule.tabs import primitive_insert, primitive_delete
from xmodule.tabs import InvalidTabsException


def process_request(action, request):
    """Routes requests to the appropriate helper function"""

    course_id = request.POST.get('course_id', '').strip()
    if action == 'get_current_tabs':
        title = _('Current Tabs:')
        message = get_current_tabs(course_id)
    elif action == 'delete_tab':
        title = _('Delete Tab Status:')
        delete_tab_args = request.POST.get('tab_delete', '').strip()
        message = delete_tab(course_id, delete_tab_args)
    elif action == 'insert_tab':
        title = _('Insert Tab Status:')
        insert_tab_args = request.POST.get('tab_insert', '').strip()
        message = insert_tab(course_id, insert_tab_args)
    return u"<h4>{title}</h4><p class='unique-row'>{message}</p>".format(
        title=title,
        message=message,
    )


def get_current_tabs(course_id):
    """Displays a list of tabs for the given course"""

    try:
        course_key = locator.CourseLocator.from_string(course_id)
        course = get_course_by_id(course_key)
    except InvalidKeyError:
        message = _('Error - Invalid Course ID')
    else:
        # Translators: number, type, and name refer to tab number, tab type, and tab name
        message = _('number, type, name')
        for index, item in enumerate(course.tabs):
            message += "<br />{tab_number}, {tab_type}, {tab_name}".format(
                tab_number=index + 1,
                tab_type=item['type'],
                tab_name=item['name'],
            )
    return message


def delete_tab(course_id, args):
    """Deletes the specified tab from the course"""

    try:
        tab_number = int(args)
        course_key = locator.CourseLocator.from_string(course_id)
        course = get_course_by_id(course_key)
    except InvalidKeyError:
        message = _('Error - Invalid Course ID')
        return message
    except ValueError:
        message = _('Error - Invalid arguments. Expecting one argument [tab-number]')
        return message
    try:
        primitive_delete(course, tab_number - 1)  # -1 for 0-based indexing
        message = _("Tab {tab_number} for course {course_key} successfully deleted".format(
            tab_number=tab_number,
            course_key=course_key,
        ))
    except ValueError as error:
        message = _("Command Failed - {msg}".format(
            msg=error,
        ))
    return message


def insert_tab(course_id, args):
    """Inserts the specified tab into the list of tabs for this course"""

    try:
        course_key = locator.CourseLocator.from_string(course_id)
        course = get_course_by_id(course_key)
    except InvalidKeyError:
        message = _('Error - Invalid Course ID')
        return message
    args = [arg.strip() for arg in args.split(",")]
    if len(args) != 3:
        message = _('Error - Invalid number of arguments. Expecting [tab-number], [tab-type], [tab-name]')
        return message
    try:
        tab_number = int(args[0])
        tab_type = args[1]
        tab_name = args[2]
    except ValueError:
        message = _('Error - Invalid arguments. Expecting [tab-number], [tab-type], [tab-name]')
        return message
    try:
        primitive_insert(course, tab_number - 1, tab_type, tab_name)  # -1 as above
        message = _("Tab {tab_number}, {tab_type}, {tab_name} for course {course_key} successfully created".format(
            tab_number=tab_number,
            tab_type=tab_type,
            tab_name=tab_name,
            course_key=course_key,
        ))
    except (ValueError, InvalidTabsException) as error:
        message = _("Command Failed - {msg}".format(
            msg=error,
        ))
    return message
