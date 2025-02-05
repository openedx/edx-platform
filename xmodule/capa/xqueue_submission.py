"""
LMS Interface to external queueing system (xqueue)
"""
from typing import Dict, Optional, TYPE_CHECKING

import hashlib
import json
import logging

import requests
from django.conf import settings
from django.urls import reverse
from requests.auth import HTTPBasicAuth
import re
from xmodule.capa.util import construct_callback
if TYPE_CHECKING:
    from xmodule.capa_block import ProblemBlock

log = logging.getLogger(__name__)
dateformat = '%Y-%m-%dT%H:%M:%S'


XQUEUE_METRIC_NAME = 'edxapp.xqueue'

# Wait time for response from Xqueue.
XQUEUE_TIMEOUT = 35  # seconds
CONNECT_TIMEOUT = 3.05  # seconds
READ_TIMEOUT = 10  # seconds


def extract_item_data(header, payload):
    if isinstance(header, str):
        try:
            header = json.loads(header)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error to header: {e}")

    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error to payload: {e}")

    callback_url = header.get('lms_callback_url')
    queue_name = header.get('queue_name', 'default')
    if not callback_url:
        raise ValueError("El header is not content 'lms_callback_url'.")

    match_item_id = re.search(r'block@([^/]+)', callback_url)
    match_item_type = re.search(r'type@([^+]+)', callback_url)
    match_course_id = re.search(r'course-v1:([^/]+)', callback_url)

    if not (match_item_id and match_item_type and match_course_id):
        raise ValueError(f"The callback_url is not valid: {callback_url}")

    item_id = match_item_id.group(1)
    item_type = match_item_type.group(1)
    course_id = match_course_id.group(1)

    try:
        student_info = json.loads(payload["student_info"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Error to student_info: {e}")
    
    try:
        grader_payload = payload["grader_payload"]
        if isinstance(grader_payload, str):
            grader_payload = json.loads(grader_payload)
        grader = grader_payload.get("grader", '')
    except json.JSONDecodeError as e:
        raise ValueError(f"Error  grader_payload: {e}")
    except KeyError as e:
        raise ValueError(f"Error payload: {e}")
    
     

    student_id = student_info.get("anonymous_student_id")
    if not student_id:
        raise ValueError("The field 'anonymous_student_id' is not student_info.")

    student_dict = {
        'item_id': item_id,
        'item_type': item_type,
        'course_id': course_id,
        'student_id': student_id
    }

    student_answer = payload.get("student_response")
    if student_answer is None:
        raise ValueError("El campo 'student_response' no está presente en payload.")

    return student_dict, student_answer, queue_name, grader

class XQueueInterfaceSubmission:
    """
    Interface to the external grading system
    """    

    def send_to_submission(self, header, body, files_to_upload=None):
        from submissions.api import create_submission
        try:
            student_item, answer, queue_name, grader = extract_item_data(header, body)
            
            log.error(f"student_item: {student_item}")
            log.error(f"header: {header}")
            log.error(f"body: {body}")
            log.error(f"grader: {grader}")
            
            submission = create_submission(student_item, answer, queue_name=queue_name, grader=grader)
            
            return submission
        except Exception as e:
            return {"error": str(e)}