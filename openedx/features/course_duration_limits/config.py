"""
Content type gating waffle flag
"""
import random

from django.dispatch import receiver
from django.db import IntegrityError

from experiments.models import ExperimentData, ExperimentKeyValue
from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, WaffleFlag
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE


WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name=u'content_type_gating')

CONTENT_TYPE_GATING_FLAG = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'debug',
    flag_undefined_default=False
)

FEATURE_BASED_ENROLLMENT_GLOBAL_KILL_FLAG = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name=u'global_kill_switch',
    flag_undefined_default=False
)

EXPERIMENT_ID = 11
EXPERIMENT_DATA_HOLDBACK_KEY = 'holdback'


@receiver(ENROLL_STATUS_CHANGE)
def set_value_for_content_type_gating_holdback(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    if event == EnrollStatusChange.enroll:
        user_holdback_data = ExperimentData.objects.filter(
            user=user,
            experiment_id=EXPERIMENT_ID,
            key=EXPERIMENT_DATA_HOLDBACK_KEY,
        )
        user_holdback_data_already_set = user_holdback_data.exists()
        if not user_holdback_data_already_set:
            try:
                content_type_gating_holdback_percentage_value = ExperimentKeyValue.objects.get(
                    experiment_id=EXPERIMENT_ID,
                    key="content_type_gating_holdback_percentage"
                ).value
                content_type_gating_holdback_percentage = float(content_type_gating_holdback_percentage_value) / 100
                is_in_holdback = str(random.random() < content_type_gating_holdback_percentage)

                ExperimentData.objects.create(
                    user=user,
                    experiment_id=EXPERIMENT_ID,
                    key=EXPERIMENT_DATA_HOLDBACK_KEY,
                    value=is_in_holdback
                )
            except (ExperimentKeyValue.DoesNotExist, AttributeError):
                pass
            except IntegrityError:
                # There is a race condition when multiple enrollments happen at the same time where the ExperimentData
                # row for one enrollment is created between the duplicate check and creation for the other enrollment.
                # Since we're ignoring skipping duplicate entries anyway, this is safe to ignore.
                pass
