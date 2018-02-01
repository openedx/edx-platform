from crum import get_current_request
from channels import Group
import json
from .services import CompletionService


def roll_up(user, course_key):

    completion_service = CompletionService(user, course_key)
    percent_completed = completion_service.get_percent_completed(get_current_request())

    # fire event to websocket
    Group('completion').send(
        {'text': json.dumps({
            'course_id': str(course_key),
            'percent_complete': percent_completed
        })}
    )