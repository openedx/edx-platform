import json
from courseware.models import StudentModule
from xmodule.fields import Date

datetime_to_json = Date().to_json


def set_due_date_extension(request, course_id, section, student, due_date):
    """
    Sets a due date extension.  Factored to be usable in both legacy and beta
    instructor dashboards.
    """
    try:
        student_module = StudentModule.objects.get(
            student_id=student.id,
            course_id=course_id,
            module_state_key=section
        )
        state = json.loads(student_module.state)
        state['extended_due'] = datetime_to_json(due_date)
        student_module.state = json.dumps(state)
        student_module.save()
        return None # no error

    except StudentModule.DoesNotExist:
        return "Couldn't find module with that urlname: {0} {1}. ".format(
            section, student
        )
