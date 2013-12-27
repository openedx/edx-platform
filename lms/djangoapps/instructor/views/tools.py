"""
Tools for the instructor dashboard
"""
import json

from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _

from courseware.models import StudentModule
from xmodule.fields import Date

DATE_FIELD = Date()


class DashboardError(Exception):
    """
    Errors arising from use of the instructor dashboard.
    """
    def response(self):
        error = unicode(self)
        return HttpResponseBadRequest(json.dumps({'error': error}))


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
            state['extended_due'] = DATE_FIELD.to_json(due_date)
            student_module.state = json.dumps(state)
            student_module.save()
        except StudentModule.DoesNotExist:
            pass

        for child in node.get_children():
            set_due_date(child)

    set_due_date(unit)
