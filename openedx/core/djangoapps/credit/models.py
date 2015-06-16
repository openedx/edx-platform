# -*- coding: utf-8 -*-
"""
Models for Credit Eligibility for courses.

Credit courses allow students to receive university credit for
successful completion of a course on EdX
"""

import logging

from django.db import models
from django.db import transaction
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords


from jsonfield.fields import JSONField
from model_utils.models import TimeStampedModel
from xmodule_django.models import CourseKeyField
from django.utils.translation import ugettext_lazy


log = logging.getLogger(__name__)


class CreditProvider(TimeStampedModel):
    """This model represents an institution that can grant credit for a course.

    Each provider is identified by unique ID (e.g., 'ASU'). CreditProvider also
    includes a `url` where the student will be sent when he/she will try to
    get credit for course. Eligibility duration will be use to set duration
    for which credit eligible message appears on dashboard.
    """
    provider_id = models.CharField(
        max_length=255,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z,A-Z,0-9,\-]+$",
                message="Only alphanumeric characters and hyphens (-) are allowed",
                code="invalid_provider_id",
            )
        ],
        help_text=ugettext_lazy(
            "Unique identifier for this credit provider. "
            "Only alphanumeric characters and hyphens (-) are allowed. "
            "The identifier is case-sensitive."
        )
    )

    active = models.BooleanField(
        default=True,
        help_text=ugettext_lazy("Whether the credit provider is currently enabled.")
    )

    display_name = models.CharField(
        max_length=255,
        help_text=ugettext_lazy("Name of the credit provider displayed to users")
    )

    enable_integration = models.BooleanField(
        default=False,
        help_text=ugettext_lazy(
            "When true, automatically notify the credit provider "
            "when a user requests credit. "
            "In order for this to work, a shared secret key MUST be configured "
            "for the credit provider in secure auth settings."
        )
    )

    provider_url = models.URLField(
        default="",
        help_text=ugettext_lazy(
            "URL of the credit provider.  If automatic integration is "
            "enabled, this will the the end-point that we POST to "
            "to notify the provider of a credit request.  Otherwise, the "
            "user will be shown a link to this URL, so the user can "
            "request credit from the provider directly."
        )
    )

    # Default is one year
    DEFAULT_ELIGIBILITY_DURATION = 31556970

    eligibility_duration = models.PositiveIntegerField(
        help_text=ugettext_lazy(u"Number of seconds to show eligibility message"),
        default=DEFAULT_ELIGIBILITY_DURATION
    )


class CreditCourse(models.Model):
    """
    Model for tracking a credit course.
    """

    course_key = CourseKeyField(max_length=255, db_index=True, unique=True)
    enabled = models.BooleanField(default=False)
    providers = models.ManyToManyField(CreditProvider)

    @classmethod
    def is_credit_course(cls, course_key):
        """Check that given course is credit or not.

        Args:
            course_key(CourseKey): The course identifier

        Returns:
            Bool True if the course is marked credit else False
        """
        return cls.objects.filter(course_key=course_key, enabled=True).exists()

    @classmethod
    def get_credit_course(cls, course_key):
        """Get the credit course if exists for the given 'course_key'.

        Args:
            course_key(CourseKey): The course identifier

        Raises:
            DoesNotExist if no CreditCourse exists for the given course key.

        Returns:
            CreditCourse if one exists for the given course key.
        """
        return cls.objects.get(course_key=course_key, enabled=True)


class CreditRequirement(TimeStampedModel):
    """
    This model represents a credit requirement.

    Each requirement is uniquely identified by its 'namespace' and
    'name' fields.
    The 'name' field stores the unique name or location (in case of XBlock)
    for a requirement, which serves as the unique identifier for that
    requirement.
    The 'display_name' field stores the display name of the requirement.
    The 'criteria' field dictionary provides additional information, clients
    may need to determine whether a user has satisfied the requirement.
    """

    course = models.ForeignKey(CreditCourse, related_name="credit_requirements")
    namespace = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, default="")
    criteria = JSONField()
    active = models.BooleanField(default=True)

    class Meta(object):
        """
        Model metadata.
        """
        unique_together = ('namespace', 'name', 'course')

    @classmethod
    def add_or_update_course_requirement(cls, credit_course, requirement):
        """
        Add requirement to a given course.

        Args:
            credit_course(CreditCourse): The identifier for credit course
            requirement(dict): Requirement dict to be added

        Returns:
            (CreditRequirement, created) tuple
        """

        credit_requirement, created = cls.objects.get_or_create(
            course=credit_course,
            namespace=requirement["namespace"],
            name=requirement["name"],
            display_name=requirement["display_name"],
            defaults={"criteria": requirement["criteria"], "active": True}
        )
        if not created:
            credit_requirement.criteria = requirement["criteria"]
            credit_requirement.active = True
            credit_requirement.save()

        return credit_requirement, created

    @classmethod
    def get_course_requirements(cls, course_key, namespace=None):
        """
        Get credit requirements of a given course.

        Args:
            course_key(CourseKey): The identifier for a course
            namespace(str): Namespace of credit course requirements

        Returns:
            QuerySet of CreditRequirement model
        """
        requirements = CreditRequirement.objects.filter(course__course_key=course_key, active=True)
        if namespace:
            requirements = requirements.filter(namespace=namespace)
        return requirements

    @classmethod
    def disable_credit_requirements(cls, requirement_ids):
        """
        Mark the given requirements inactive.

        Args:
            requirement_ids(list): List of ids

        Returns:
            None
        """
        cls.objects.filter(id__in=requirement_ids).update(active=False)

    @classmethod
    def get_course_requirement(cls, course_key, namespace, name):
        """Get credit requirement of a given course.

        Args:
            course_key(CourseKey): The identifier for a course
            namespace(str): Namespace of credit course requirements
            name(str): Name of credit course requirement

        Returns:
            CreditRequirement object if exists

        """
        try:
            return cls.objects.get(
                course__course_key=course_key, active=True, namespace=namespace, name=name
            )
        except cls.DoesNotExist:
            return None


class CreditRequirementStatus(TimeStampedModel):
    """
    This model represents the status of each requirement.

    For a particular credit requirement, a user can either:
    1) Have satisfied the requirement (example: approved in-course reverification)
    2) Have failed the requirement (example: denied in-course reverification)
    3) Neither satisfied nor failed (example: the user hasn't yet attempted in-course reverification).

    Cases (1) and (2) are represented by having a CreditRequirementStatus with
    the status set to "satisfied" or "failed", respectively.

    In case (3), no CreditRequirementStatus record will exist for the requirement and user.

    """

    REQUIREMENT_STATUS_CHOICES = (
        ("satisfied", "satisfied"),
        ("failed", "failed"),
    )

    username = models.CharField(max_length=255, db_index=True)
    requirement = models.ForeignKey(CreditRequirement, related_name="statuses")
    status = models.CharField(max_length=32, choices=REQUIREMENT_STATUS_CHOICES)

    # Include additional information about why the user satisfied or failed
    # the requirement.  This is specific to the type of requirement.
    # For example, the minimum grade requirement might record the user's
    # final grade when the user completes the course.  This allows us to display
    # the grade to users later and to send the information to credit providers.
    reason = JSONField(default={})

    class Meta(object):  # pylint: disable=missing-docstring
        get_latest_by = "created"

    @classmethod
    def get_statuses(cls, requirements, username):
        """ Get credit requirement statuses of given requirement and username

        Args:
            requirement(CreditRequirement): The identifier for a requirement
            username(str): username of the user

        Returns:
            Queryset 'CreditRequirementStatus' objects
        """
        return cls.objects.filter(requirement__in=requirements, username=username)

    @classmethod
    @transaction.commit_on_success
    def add_or_update_requirement_status(cls, username, requirement, status="satisfied", reason=None):
        """Add credit requirement status for given username.

        Args:
            username(str): Username of the user
            requirement(CreditRequirement): 'CreditRequirement' object
            status(str): Status of the requirement
            reason(dict): Reason of the status

        """
        requirement_status, created = cls.objects.get_or_create(
            username=username,
            requirement=requirement,
            defaults={"reason": reason, "status": status}
        )
        if not created:
            requirement_status.status = status
            requirement_status.reason = reason if reason else {}
            requirement_status.save()


class CreditEligibility(TimeStampedModel):
    """
    A record of a user's eligibility for credit from a specific credit
    provider for a specific course.
    """
    username = models.CharField(max_length=255, db_index=True)
    course = models.ForeignKey(CreditCourse, related_name="eligibilities")
    provider = models.ForeignKey(CreditProvider, related_name="eligibilities")

    class Meta(object):  # pylint: disable=missing-docstring
        unique_together = ('username', 'course')

    @classmethod
    def is_user_eligible_for_credit(cls, course_key, username):
        """Check if the given user is eligible for the provided credit course

        Args:
            course_key(CourseKey): The course identifier
            username(str): The username of the user

        Returns:
            Bool True if the user eligible for credit course else False
        """
        return cls.objects.filter(course__course_key=course_key, username=username).exists()


class CreditRequest(TimeStampedModel):
    """
    A request for credit from a particular credit provider.

    When a user initiates a request for credit, a CreditRequest record will be created.
    Each CreditRequest is assigned a unique identifier so we can find it when the request
    is approved by the provider.  The CreditRequest record stores the parameters to be sent
    at the time the request is made.  If the user re-issues the request
    (perhaps because the user did not finish filling in forms on the credit provider's site),
    the request record will be updated, but the UUID will remain the same.
    """

    uuid = models.CharField(max_length=32, unique=True, db_index=True)
    username = models.CharField(max_length=255, db_index=True)
    course = models.ForeignKey(CreditCourse, related_name="credit_requests")
    provider = models.ForeignKey(CreditProvider, related_name="credit_requests")
    timestamp = models.DateTimeField(auto_now_add=True)
    parameters = JSONField()

    REQUEST_STATUS_PENDING = "pending"
    REQUEST_STATUS_APPROVED = "approved"
    REQUEST_STATUS_REJECTED = "rejected"

    REQUEST_STATUS_CHOICES = (
        (REQUEST_STATUS_PENDING, "Pending"),
        (REQUEST_STATUS_APPROVED, "Approved"),
        (REQUEST_STATUS_REJECTED, "Rejected"),
    )
    status = models.CharField(
        max_length=255,
        choices=REQUEST_STATUS_CHOICES,
        default=REQUEST_STATUS_PENDING
    )

    history = HistoricalRecords()

    @classmethod
    def credit_requests_for_user(cls, username):
        """
        Retrieve all credit requests for a user.

        Arguments:
            username (unicode): The username of the user.

        Returns: list

        Example Usage:
        >>> CreditRequest.credit_requests_for_user("bob")
        [
            {
                "uuid": "557168d0f7664fe59097106c67c3f847",
                "timestamp": "2015-05-04T20:57:57.987119+00:00",
                "course_key": "course-v1:HogwartsX+Potions101+1T2015",
                "provider": {
                    "id": "HogwartsX",
                    "display_name": "Hogwarts School of Witchcraft and Wizardry",
                },
                "status": "pending"  # or "approved" or "rejected"
            }
        ]

        """

        return [
            {
                "uuid": request.uuid,
                "timestamp": request.modified,
                "course_key": request.course.course_key,
                "provider": {
                    "id": request.provider.provider_id,
                    "display_name": request.provider.display_name
                },
                "status": request.status
            }
            for request in cls.objects.select_related('course', 'provider').filter(username=username)
        ]

    class Meta(object):  # pylint: disable=missing-docstring
        # Enforce the constraint that each user can have exactly one outstanding
        # request to a given provider.  Multiple requests use the same UUID.
        unique_together = ('username', 'course', 'provider')
