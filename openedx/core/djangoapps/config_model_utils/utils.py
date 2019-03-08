"""utils for feature-based enrollments"""
from experiments.models import ExperimentData
from openedx.features.course_duration_limits.config import (
    EXPERIMENT_ID,
    EXPERIMENT_DATA_HOLDBACK_KEY
)


def is_in_holdback(user):
    """
    Return true if given user is in holdback expermiment
    """
    in_holdback = False
    if user and user.is_authenticated:
        if 'experimentdata' in getattr(user, '_prefetched_objects_cache', {}):
            for experiment_data in user.experimentdata_set.all():
                if (
                    experiment_data.experiment_id == EXPERIMENT_ID and
                    experiment_data.key == EXPERIMENT_DATA_HOLDBACK_KEY
                ):
                    in_holdback = experiment_data.value == 'True'
                    break
        else:
            try:
                holdback_value = ExperimentData.objects.get(
                    user=user,
                    experiment_id=EXPERIMENT_ID,
                    key=EXPERIMENT_DATA_HOLDBACK_KEY,
                ).value
            except ExperimentData.DoesNotExist:
                pass
            else:
                in_holdback = holdback_value == 'True'

    return in_holdback
