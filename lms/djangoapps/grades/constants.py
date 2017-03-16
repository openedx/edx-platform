"""
Constants and Enums used by Grading.
"""

from enum import Enum

class ScoreDatabaseTableEnum(object):
    """
    The various database tables that store scores.
    """
    courseware_student_module = 'csm'
    submissions = 'submissions'


class AccessModeEnum(Enum):
    """
    Access modes for grade calculation.
    """
    read_only = 'read_only'
    read_write = 'read_write'
    read_write_if_engaged = 'read_write_if_engaged'
