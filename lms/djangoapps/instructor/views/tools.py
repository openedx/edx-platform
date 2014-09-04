"""
Tools for the instructor dashboard
"""
import dateutil
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.utils.timezone import utc
from django.utils.translation import ugettext as _

from courseware.models import StudentModule
from xmodule.fields import Date
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import UsageKey

from bulk_email.models import CourseAuthorization

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


def bulk_email_is_enabled_for_course(course_id):
    """
    Staff can only send bulk email for a course if all the following conditions are true:
    1. Bulk email feature flag is on.
    2. It is a studio course.
    3. Bulk email is enabled for the course.
    """

    bulk_email_enabled_globally = (settings.FEATURES['ENABLE_INSTRUCTOR_EMAIL'] == True)
    is_studio_course = (modulestore().get_modulestore_type(course_id) != ModuleStoreEnum.Type.xml)
    bulk_email_enabled_for_course = CourseAuthorization.instructor_email_enabled(course_id)

    if bulk_email_enabled_globally and is_studio_course and bulk_email_enabled_for_course:
        return True

    return False


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


def get_extended_due(course, unit, student):
    """
    Get the extended due date out of a student's state for a particular unit.
    """
    student_module = StudentModule.objects.get(
        student_id=student.id,
        course_id=course.id,
        module_state_key=unit.location
    )

    state = json.loads(student_module.state)
    extended = state.get('extended_due', None)
    if extended:
        return DATE_FIELD.from_json(extended)


def set_due_date_extension(course, unit, student, due_date):
    """
    Sets a due date extension. Raises DashboardError if the unit or extended
    due date is invalid.
    """
    if due_date:
        # Check that the new due date is valid:
        original_due_date = getattr(unit, 'due', None)

        if not original_due_date:
            raise DashboardError(_("Unit {0} has no due date to extend.").format(unit.location))
        if due_date < original_due_date:
            raise DashboardError(_("An extended due date must be later than the original due date."))
    else:
        # We are deleting a due date extension. Check that it exists:
        if not get_extended_due(course, unit, student):
            raise DashboardError(_("No due date extension is set for that student and unit."))

    def set_due_date(node):
        """
        Recursively set the due date on a node and all of its children.
        """
        try:
            student_module = StudentModule.objects.get(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location
            )
            state = json.loads(student_module.state)

        except StudentModule.DoesNotExist:
            # Normally, a StudentModule is created as a side effect of assigning
            # a value to a property in an XModule or XBlock which has a scope
            # of 'Scope.user_state'.  Here, we want to alter user state but
            # can't use the standard XModule/XBlock machinery to do so, because
            # it fails to take into account that the state being altered might
            # belong to a student other than the one currently logged in.  As a
            # result, in our work around, we need to detect whether the
            # StudentModule has been created for the given student on the given
            # unit and create it if it is missing, so we can use it to store
            # the extended due date.
            student_module = StudentModule.objects.create(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location,
                module_type=node.category
            )
            state = {}

        state['extended_due'] = DATE_FIELD.to_json(due_date)
        student_module.state = json.dumps(state)
        student_module.save()

        for child in node.get_children():
            set_due_date(child)

    set_due_date(unit)


def dump_module_extensions(course, unit):
    """
    Dumps data about students with due date extensions for a particular module,
    specified by 'url', in a particular course.
    """
    data = []
    header = [_("Username"), _("Full Name"), _("Extended Due Date")]
    query = StudentModule.objects.filter(
        course_id=course.id,
        module_state_key=unit.location)
    for module in query:
        state = json.loads(module.state)
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = DATE_FIELD.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        fullname = module.student.profile.name
        data.append(dict(zip(
            header,
            (module.student.username, fullname, extended_due))))
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
    units = dict([(u.location, u) for u in units])
    query = StudentModule.objects.filter(
        course_id=course.id,
        student_id=student.id)
    for module in query:
        state = json.loads(module.state)
        # temporary hack: module_state_key is missing the run but units are not. fix module_state_key
        module_loc = module.module_state_key.map_into_course(module.course_id)
        if module_loc not in units:
            continue
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = DATE_FIELD.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        title = title_or_url(units[module_loc])
        data.append(dict(zip(header, (title, extended_due))))
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
