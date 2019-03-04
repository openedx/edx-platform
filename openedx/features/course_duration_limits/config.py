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
