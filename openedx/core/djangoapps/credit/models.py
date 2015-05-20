# -*- coding: utf-8 -*-
"""
Models for Credit Eligibility for courses.

Credit courses allow students to receive university credit for
successful completion of a course on EdX
"""

import logging

from django.db import models
from model_utils.models import TimeStampedModel
from xmodule_django.models import CourseKeyField
from jsonfield.fields import JSONField

log = logging.getLogger(__name__)


class CreditCourse(models.Model):
    """Model for tracking a credit course."""

    course_key = CourseKeyField(max_length=255, db_index=True, unique=True)
    enabled = models.BooleanField(default=False)


class CreditProvider(TimeStampedModel):
    """This model represents an institution that can grant credit for a course.

    Each provider is identified by unique ID (e.g., 'ASU').
    """

    provider_id = models.CharField(max_length=255, db_index=True, unique=True)
    display_name = models.CharField(max_length=255)


class CreditRequirement(TimeStampedModel):
    """This model represents a credit requirement.

    Each requirement is uniquely identified by a `namespace` and a `name`. CreditRequirements
    also include a `configuration` dictionary, the format of which varies by the type of requirement.
    The configuration dictionary provides additional information clients may need to determine
    whether a user has satisfied the requirement.
    """

    course = models.ForeignKey(CreditCourse, related_name="credit_requirements")
    namespace = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    configuration = JSONField()
    active = models.BooleanField(default=True)

    class Meta(object):
        """Model metadata"""
        unique_together = ('namespace', 'name', 'course')


class CreditRequirementStatus(TimeStampedModel):
    """This model represents the status of each requirement."""

    REQUIREMENT_STATUS_CHOICES = (
        ("satisfied", "satisfied"),
    )

    username = models.CharField(max_length=255, db_index=True)
    requirement = models.ForeignKey(CreditRequirement, related_name="statuses")
    status = models.CharField(choices=REQUIREMENT_STATUS_CHOICES, max_length=32)


class CreditEligibility(TimeStampedModel):
    """A record of a user's eligibility for credit from a specific credit
    provider for a specific course.
    """

    username = models.CharField(max_length=255, db_index=True)
    course = models.ForeignKey(CreditCourse, related_name="eligibilities")
    provider = models.ForeignKey(CreditProvider, related_name="eligibilities")

    class Meta(object):
        """Model metadata"""
        unique_together = ('username', 'course')
