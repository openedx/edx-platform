"""
This module provides an interface for submitting student responses
to an external grading system through XQueue.
"""

import json
import logging
from xmodule.capa.errors import (
    GetSubmissionParamsError,
    JSONParsingError,
    MissingKeyError,
    ValidationError,
    TypeErrorSubmission,
    RuntimeErrorSubmission
)

log = logging.getLogger(__name__)


class XQueueInterfaceSubmission:
    """Interface to the external grading system."""

    def __init__(self, block):
        self.block = block

    def _parse_json(self, data, name):
        """
        Helper function to safely parse data that may or may not be a JSON string.
        This is necessary because some callers may already provide parsed Python dicts
        (e.g., during internal calls or test cases), while other sources may send raw JSON strings.
        This helper ensures consistent behavior regardless of input format.
        Args:
            data: The input to parse, either a JSON string or a Python dict.
            name: Name of the field (used for error reporting).
        Returns:
            Parsed Python object or original data if already parsed.
        Raises:
            JSONParsingError: If `data` is a string and cannot be parsed as JSON.
        """
        try:
            return json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError as e:
            raise JSONParsingError(name, str(e)) from e

    def get_submission_params(self, header, payload):
        """
        Extracts student submission data from the given header and payload.
        """
        header = self._parse_json(header, "header")
        payload = self._parse_json(payload, "payload")

        queue_name = header.get('queue_name', 'default')

        if not self.block:
            raise GetSubmissionParamsError()

        course_id = str(self.block.scope_ids.usage_id.context_key)
        item_type = self.block.scope_ids.block_type
        points_possible = self.block.max_score()

        item_id = str(self.block.scope_ids.usage_id)

        try:
            grader_payload = self._parse_json(payload["grader_payload"], "grader_payload")
            grader_file_name = grader_payload.get("grader", '')
        except KeyError as e:
            raise MissingKeyError("grader_payload") from e

        student_info = self._parse_json(payload["student_info"], "student_info")
        student_id = student_info.get("anonymous_student_id")

        if not student_id:
            raise ValidationError("The field 'anonymous_student_id' is missing from student_info.")

        student_answer = payload.get("student_response")
        if student_answer is None:
            raise ValidationError("The field 'student_response' does not exist.")

        student_dict = {
            'item_id': item_id,
            'item_type': item_type,
            'course_id': course_id,
            'student_id': student_id
        }

        return student_dict, student_answer, queue_name, grader_file_name, points_possible

    def send_to_submission(self, header, body, files_to_upload=None):
        """
        Submits the extracted student data to the edx-submissions system.
        """
        try:
            from submissions.api import create_external_grader_detail
            student_item, answer, queue_name, grader_file_name, points_possible = (
                self.get_submission_params(header, body)
            )
            return create_external_grader_detail(
                student_item,
                answer,
                queue_name=queue_name,
                grader_file_name=grader_file_name,
                points_possible=points_possible,
                files=files_to_upload
            )
        except (JSONParsingError, MissingKeyError, ValidationError) as e:
            log.error("%s", e)
            return {"error": str(e)}
        except TypeError as e:
            log.error("%s", e)
            raise TypeErrorSubmission(str(e)) from e
        except RuntimeError as e:
            log.error("%s", e)
            raise RuntimeErrorSubmission(str(e)) from e
