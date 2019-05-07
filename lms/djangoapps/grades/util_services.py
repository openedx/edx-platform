"A light weight interface to grading helper functions"

import six
from courseware.models import StudentModule

from . import grade_utils, tasks


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

    def process_score_csv(self, block_id, score_file, block_weight, sync=True):
        """
        Process the score CSV upload, synchronously or async.
        """
        if sync:
            return grade_utils.process_score_csv(block_id, score_file, block_weight)
        else:
            from django.core.files.storage import default_storage
            filename = 'csv/import/%s' % block_id
            default_storage.save(filename, score_file)
            return tasks.process_score_csv_async.delay(six.text_type(block_id), filename, block_weight)
