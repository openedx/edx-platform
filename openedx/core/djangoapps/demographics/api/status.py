"""
Python API for Demographics Status
"""

from openedx.features.enterprise_support.utils import is_enterprise_learner
from openedx.core.djangoapps.programs.utils import is_user_enrolled_in_program_type


def show_user_demographics(user):
    # Is the learner enrolled in MicroBachelors Program or is the learner an Enterprise learner?
    is_user_in_microbachelors_program = is_user_enrolled_in_program_type(user, "microbachelors")
    return is_user_in_microbachelors_program and not is_enterprise_learner(user)
