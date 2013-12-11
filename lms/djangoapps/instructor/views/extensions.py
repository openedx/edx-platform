"""
Common library for working with individual due date extensions that can be used
by either the legacy or the beta instructor dashboard.
"""

import json
from courseware.models import StudentModule
from xmodule.fields import Date

DATE_FIELD = Date()


def set_due_date_extension(course, url, student, due_date):
    """
    Sets a due date extension.  Factored to be usable in both legacy and beta
    instructor dashboards.
    """
    unit = _find_unit(course, url)
    if not unit:
        return "Couldn't find module for url: {0}".format(url), None

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

    return None, unit  # no error


def _find_unit(node, url):
    """
    Find node in course tree for url.
    """
    if node.location.url() == url:
        return node
    for child in node.get_children():
        found = _find_unit(child, url)
        if found:
            return found
    return None


def _get_units_with_due_date(course):
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
    units.sort(key=_title_or_url)
    return units


def get_units_with_due_date_options(course):
    """
    Finds all top level units that have a due date and returns them as a
    sequence of (title, url) tuples suitable for populating the pull down to
    select a unit in the 'Extensions' tab.
    """
    def make_option(node):
        "Returns (title, url) tuple for a node."
        return _title_or_url(node), node.location.url()
    return map(make_option, _get_units_with_due_date(course))


def _title_or_url(node):
    """
    Returns the `display_name` attribute of the passed in node of the course
    tree, if it has one.  Otherwise returns the node's url.
    """
    title = getattr(node, 'display_name', None)
    if not title:
        title = node.location.url()
    return title


def dump_module_extensions(course, url):
    """
    Dumps data about students with due date extensions for a particular module,
    specified by 'url', in a particular course.  Returns a tuple of (error,
    data).  If there is an error, `error` will be a strong suitable for
    displaying to the user and `data` will be None.  Otherwise `error` will be
    None, and `data` will be a data structure formatted for use by the legacy
    instructor dashboard's 'datatable'.
    """
    unit = _find_unit(course, url)
    if not unit:
        return "Couldn't find module for url: {0}".format(url), {}

    data = []
    query = StudentModule.objects.filter(
        course_id=course.id,
        module_state_key=url)
    for module in query:
        state = json.loads(module.state)
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = DATE_FIELD.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        fullname = module.student.profile.name
        data.append((module.student.username, fullname, extended_due))
    data.sort(key=lambda x: x[0])
    return None, {
        "header": ["Username", "Full Name", "Extended Due Date"],
        "title": "Users with due date extensions for {0}".format(
            _title_or_url(unit)),
        "data": data
    }


def dump_student_extensions(course, student):
    """
    Dumps data about the due date extensions granted for a particular student
    in a particular course.  Returns a data structure formatted for use by the
    legacy instructor dashboard's 'datatable'.
    """
    data = []
    units = _get_units_with_due_date(course)
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
        title = _title_or_url(units[module.module_state_key])
        data.append((title, extended_due))
    return {
        "header": ["Unit", "Extended Due Date"],
        "title": "Due date extensions for {0} {1} ({2})".format(
            student.first_name, student.last_name, student.username),
        "data": data}
