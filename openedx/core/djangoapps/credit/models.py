# -*- coding: utf-8 -*-
"""
Models for Credit Eligibility for courses.

Credit courses allow students to receive university credit for
successful completion of a course on EdX
"""

import logging

from django.db import models
from django.db.utils import IntegrityError

from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements
from xmodule_django.models import CourseKeyField


log = logging.getLogger(__name__)


class CreditCourse(models.Model):
    """Model for tracking a credit course."""

    course_key = CourseKeyField(max_length=255, db_index=True, unique=True)
    enabled = models.BooleanField(default=False)

    @classmethod
    def is_credit_course(cls, course_key):
        """ Check that given course is credit or not

        Args:
            course_key(CourseKey): The course identifier

        Returns:
            Bool True if the course is marked credit else False
        """
        return cls.objects.filter(course_key=course_key, enabled=True).exists()

    @classmethod
    def get_credit_course(cls, course_key):
        """ Get the credit course if exists

        Args:
            course_key(CourseKey): The course identifier

        Raises:
            DoesNotExist if no CreditCourse exists for the given course key.

        Returns:
            CreditCourse if one exists for the given course key.
        """
        return cls.objects.get(course_key=course_key, enabled=True)


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

    @classmethod
    def add_course_requirement(cls, credit_course, requirement):
        """ Add requirements to given course
        Args:
            credit_course(CreditCourse): The identifier for credit course course
            requirements(dict): Dict of requirements to be added

        Raises:
            InvalidCreditRequirements if any issue on requirement

        Returns:
            None
        """
        try:
            cls.objects.create(
                course=credit_course,
                namespace=requirement["namespace"],
                name=requirement["name"],
                configuration=requirement["configuration"]
            )
        except IntegrityError:
            # skip the duplicate entry
            pass
        except:  # pylint: disable=bare-except
            raise InvalidCreditRequirements

    @classmethod
    def get_course_requirements(cls, course_key, namespace=None):
        """ Get credit requirements of a given course

        Args:
            course_key(CourseKey): The identifier for a course
            namespace(str): namespace of credit course requirements

        Returns:
            QuerySet of CreditRequirement model
        """
        requirements = CreditRequirement.objects.filter(course__course_key=course_key, active=True)
        if namespace:
            requirements = requirements.filter(namespace=namespace)
        return requirements


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
