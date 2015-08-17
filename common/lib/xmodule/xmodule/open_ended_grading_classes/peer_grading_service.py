import logging
import dogstats_wrapper as dog_stats_api

from .grading_service_module import GradingService
from opaque_keys.edx.keys import UsageKey

log = logging.getLogger(__name__)


class PeerGradingService(GradingService):
    """
    Interface with the grading controller for peer grading
    """

    METRIC_NAME = 'edxapp.open_ended_grading.peer_grading_service'

    def __init__(self, config, render_template):
        config['render_template'] = render_template
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

    def get_data_for_location(self, problem_location, student_id):
        if isinstance(problem_location, UsageKey):
            problem_location = problem_location.to_deprecated_string()
        params = {'location': problem_location, 'student_id': student_id}
        result = self.get(self.get_data_for_location_url, params)
        self._record_result('get_data_for_location', result)
        for key in result.keys():
            if key in ('success', 'error', 'version'):
                continue

            dog_stats_api.histogram(
                self._metric_name('get_data_for_location.{}'.format(key)),
                result[key],
            )
        return result

    def get_next_submission(self, problem_location, grader_id):
        if isinstance(problem_location, UsageKey):
            problem_location = problem_location.to_deprecated_string()
        result = self._render_rubric(self.get(
            self.get_next_submission_url,
            {
                'location': problem_location,
                'grader_id': grader_id
            }
        ))
        self._record_result('get_next_submission', result)
        return result

    def save_grade(self, **kwargs):
        data = kwargs
        data.update({'rubric_scores_complete': True})
        result = self.post(self.save_grade_url, data)
        self._record_result('save_grade', result)
        return result

    def is_student_calibrated(self, problem_location, grader_id):
        if isinstance(problem_location, UsageKey):
            problem_location = problem_location.to_deprecated_string()
        params = {'problem_id': problem_location, 'student_id': grader_id}
        result = self.get(self.is_student_calibrated_url, params)
        self._record_result(
            'is_student_calibrated',
            result,
            tags=['calibrated:{}'.format(result.get('calibrated'))]
        )
        return result

    def show_calibration_essay(self, problem_location, grader_id):
        if isinstance(problem_location, UsageKey):
            problem_location = problem_location.to_deprecated_string()
        params = {'problem_id': problem_location, 'student_id': grader_id}
        result = self._render_rubric(self.get(self.show_calibration_essay_url, params))
        self._record_result('show_calibration_essay', result)
        return result

    def save_calibration_essay(self, **kwargs):
        data = kwargs
        data.update({'rubric_scores_complete': True})
        result = self.post(self.save_calibration_essay_url, data)
        self._record_result('show_calibration_essay', result)
        return result

    def get_problem_list(self, course_id, grader_id):
        params = {'course_id': course_id.to_deprecated_string(), 'student_id': grader_id}
        result = self.get(self.get_problem_list_url, params)

        if 'problem_list' in result:
            for problem in result['problem_list']:
                problem['location'] = course_id.make_usage_key_from_deprecated_string(problem['location'])

        self._record_result('get_problem_list', result)
        dog_stats_api.histogram(
            self._metric_name('get_problem_list.result.length'),
            len(result.get('problem_list', [])),
        )
        return result

    def get_notifications(self, course_id, grader_id):
        params = {'course_id': course_id.to_deprecated_string(), 'student_id': grader_id}
        result = self.get(self.get_notifications_url, params)
        self._record_result(
            'get_notifications',
            result,
            tags=['needs_to_peer_grade:{}'.format(result.get('student_needs_to_peer_grade'))]
        )
        return result


class MockPeerGradingService(object):
    """
    This is a mock peer grading service that can be used for unit tests
    without making actual service calls to the grading controller
    """

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
        return {
            "version": 1,
            "count_graded": 3,
            "count_required": 3,
            "success": True,
            "student_sub_count": 1,
            'submissions_available': 0,
        }
