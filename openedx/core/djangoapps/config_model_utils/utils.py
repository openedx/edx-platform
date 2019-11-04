"""utils for feature-based enrollments"""
from __future__ import absolute_import

from experiments.models import ExperimentData
from openedx.features.course_duration_limits.config import EXPERIMENT_DATA_HOLDBACK_KEY, EXPERIMENT_ID
from student.models import FBEEnrollmentExclusion


def is_in_holdback(user, enrollment):
    """
    Return true if given user is in holdback expermiment
    """
    in_holdback = False
    if user and user.is_authenticated:
        try:
            holdback_value = ExperimentData.objects.get(
                user=user,
                experiment_id=EXPERIMENT_ID,
                key=EXPERIMENT_DATA_HOLDBACK_KEY,
            ).value
            in_holdback = holdback_value == 'True'
        except ExperimentData.DoesNotExist:
            pass

    if enrollment is not None:
        try:
            if enrollment.fbeenrollmentexclusion:
                return True
        except FBEEnrollmentExclusion.DoesNotExist:
            pass

    return in_holdback
