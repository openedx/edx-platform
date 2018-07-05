"""
Django ORM model specifications for the Course Structures sub-application
"""
import json
import logging

from collections import OrderedDict
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKey

from util.models import CompressedTextField


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
