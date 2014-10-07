"""
Tools for the instructor dashboard
"""
import json
import dateutil
import itertools

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.utils.timezone import utc
from django.utils.translation import ugettext as _

from courseware.models import StudentModule
from xmodule.fields import Date
from xmodule.modulestore import XML_MODULESTORE_TYPE
from xmodule.modulestore.django import modulestore

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
    is_studio_course = (modulestore().get_modulestore_type(course_id) != XML_MODULESTORE_TYPE)
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
        if node.location.url() == url:
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
        title = node.location.url()
    return title


def set_due_date_extension(course, unit, student, due_date):
    """
    Sets a due date extension.
    """
    def set_due_date(node):
        """
        Recursively set the due date on a node and all of its children.
        """
        try:
            student_module = StudentModule.objects.get(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location.url()
            )
            state = json.loads(student_module.state)

        except StudentModule.DoesNotExist:
            student_module = StudentModule.objects.create(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location.url(),
                module_type=node.category)
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
        module_state_key=unit.location.url())
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
    units = dict([(u.location.url(), u) for u in units])
    query = StudentModule.objects.filter(
        course_id=course.id,
        student_id=student.id)
    for module in query:
        state = json.loads(module.state)
        if module.module_state_key not in units:
            continue
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = DATE_FIELD.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        title = title_or_url(units[module.module_state_key])
        data.append(dict(zip(header, (title, extended_due))))
    return {
        "header": header,
        "title": _("Due date extensions for {0} {1} ({2})").format(
            student.first_name, student.last_name, student.username),
        "data": data}


def reapply_all_extensions(course):
    units = get_units_with_due_date(course)
    units = dict([(u.location.url(), u) for u in units])
    msks = units.keys()
    query = StudentModule.objects.filter(
        course_id=course.id,
        module_state_key__in=msks,
        state__contains='extended_due'
    )
    eunit_map = itertools.groupby(query, lambda el: el.student)
    reapplied = {}
    for student, extended_modules in eunit_map:
        for module in extended_modules:
            state = json.loads(module.state)
            edue = DATE_FIELD.from_json(state.get('extended_due'))
            if not edue:
                continue
            unit = units.get(module.module_state_key)
            print('reapplying extension %s to %s for user %s' %
                  (edue, unit.location.url(), student.username))
            set_due_date_extension(course, unit, student, edue)
            r = reapplied.get(student.username, [])
            r.append(unit.location.url())
            reapplied[student.username] = r
    return reapplied
