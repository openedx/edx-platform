"""
Implementation of "courseware" service
"""

import logging

from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from courseware.models import StudentModule
from instructor.views.tools import get_student_from_identifier
import instructor.enrollment as enrollment


log = logging.getLogger(__name__)


class CoursewareService(object):
    """
    Courseware service for deleting student attempt
    """

    def delete_student_attempt(self, student_identifier, course_id, content_id):
        """
        Deletes student state for a problem.

        Takes some of the following query parameters
            - content_id is a url-name of a problem
            - unique_student_identifier is an email or username
            - course_id is the id for the course
        """
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        student = get_student_from_identifier(student_identifier)
        try:
            module_state_key = course_id.make_usage_key_from_deprecated_string(content_id)
        except InvalidKeyError:
            log.error("Invalid content id %s .", content_id)
        if student:
            try:
                enrollment.reset_student_attempts(course_id, student, module_state_key, delete_module=True)
            except StudentModule.DoesNotExist:
                log.error("Module does not exist.")
            except enrollment.sub_api.SubmissionError:
                # Trust the submissions API to log the error
                log.error("An error occurred while deleting the score.")

