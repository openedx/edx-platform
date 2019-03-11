"""
Content type gating waffle flag
"""
import random

from django.dispatch import receiver
from django.db import IntegrityError

from experiments.models import ExperimentData, ExperimentKeyValue
from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE


EXPERIMENT_ID = 11
EXPERIMENT_DATA_HOLDBACK_KEY = 'holdback'
