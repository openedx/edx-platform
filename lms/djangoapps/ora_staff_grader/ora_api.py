"""
Functions used for interacting with ORA

All XBlock handlers are wrapped to either return data or raise an exception to make error-handling clear.
"""
import json
from lms.djangoapps.ora_staff_grader.errors import ExceptionWithContext, LockContestedError

from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler


def get_submissions(request, usage_id):
    """
    Get a list of submissions from the ORA's 'list_staff_workflows' XBlock.json_handler
    """
    response = call_xblock_json_handler(request, usage_id, 'list_staff_workflows', {})

    if response.status_code != 200:
        raise Exception()

    return json.loads(response.content)


def get_rubric_config(request, usage_id):
    """
    Get rubric data from the ORA's 'get_rubric' XBlock.json_handler
    """
    data = {'target_rubric_block_id': usage_id}
    response = call_xblock_json_handler(request, usage_id, 'get_rubric', data)

    # Unhandled errors might not be JSON, catch before loading
    if response.status_code != 200:
        raise Exception()

    response_data = json.loads(response.content)

    # Handled faillure still returns HTTP 200 but with 'success': False and supplied error message "msg"
    if not response_data.get('success', False):
        raise ExceptionWithContext(context={"msg": response_data.get('msg', '')})

    return response_data['rubric']


def get_submission_info(request, usage_id, submission_uuid):
    """
    Get submission content from ORA 'get_submission_info' XBlock.json_handler
    """
    data = {'submission_uuid': submission_uuid}
    response = call_xblock_json_handler(request, usage_id, 'get_submission_info', data)

    if response.status_code != 200:
        raise Exception()

    return json.loads(response.content)


def get_assessment_info(request, usage_id, submission_uuid):
    """
    Get assessment data from ORA 'get_assessment_info' XBlock.json_handler
    """
    data = {'submission_uuid': submission_uuid}
    response = call_xblock_json_handler(request, usage_id, 'get_assessment_info', data)

    if response.status_code != 200:
        raise Exception()

    return json.loads(response.content)


def submit_grade(request, usage_id, grade_data):
    """
    Submit a grade for an assessment.

    Returns: {'success': True/False, 'msg': err_msg}
    """
    response = call_xblock_json_handler(request, usage_id, 'staff_assess', grade_data)

    # Unhandled errors might not be JSON, catch before loading
    if response.status_code != 200:
        raise Exception()

    response_data = json.loads(response.content)

    # Handled faillure still returns HTTP 200 but with 'success': False and supplied error message "msg"
    if not response_data.get('success', False):
        raise ExceptionWithContext(context={"msg": response_data.get('msg', '')})

    return response_data


def check_submission_lock(request, usage_id, submission_uuid):
    """
    Look up lock info for the given submission by calling the ORA's 'check_submission_lock' XBlock.json_handler
    """
    data = {'submission_uuid': submission_uuid}
    response = call_xblock_json_handler(request, usage_id, 'check_submission_lock', data)

    # Unclear that there would every be an error (except network/auth) but good to catch here
    if response.status_code != 200:
        raise Exception()

    return json.loads(response.content)


def claim_submission_lock(request, usage_id, submission_uuid):
    """
    Attempt to claim a submission lock for grading.

    Returns:
    - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
    """
    body = {"submission_uuid": submission_uuid}
    response = call_xblock_json_handler(request, usage_id, 'claim_submission_lock', body)

    # Lock contested returns a 403
    if response.status_code == 403:
        raise LockContestedError()

    # Other errors should raise a blanket exception
    elif response.status_code != 200:
        raise Exception()

    return json.loads(response.content)


def delete_submission_lock(request, usage_id, submission_uuid):
    """
    Attempt to claim a submission lock for grading.

    Returns:
    - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
    """
    body = {"submission_uuid": submission_uuid}

    # Return raw response to preserve HTTP status codes for failure states
    response = call_xblock_json_handler(request, usage_id, 'delete_submission_lock', body)

    # Lock contested returns a 403
    if response.status_code == 403:
        raise LockContestedError()

    # Other errors should raise a blanket exception
    elif response.status_code != 200:
        raise Exception()

    return json.loads(response.content)
