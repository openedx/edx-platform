"""
Constants and Enums used by Grading.
"""


class ScoreDatabaseTableEnum(object):
    """
    The various database tables that store scores.
    """
    courseware_student_module = 'csm'
    submissions = 'submissions'
    overrides = 'overrides'


class GradeOverrideFeatureEnum(object):
    proctoring = u'PROCTORING'
    gradebook = u'GRADEBOOK'
    grade_import = 'grade-import'
