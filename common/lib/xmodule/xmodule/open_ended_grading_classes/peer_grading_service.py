import json
import logging

from .grading_service_module import GradingService, GradingServiceError

log = logging.getLogger(__name__)


class PeerGradingService(GradingService):
    """
    Interface with the grading controller for peer grading
    """

    def __init__(self, config, system):
        config['system'] = system
        super(PeerGradingService, self).__init__(config)
        self.url = config['url'] + config['peer_grading']
        self.login_url = self.url + '/login/'
        self.get_next_submission_url = self.url + '/get_next_submission/'
        self.save_grade_url = self.url + '/save_grade/'
        self.is_student_calibrated_url = self.url + '/is_student_calibrated/'
        self.show_calibration_essay_url = self.url + '/show_calibration_essay/'
        self.save_calibration_essay_url = self.url + '/save_calibration_essay/'
        self.get_problem_list_url = self.url + '/get_problem_list/'
        self.get_notifications_url = self.url + '/get_notifications/'
        self.get_data_for_location_url = self.url + '/get_data_for_location/'
        self.system = system

    def get_data_for_location(self, problem_location, student_id):
        params = {'location': problem_location, 'student_id': student_id}
        response = self.get(self.get_data_for_location_url, params)
        return self.try_to_decode(response)

    def get_next_submission(self, problem_location, grader_id):
        response = self.get(
            self.get_next_submission_url,
            {
                'location': problem_location,
                'grader_id': grader_id
            }
        )
        return self.try_to_decode(self._render_rubric(response))

    def save_grade(self, **kwargs):
        data = kwargs
        data.update({'rubric_scores_complete': True})
        return self.try_to_decode(self.post(self.save_grade_url, data))

    def is_student_calibrated(self, problem_location, grader_id):
        params = {'problem_id': problem_location, 'student_id': grader_id}
        return self.try_to_decode(self.get(self.is_student_calibrated_url, params))

    def show_calibration_essay(self, problem_location, grader_id):
        params = {'problem_id': problem_location, 'student_id': grader_id}
        response = self.get(self.show_calibration_essay_url, params)
        return self.try_to_decode(self._render_rubric(response))

    def save_calibration_essay(self, **kwargs):
        data = kwargs
        data.update({'rubric_scores_complete': True})
        return self.try_to_decode(self.post(self.save_calibration_essay_url, data))

    def get_problem_list(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_problem_list_url, params)
        return self.try_to_decode(response)

    def get_notifications(self, course_id, grader_id):
        params = {'course_id': course_id, 'student_id': grader_id}
        response = self.get(self.get_notifications_url, params)
        return self.try_to_decode(response)

    def try_to_decode(self, text):
        try:
            text = json.loads(text)
        except:
            pass
        return text


"""
This is a mock peer grading service that can be used for unit tests
without making actual service calls to the grading controller
"""


class MockPeerGradingService(object):
    def get_next_submission(self, problem_location, grader_id):
        return {
            'success': True,
            'submission_id': 1,
            'submission_key': "",
            'student_response': 'Sample student response.',
            'prompt': 'Sample submission prompt.',
            'rubric': 'Placeholder text for the full rubric.',
            'max_score': 4
        }

    def save_grade(self, **kwargs):
        return {'success': True}

    def is_student_calibrated(self, problem_location, grader_id):
        return {'success': True, 'calibrated': True}

    def show_calibration_essay(self, problem_location, grader_id):
        return {'success': True,
                'submission_id': 1,
                'submission_key': '',
                'student_response': 'Sample student response.',
                'prompt': 'Sample submission prompt.',
                'rubric': 'Placeholder text for the full rubric.',
                'max_score': 4}

    def save_calibration_essay(self, **kwargs):
        return {'success': True, 'actual_score': 2}

    def get_problem_list(self, course_id, grader_id):
        return {'success': True,
                'problem_list': [
                ]}

    def get_data_for_location(self, problem_location, student_id):
        return {"version": 1, "count_graded": 3, "count_required": 3, "success": True, "student_sub_count": 1, 'submissions_available' : 0}
