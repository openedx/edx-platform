""" XBlock handler functions used by ESG endpoints """
import json
from lms.djangoapps.ora_staff_grader.utils import call_xblock_json_handler

class XblockHandlersMixin():
    """ XBlock handler functions for ESG. Provides a light interface and data transforms for reuse and ease-of-use. """

    def get_submissions(self, request, usage_id):
        """
        Get a list of submissions from the ORA's 'list_staff_workflows' XBlock.json_handler
        """
        response = call_xblock_json_handler(request, usage_id, 'list_staff_workflows', {})
        return json.loads(response.content)

    def get_rubric_config(self, request, usage_id):
        """
        Get rubric data from the ORA's 'get_rubric' XBlock.json_handler
        """
        data = {'target_rubric_block_id': usage_id}
        response = call_xblock_json_handler(request, usage_id, 'get_rubric', data)
        return json.loads(response.content)

    def get_submission_info(self, request, usage_id, submission_uuid):
        """
        Get submission content from ORA 'get_submission_info' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'get_submission_info', data)
        return json.loads(response.content)

    def get_assessment_info(self, request, usage_id, submission_uuid):
        """
        Get assessment data from ORA 'get_assessment_info' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'get_assessment_info', data)
        return json.loads(response.content)

    def submit_grade(self, request, usage_id, grade_data):
        """
        Submit a grade for an assessment.

        Returns: {'success': True/False, 'msg': err_msg}
        """
        response = call_xblock_json_handler(request, usage_id, 'staff_assess', grade_data)
        return json.loads(response.content)

    def check_submission_lock(self, request, usage_id, submission_uuid):
        """
        Look up lock info for the given submission by calling the ORA's 'check_submission_lock' XBlock.json_handler
        """
        data = {'submission_uuid': submission_uuid}
        response = call_xblock_json_handler(request, usage_id, 'check_submission_lock', data)
        return json.loads(response.content)

    def claim_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {"submission_uuid": submission_uuid}

        # Return the raw response to preserve HTTP status codes for failure states
        return call_xblock_json_handler(request, usage_id, 'claim_submission_lock', body)

    def delete_submission_lock(self, request, usage_id, submission_uuid):
        """
        Attempt to claim a submission lock for grading.

        Returns:
        - lockStatus (string) - One of ['not-locked', 'locked', 'in-progress']
        """
        body = {"submission_uuid": submission_uuid}

        # Return raw response to preserve HTTP status codes for failure states
        return call_xblock_json_handler(request, usage_id, 'delete_submission_lock', body)
