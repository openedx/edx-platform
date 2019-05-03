"A light weight interface to grading helper functions"


from collections import namedtuple
from .grade_utils import are_grades_frozen
from courseware.models import StudentModule


class GradesUtilService(object):
    """
    An interface to be used by xblocks.
    """
    def __init__(self, **kwargs):
        super(GradesUtilService, self).__init__()
        self.course_id = kwargs.get('course_id', None)

    def are_grades_frozen(self):
        "Check if grades are frozen for given course key"
        return are_grades_frozen(self.course_id)

    def get_score(self, user_id, usage_key):
        from courseware.model_data import ScoresClient
        client = ScoresClient(usage_key.course_key, user_id)
        client.fetch_scores([usage_key])
        return client.get(usage_key)

    def get_scores(self, usage_key, user_ids=None):
        scores_qset = StudentModule.objects.filter(
            course_id=usage_key.course_key,
            module_state_key=usage_key,
        )
        if user_ids:
            scores_qset = scores_qset.filter(student_id__in=user_ids)
        UserScore = namedtuple('UserScore', 'student score total created modified')

        for row in scores_qset:
            yield UserScore(row.student, row.grade, row.max_grade, row.created, row.modified)

    def set_score(self, usage_key, student_id, score):
        state = StudentModule.objects.update_or_create(
            student_id=student_id,
            course_id=usage_key.course_key,
            module_state_key=usage_key,
            defaults={
                'module_type': 'problem',
                'grade': score,
            })
