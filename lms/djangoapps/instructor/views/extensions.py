import json
from courseware.models import StudentModule
from xmodule.fields import Date

datetime_to_json = Date().to_json


def set_due_date_extension(course, url, student, due_date):
    """
    Sets a due date extension.  Factored to be usable in both legacy and beta
    instructor dashboards.
    """
    def find_node(node):
        """
        Find node in course tree for url.
        """
        if node.location.url() == url:
            return node
        for child in node.get_children():
            found = find_node(child)
            if found:
                return found
        return None

    node = find_node(course)
    if not node:
        return "Couldn't find module for url: {0}" % url

    def set_due_date(node):
        try:
            student_module = StudentModule.objects.get(
                student_id=student.id,
                course_id=course.id,
                module_state_key=node.location.url()
            )

            state = json.loads(student_module.state)
            state['extended_due'] = datetime_to_json(due_date)
            student_module.state = json.dumps(state)
            student_module.save()
        except StudentModule.DoesNotExist:
            pass

        for child in node.get_children():
            set_due_date(child)

    set_due_date(node)

    return None # no error
