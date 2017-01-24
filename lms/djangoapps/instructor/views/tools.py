"""
Tools for the instructor dashboard
"""
import dateutil
import json

from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.utils.timezone import utc
from django.utils.translation import ugettext as _

from courseware.models import StudentFieldOverride
from courseware.field_overrides import disable_overrides
from courseware.student_field_overrides import (
    clear_override_for_user,
    get_override_for_user,
    override_field_for_user,
)
from xmodule.fields import Date
from opaque_keys.edx.keys import UsageKey

DATE_FIELD = Date()


class DashboardError(Exception):
    """
    Errors arising from use of the instructor dashboard.
    """
    def response(self):
        """
        Generate an instance of HttpResponseBadRequest for this error.
        """
        error = unicode(self)
        return HttpResponseBadRequest(json.dumps({'error': error}))


def handle_dashboard_error(view):
    """
    Decorator which adds seamless DashboardError handling to a view.  If a
    DashboardError is raised during view processing, an HttpResponseBadRequest
    is sent back to the client with JSON data about the error.
    """
    def wrapper(request, course_id):
        """
        Wrap the view.
        """
        try:
            return view(request, course_id=course_id)
        except DashboardError, error:
            return error.response()

    return wrapper


def strip_if_string(value):
    if isinstance(value, basestring):
        return value.strip()
    return value


def get_student_from_identifier(unique_student_identifier):
    """
    Gets a student object using either an email address or username.

    Returns the student object associated with `unique_student_identifier`

    Raises User.DoesNotExist if no user object can be found.
    """
    unique_student_identifier = strip_if_string(unique_student_identifier)
    if "@" in unique_student_identifier:
        student = User.objects.get(email=unique_student_identifier)
    else:
        student = User.objects.get(username=unique_student_identifier)
    return student


def require_student_from_identifier(unique_student_identifier):
    """
    Same as get_student_from_identifier() but will raise a DashboardError if
    the student does not exist.
    """
    try:
        return get_student_from_identifier(unique_student_identifier)
    except User.DoesNotExist:
        raise DashboardError(
            _("Could not find student matching identifier: {student_identifier}").format(
                student_identifier=unique_student_identifier
            )
        )


def parse_datetime(datestr):
    """
    Convert user input date string into an instance of `datetime.datetime` in
    UTC.
    """
    try:
        return dateutil.parser.parse(datestr).replace(tzinfo=utc)
    except ValueError:
        raise DashboardError(_("Unable to parse date: ") + datestr)


def find_unit(course, url):
    """
    Finds the unit (block, module, whatever the terminology is) with the given
    url in the course tree and returns the unit.  Raises DashboardError if no
    unit is found.
    """
    def find(node, url):
        """
        Find node in course tree for url.
        """
        if node.location.to_deprecated_string() == url:
            return node
        for child in node.get_children():
            found = find(child, url)
            if found:
                return found
        return None

    unit = find(course, url)
    if unit is None:
        raise DashboardError(_("Couldn't find module for url: {0}").format(url))
    return unit


def get_units_with_due_date(course):
    """
    Returns all top level units which have due dates.  Does not return
    descendents of those nodes.
    """
    units = []

    def visit(node):
        """
        Visit a node.  Checks to see if node has a due date and appends to
        `units` if it does.  Otherwise recurses into children to search for
        nodes with due dates.
        """
        if getattr(node, 'due', None):
            units.append(node)
        else:
            for child in node.get_children():
                visit(child)
    visit(course)
    #units.sort(key=_title_or_url)
    return units


def title_or_url(node):
    """
    Returns the `display_name` attribute of the passed in node of the course
    tree, if it has one.  Otherwise returns the node's url.
    """
    title = getattr(node, 'display_name', None)
    if not title:
        title = node.location.to_deprecated_string()
    return title


def set_due_date_extension(course, unit, student, due_date):
    """
    Sets a due date extension. Raises DashboardError if the unit or extended
    due date is invalid.
    """
    if due_date:
        # Check that the new due date is valid:
        with disable_overrides():
            original_due_date = getattr(unit, 'due', None)

        if not original_due_date:
            raise DashboardError(_("Unit {0} has no due date to extend.").format(unit.location))
        if due_date < original_due_date:
            raise DashboardError(_("An extended due date must be later than the original due date."))

        override_field_for_user(student, unit, 'due', due_date)

    else:
        # We are deleting a due date extension. Check that it exists:
        if not get_override_for_user(student, unit, 'due'):
            raise DashboardError(_("No due date extension is set for that student and unit."))

        clear_override_for_user(student, unit, 'due')


def dump_module_extensions(course, unit):
    """
    Dumps data about students with due date extensions for a particular module,
    specified by 'url', in a particular course.
    """
    data = []
    header = [_("Username"), _("Full Name"), _("Extended Due Date")]
    query = StudentFieldOverride.objects.filter(
        course_id=course.id,
        location=unit.location,
        field='due')
    for override in query:
        due = DATE_FIELD.from_json(json.loads(override.value))
        due = due.strftime("%Y-%m-%d %H:%M")
        fullname = override.student.profile.name
        data.append(dict(zip(
            header,
            (override.student.username, fullname, due))))
    data.sort(key=lambda x: x[header[0]])
    return {
        "header": header,
        "title": _("Users with due date extensions for {0}").format(
            title_or_url(unit)),
        "data": data
    }


def dump_student_extensions(course, student):
    """
    Dumps data about the due date extensions granted for a particular student
    in a particular course.
    """
    data = []
    header = [_("Unit"), _("Extended Due Date")]
    units = get_units_with_due_date(course)
    units = {u.location: u for u in units}
    query = StudentFieldOverride.objects.filter(
        course_id=course.id,
        student=student,
        field='due')
    for override in query:
        location = override.location.replace(course_key=course.id)
        if location not in units:
            continue
        due = DATE_FIELD.from_json(json.loads(override.value))
        due = due.strftime("%Y-%m-%d %H:%M")
        title = title_or_url(units[location])
        data.append(dict(zip(header, (title, due))))
    return {
        "header": header,
        "title": _("Due date extensions for {0} {1} ({2})").format(
            student.first_name, student.last_name, student.username),
        "data": data}


def add_block_ids(payload):
    """
    rather than manually parsing block_ids from module_ids on the client, pass the block_ids explicitly in the payload
    """
    if 'data' in payload:
        for ele in payload['data']:
            if 'module_id' in ele:
                ele['block_id'] = UsageKey.from_string(ele['module_id']).block_id
