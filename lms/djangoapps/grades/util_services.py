"A light weight interface to grading helper functions"


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
