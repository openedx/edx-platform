"A light weight interface to grading helper functions"

from courseware.models import StudentModule

from .grade_utils import are_grades_frozen


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

    def get_score(self, usage_key, user_id):
        """
        Return score for user_id and usage_key.
        """
        try:
            score = StudentModule.objects.get(
                course_id=usage_key.course_key,
                module_state_key=usage_key,
                student_id=user_id
            )
        except StudentModule.DoesNotExist:
            return None
        else:
            return {
                'grade': score.grade,
                'score': score.grade * (score.max_grade or 1),
                'max_grade': score.max_grade,
                'created': score.created,
                'modified': score.modified
            }

    def get_scores(self, usage_key, user_ids=None):
        """
        Return dictionary of student_id: scores.
        """
        scores_qset = StudentModule.objects.filter(
            course_id=usage_key.course_key,
            module_state_key=usage_key,
        )
        if user_ids:
            scores_qset = scores_qset.filter(student_id__in=user_ids)

        return {row.student_id: {'grade': row.grade,
                                 'score': row.grade * (row.max_grade or 1),
                                 'max_grade': row.max_grade,
                                 'created': row.created,
                                 'modified': row.modified,
                                 'state': row.state} for row in scores_qset}

    def set_score(self, usage_key, student_id, score, max_points, **defaults):
        """
        Set a score.
        """
        defaults['module_type'] = 'problem'
        defaults['grade'] = score / max_points
        defaults['max_grade'] = max_points
        StudentModule.objects.update_or_create(
            student_id=student_id,
            course_id=usage_key.course_key,
            module_state_key=usage_key,
            defaults=defaults)
