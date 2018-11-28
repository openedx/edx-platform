"""
Content type gating waffle flag
"""
import random

from django.dispatch import receiver

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

EXPERIMENT_ID = 11
EXPERIMENT_DATA_HOLDBACK_KEY = 'holdback_{0}'


@receiver(ENROLL_STATUS_CHANGE)
def set_value_for_content_type_gating_holdback(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    experiment_data_holdback_key = EXPERIMENT_DATA_HOLDBACK_KEY.format(user)
    if event == EnrollStatusChange.enroll:
        user_holdback_data = ExperimentData.objects.filter(
            user=user,
            experiment_id=EXPERIMENT_ID,
            key=experiment_data_holdback_key,
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
                    key=experiment_data_holdback_key,
                    value=is_in_holdback
                )
            except (ExperimentKeyValue.DoesNotExist, AttributeError):
                pass
