"""
PhilU overrides courseware tasks
"""
import json
import logging

from courseware.models import StudentModule

log = logging.getLogger('edx.celery.task')


def task_correct_polls_data():
    """
    This task method converts possible choices data from list to string
    :return:
    """
    log.info('Getting student modules')

    student_modules = StudentModule.objects.filter(state__icontains='possible_choices')
    for module in student_modules:
        user_state = module.state
        try:
            json_state = json.loads(user_state)
            json_possible_choices = json_state["possible_choices"]

            if isinstance(json_possible_choices, list):

                possible_choices = json.dumps(json_possible_choices)
                json_state.update({"possible_choices": possible_choices})

                module.state = json.dumps(json_state)
                module.save()

                log.info('Module changed with id ' + str(module.id))
        except Exception as ex:  # pylint: disable=broad-except
            log.error('Code failed for ' + str(module.id) + ' and error is ' + str(ex.message))
