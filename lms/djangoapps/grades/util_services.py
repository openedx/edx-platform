"A light weight interface to grading helper functions"

import six

from courseware.models import StudentModule

from . import grade_utils


class GradesUtilService(object):
    """
    An interface to be used by xblocks.
    """
    def __init__(self, **kwargs):
        super(GradesUtilService, self).__init__()
        self.course_id = kwargs.get('course_id', None)

    def are_grades_frozen(self):
        "Check if grades are frozen for given course key"
        return grade_utils.are_grades_frozen(self.course_id)

    def get_score(self, usage_key, user_id):
        """
        Return score for user_id and usage_key.
        """
        return grade_utils.get_score(usage_key, user_id)

    def get_scores(self, usage_key, user_ids=None):
        """
        Return dictionary of student_id: scores.
        """
        return grade_utils.get_scores(usage_key, user_ids)

    def set_score(self, usage_key, student_id, score, max_points, **defaults):
        """
        Set a score.
        """
        return set_score(usage_key, student_id, score, max_points, **defaults)

    def get_score_processor(self, **kwargs):
        """
        Return a csv score processor.
        """
        return grade_utils.ScoreCSVProcessor(**kwargs)
