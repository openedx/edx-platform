import json
from courseware.models import StudentModule
from xmodule.fields import Date

date_field = Date()


def set_due_date_extension(course, url, student, due_date):
    """
    Sets a due date extension.  Factored to be usable in both legacy and beta
    instructor dashboards.
    """
    unit = find_unit(course, url)
    if not unit:
        return "Couldn't find module for url: {0}".format(url), None

    def set_due_date(node):
        try:
            student_module = StudentModule.objects.get(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location.url()
            )

            state = json.loads(student_module.state)
            state['extended_due'] = date_field.to_json(due_date)
            student_module.state = json.dumps(state)
            student_module.save()
        except StudentModule.DoesNotExist:
            pass

        for child in node.get_children():
            set_due_date(child)

    set_due_date(unit)

    return None, unit  # no error


def find_unit(node, url):
    """
    Find node in course tree for url.
    """
    if node.location.url() == url:
        return node
    for child in node.get_children():
        found = find_unit(child, url)
        if found:
            return found
    return None


def get_units_with_due_date(course):
    units = []

    def visit(node, level=0):
        if getattr(node, 'due', None):
            units.append(node)
        else:
            for child in node.get_children():
                visit(child, level + 1)
    visit(course)
    units.sort(key=title_or_url)
    return units


def get_units_with_due_date_options(course):
    def make_option(node):
        return title_or_url(node), node.location.url()
    return map(make_option, get_units_with_due_date(course))


def title_or_url(node):
    title = getattr(node, 'display_name', None)
    if not title:
        title = node.location.url()
    return title


def dump_students_with_due_date_extensions(course, url):
    unit = find_unit(course, url)
    if not unit:
        return "Couldn't find module for url: {0}".format(url), {}

    data = []
    query = StudentModule.objects.filter(
        course_id=course.id,
        module_state_key=url)
    for sm in query:
        state = json.loads(sm.state)
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = date_field.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        fullname = sm.student.profile.name
        data.append((sm.student.username, fullname, extended_due))
    data.sort(key=lambda x: x[0])
    return None, {
        "header": ["Username", "Full Name", "Extended Due Date"],
        "title": "Users with due date extensions for {0}".format(
            title_or_url(unit)),
        "data": data
    }


def dump_due_date_extensions_for_student(course, student):
    data = []
    units = get_units_with_due_date(course)
    units = dict([(u.location.url(), u) for u in units])
    query = StudentModule.objects.filter(
        course_id=course.id,
        student_id=student.id)
    for sm in query:
        state = json.loads(sm.state)
        if sm.module_state_key not in units:
            continue
        extended_due = state.get("extended_due")
        if not extended_due:
            continue
        extended_due = date_field.from_json(extended_due)
        extended_due = extended_due.strftime("%Y-%m-%d %H:%M")
        title = title_or_url(units[sm.module_state_key])
        data.append((title, extended_due))
    return None, {
        "header": ["Unit", "Extended Due Date"],
        "title": "Due date extensions for {0} {1} ({2})".format(
            student.first_name, student.last_name, student.username),
        "data": data}
