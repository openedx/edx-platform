"""
xqueue_submission.py

This module handles the extraction and processing of student submission data
from edx-submission.
"""

import json
import logging

import re
from opaque_keys.edx.keys import CourseKey

log = logging.getLogger(__name__)
dateformat = '%Y-%m-%dT%H:%M:%S'


class XQueueInterfaceSubmission:
    """Interface to the external grading system."""

    def _parse_json(self, data, name):
        """Helper function to parse JSON safely."""
        try:
            return json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing {name}: {e}") from e

    def _extract_identifiers(self, callback_url):
        """Extracts identifiers from the callback URL."""
        item_id_match = re.search(r'block@([^\/]+)', callback_url)
        item_type_match = re.search(r'type@([^+]+)', callback_url)
        course_id_match = re.search(r'(course-v1:[^\/]+)', callback_url)

        if not item_id_match or not item_type_match or not course_id_match:
            raise ValueError("The callback_url does not contain the required information.")

        return item_id_match.group(1), item_type_match.group(1), course_id_match.group(1)

    def extract_item_data(self, header, payload):
        """
        Extracts student submission data from the given header and payload.
        """
        from lms.djangoapps.courseware.models import StudentModule
        from opaque_keys.edx.locator import BlockUsageLocator

        header = self._parse_json(header, "header")
        payload = self._parse_json(payload, "payload")

        callback_url = header.get('lms_callback_url')
        queue_name = header.get('queue_name', 'default')

        if not callback_url:
            raise ValueError("The header does not contain 'lms_callback_url'.")

        item_id, item_type, course_id = self._extract_identifiers(callback_url)

        student_info = self._parse_json(payload["student_info"], "student_info")

        try:
            full_block_id = f"block-v1:{course_id.replace('course-v1:', '')}+type@{item_type}+block@{item_id}"
            usage_key = BlockUsageLocator.from_string(full_block_id)
        except Exception as e:
            raise ValueError(f"Error creating BlockUsageLocator. Invalid ID: {full_block_id}, Error: {e}") from e

        try:
            course_key = CourseKey.from_string(course_id)
        except Exception as e:
            raise ValueError(f"Error creating CourseKey: {e}") from e

        try:
            grader_payload = self._parse_json(payload["grader_payload"], "grader_payload")
            grader = grader_payload.get("grader", '')
        except KeyError as e:
            raise ValueError(f"Error in payload: {e}") from e

        student_id = student_info.get("anonymous_student_id")
        if not student_id:
            raise ValueError("The field 'anonymous_student_id' is missing from student_info.")

        student_dict = {
            'item_id': full_block_id,
            'item_type': item_type,
            'course_id': course_id,
            'student_id': student_id
        }

        student_answer = payload.get("student_response")
        if student_answer is None:
            raise ValueError("The field 'student_response' does not exist.")

        student_module = StudentModule.objects.filter(
            module_state_key=usage_key,
            course_id=course_key
        ).first()

        log.error(f"student_module: {student_module}")

        score = student_module.grade if student_module and student_module.grade is not None else None

        log.error(f"Score: {student_id}: {score}")

        return student_dict, student_answer, queue_name, grader, score

    def send_to_submission(self, header, body, files_to_upload=None):
        """
        Submits the extracted student data to the edx-submissions system.
        """
        from submissions.api import create_submission

        try:
            student_item, answer, queue_name, grader, score = self.extract_item_data(header, body)
            return create_submission(student_item, answer, queue_name=queue_name, grader=grader, score=score)
        except json.JSONDecodeError as e:
            log.error(f"JSON decoding error: {e}")
            return {"error": "Invalid JSON format"}

        except KeyError as e:
            log.error(f"Missing key: {e}")
            return {"error": f"Missing key: {e}"}

        except ValueError as e:
            log.error(f"Validation error: {e}")
            return {"error": f"Validation error: {e}"}

        except TypeError as e:
            log.error(f"Type error: {e}")
            return {"error": f"Type error: {e}"}

        except RuntimeError as e:
            log.error(f"Runtime error: {e}")
            return {"error": f"Runtime error: {e}"}
