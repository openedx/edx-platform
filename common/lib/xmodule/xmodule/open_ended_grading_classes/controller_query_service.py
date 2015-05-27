import dogstats_wrapper as dog_stats_api

import logging
from .grading_service_module import GradingService

log = logging.getLogger(__name__)


class ControllerQueryService(GradingService):
    """
    Interface to controller query backend.
    """

    METRIC_NAME = 'edxapp.open_ended_grading.controller_query_service'

    def __init__(self, config, render_template):
        config['render_template'] = render_template
        super(ControllerQueryService, self).__init__(config)
        self.url = config['url'] + config['grading_controller']
        self.login_url = self.url + '/login/'
        self.check_eta_url = self.url + '/get_submission_eta/'
        self.combined_notifications_url = self.url + '/combined_notifications/'
        self.grading_status_list_url = self.url + '/get_grading_status_list/'
        self.flagged_problem_list_url = self.url + '/get_flagged_problem_list/'
        self.take_action_on_flags_url = self.url + '/take_action_on_flags/'

    def check_for_eta(self, location):
        params = {
            'location': location,
        }
        data = self.get(self.check_eta_url, params)
        self._record_result('check_for_eta', data)
        dog_stats_api.histogram(self._metric_name('check_for_eta.eta'), data.get('eta', 0))

        return data

    def check_combined_notifications(self, course_id, student_id, user_is_staff, last_time_viewed):
        params = {
            'student_id': student_id,
            'course_id': course_id.to_deprecated_string(),
            'user_is_staff': user_is_staff,
            'last_time_viewed': last_time_viewed,
        }
        log.debug(self.combined_notifications_url)
        data = self.get(self.combined_notifications_url, params)

        tags = [u'course_id:{}'.format(course_id.to_deprecated_string()), u'user_is_staff:{}'.format(user_is_staff)]
        tags.extend(
            u'{}:{}'.format(key, value)
            for key, value in data.items()
            if key not in ('success', 'version', 'error')
        )
        self._record_result('check_combined_notifications', data, tags)
        return data

    def get_grading_status_list(self, course_id, student_id):
        params = {
            'student_id': student_id,
            'course_id': course_id.to_deprecated_string(),
        }

        data = self.get(self.grading_status_list_url, params)

        tags = [u'course_id:{}'.format(course_id.to_deprecated_string())]
        self._record_result('get_grading_status_list', data, tags)
        dog_stats_api.histogram(
            self._metric_name('get_grading_status_list.length'),
            len(data.get('problem_list', [])),
            tags=tags
        )
        return data

    def get_flagged_problem_list(self, course_id):
        params = {
            'course_id': course_id.to_deprecated_string(),
        }

        data = self.get(self.flagged_problem_list_url, params)

        tags = [u'course_id:{}'.format(course_id.to_deprecated_string())]
        self._record_result('get_flagged_problem_list', data, tags)
        dog_stats_api.histogram(
            self._metric_name('get_flagged_problem_list.length'),
            len(data.get('flagged_submissions', []))
        )
        return data

    def take_action_on_flags(self, course_id, student_id, submission_id, action_type):
        params = {
            'course_id': course_id.to_deprecated_string(),
            'student_id': student_id,
            'submission_id': submission_id,
            'action_type': action_type
        }

        data = self.post(self.take_action_on_flags_url, params)

        tags = [u'course_id:{}'.format(course_id.to_deprecated_string()), u'action_type:{}'.format(action_type)]
        self._record_result('take_action_on_flags', data, tags)
        return data


class MockControllerQueryService(object):
    """
    Mock controller query service for testing
    """

    def __init__(self, config, render_template):
        pass

    def check_for_eta(self, *args, **kwargs):
        """
        Mock later if needed.  Stub function for now.
        @param params:
        @return:
        """
        pass

    def check_combined_notifications(self, *args, **kwargs):
        combined_notifications = {
            "flagged_submissions_exist": False,
            "version": 1,
            "new_student_grading_to_view": False,
            "success": True,
            "staff_needs_to_grade": False,
            "student_needs_to_peer_grade": True,
            "overall_need_to_check": True
        }
        return combined_notifications

    def get_grading_status_list(self, *args, **kwargs):
        grading_status_list = {
            "version": 1,
            "problem_list": [
                {
                    "problem_name": "Science Question -- Machine Assessed",
                    "grader_type": "NA",
                    "eta_available": True,
                    "state": "Waiting to be Graded",
                    "eta": 259200,
                    "location": "i4x://MITx/oe101x/combinedopenended/Science_SA_ML"
                }, {
                    "problem_name": "Humanities Question -- Peer Assessed",
                    "grader_type": "NA",
                    "eta_available": True,
                    "state": "Waiting to be Graded",
                    "eta": 259200,
                    "location": "i4x://MITx/oe101x/combinedopenended/Humanities_SA_Peer"
                }
            ],
            "success": True
        }
        return grading_status_list

    def get_flagged_problem_list(self, *args, **kwargs):
        flagged_problem_list = {
            "version": 1,
            "success": False,
            "error": "No flagged submissions exist for course: MITx/oe101x/2012_Fall"
        }
        return flagged_problem_list

    def take_action_on_flags(self, *args, **kwargs):
        """
        Mock later if needed.  Stub function for now.
        @param params:
        @return:
        """
        pass


def convert_seconds_to_human_readable(seconds):
    if seconds < 60:
        human_string = "{0} seconds".format(seconds)
    elif seconds < 60 * 60:
        human_string = "{0} minutes".format(round(seconds / 60, 1))
    elif seconds < (24 * 60 * 60):
        human_string = "{0} hours".format(round(seconds / (60 * 60), 1))
    else:
        human_string = "{0} days".format(round(seconds / (60 * 60 * 24), 1))

    return human_string
