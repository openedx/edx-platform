"""
Constants and Enums used by Grading.
"""


class ScoreDatabaseTableEnum:
    """
    The various database tables that store scores.
    """
    courseware_student_module = 'csm'
    submissions = 'submissions'
    overrides = 'overrides'


class GradeOverrideFeatureEnum:
    proctoring = 'PROCTORING'
    gradebook = 'GRADEBOOK'
    grade_import = 'grade-import'
