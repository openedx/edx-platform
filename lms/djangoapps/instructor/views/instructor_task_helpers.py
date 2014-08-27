"""
A collection of helper utility functions for working with instructor
tasks.
"""
import json
import logging
from util.date_utils import get_default_time_display
from bulk_email.models import CourseEmail
from django.utils.translation import ugettext as _
from instructor_task.views import get_task_completion_info

log = logging.getLogger(__name__)


def email_error_information():
    """
    Returns email information marked as None, used in event email
    cannot be loaded
    """
    expected_info = [
        'created',
        'sent_to',
        'email',
        'number_sent'
    ]
    return {info: None for info in expected_info}


def extract_email_features(email_task):
    """
    From the given task, extract email content information

    Expects that the given task has the following attributes:
    * task_input (dict containing email_id and to_option)
    * task_output (optional, dict containing total emails sent)

    With this information, gets the corresponding email object from the
    bulk emails table, and loads up a dict containing the following:
    * created, the time the email was sent displayed in default time display
    * sent_to, the group the email was delivered to
    * email, dict containing the subject, id, and html_message of an email
    * number_sent, int number of emails sent
    If task_input cannot be loaded, then the email cannot be loaded
    and None is returned for these fields.
    """
    # Load the task input info to get email id
    try:
        task_input_information = json.loads(email_task.task_input)
    except ValueError:
        log.error("Could not parse task input as valid json; task input: %s", email_task.task_input)
        return email_error_information()

    email = CourseEmail.objects.get(id=task_input_information['email_id'])

    creation_time = get_default_time_display(email.created)
    email_feature_dict = {'created': creation_time, 'sent_to': task_input_information['to_option']}
    features = ['subject', 'html_message', 'id']
    email_info = {feature: unicode(getattr(email, feature)) for feature in features}

    # Pass along email as an object with the information we desire
    email_feature_dict['email'] = email_info

    number_sent = None
    if hasattr(email_task, 'task_output') and email_task.task_output is not None:
        try:
            task_output = json.loads(email_task.task_output)
        except ValueError:
            log.error("Could not parse task output as valid json; task output: %s", email_task.task_output)
        else:
            if 'total' in task_output:
                number_sent = int(task_output['total'])
    email_feature_dict['number_sent'] = number_sent

    return email_feature_dict


def extract_task_features(task):
    """
    Convert task to dict for json rendering.
    Expects tasks have the following features:
    * task_type (str, type of task)
    * task_input (dict, input(s) to the task)
    * task_id (str, celery id of the task)
    * requester (str, username who submitted the task)
    * task_state (str, state of task eg PROGRESS, COMPLETED)
    * created (datetime, when the task was completed)
    * task_output (optional)
    """
    # Pull out information from the task
    features = ['task_type', 'task_input', 'task_id', 'requester', 'task_state']
    task_feature_dict = {feature: str(getattr(task, feature)) for feature in features}
    # Some information (created, duration, status, task message) require additional formatting
    task_feature_dict['created'] = task.created.isoformat()

    # Get duration info, if known
    duration_sec = 'unknown'
    if hasattr(task, 'task_output') and task.task_output is not None:
        try:
            task_output = json.loads(task.task_output)
        except ValueError:
            log.error("Could not parse task output as valid json; task output: %s", task.task_output)
        else:
            if 'duration_ms' in task_output:
                duration_sec = int(task_output['duration_ms'] / 1000.0)
    task_feature_dict['duration_sec'] = duration_sec

    # Get progress status message & success information
    success, task_message = get_task_completion_info(task)
    status = _("Complete") if success else _("Incomplete")
    task_feature_dict['status'] = status
    task_feature_dict['task_message'] = task_message

    return task_feature_dict
