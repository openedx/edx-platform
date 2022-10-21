"""Models for student course enrollment"""

import crum
import hashlib  # lint-amnesty, pylint: disable=wrong-import-order
import logging  # lint-amnesty, pylint: disable=wrong-import-order
import uuid  # lint-amnesty, pylint: disable=wrong-import-order
from collections import defaultdict, namedtuple  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.course_modes.models import CourseMode, get_cosmetic_verified_display_price
from common.djangoapps.student.signals import ENROLL_STATUS_CHANGE, ENROLLMENT_TRACK_UPDATED, UNENROLL_DONE
from common.djangoapps.track import contexts, segment
from common.djangoapps.util.query import use_read_replica_if_available
from config_models.models import ConfigurationModel
from datetime import date, datetime, timedelta  # lint-amnesty, pylint: disable=wrong-import-order
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Count, Index, Q
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from edx_django_utils.cache import RequestCache, TieredCache, get_cache_key
from eventtracking import tracker
from importlib import import_module  # lint-amnesty, pylint: disable=wrong-import-order
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.courseware.models import (
    CourseDynamicUpgradeDeadlineConfiguration,
    DynamicUpgradeDeadlineConfiguration,
    OrgDynamicUpgradeDeadlineConfiguration,
)
from lms.djangoapps.utils import OptimizelyClient
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.enrollments.api import (
    _default_course_mode,
    get_enrollment_attributes,
    set_enrollment_attributes,
)
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.model_mixins import DeletableByUserValue
from openedx_events.learning.data import CourseData, CourseEnrollmentData, UserData, UserPersonalData
from openedx_events.learning.signals import (
    COURSE_ENROLLMENT_CHANGED,
    COURSE_ENROLLMENT_CREATED,
    COURSE_UNENROLLMENT_COMPLETED,
)
from openedx_filters.learning.filters import CourseEnrollmentStarted, CourseUnenrollmentStarted
from pytz import UTC
from requests.exceptions import HTTPError, RequestException
from simple_history.models import HistoricalRecords
from urllib.parse import urljoin

log = logging.getLogger(__name__)
AUDIT_LOG = logging.getLogger("audit")
SessionStore = import_module(settings.SESSION_ENGINE).SessionStore  # pylint: disable=invalid-name


# ENROLL signal used for free enrollment only
class EnrollStatusChange:
    """
    Possible event types for ENROLL_STATUS_CHANGE signal
    """
    # enroll for a course
    enroll = 'enroll'
    # unenroll for a course
    unenroll = 'unenroll'
    # add an upgrade to cart
    upgrade_start = 'upgrade_start'
    # complete an upgrade purchase
    upgrade_complete = 'upgrade_complete'
    # add a paid course to the cart
    paid_start = 'paid_start'
    # complete a paid course purchase
    paid_complete = 'paid_complete'

UNENROLLED_TO_ALLOWEDTOENROLL = 'from unenrolled to allowed to enroll'
ALLOWEDTOENROLL_TO_ENROLLED = 'from allowed to enroll to enrolled'
ENROLLED_TO_ENROLLED = 'from enrolled to enrolled'
ENROLLED_TO_UNENROLLED = 'from enrolled to unenrolled'
UNENROLLED_TO_ENROLLED = 'from unenrolled to enrolled'
ALLOWEDTOENROLL_TO_UNENROLLED = 'from allowed to enroll to enrolled'
UNENROLLED_TO_UNENROLLED = 'from unenrolled to unenrolled'
DEFAULT_TRANSITION_STATE = 'N/A'
SCORE_RECALCULATION_DELAY_ON_ENROLLMENT_UPDATE = 30

TRANSITION_STATES = (
    (UNENROLLED_TO_ALLOWEDTOENROLL, UNENROLLED_TO_ALLOWEDTOENROLL),
    (ALLOWEDTOENROLL_TO_ENROLLED, ALLOWEDTOENROLL_TO_ENROLLED),
    (ENROLLED_TO_ENROLLED, ENROLLED_TO_ENROLLED),
    (ENROLLED_TO_UNENROLLED, ENROLLED_TO_UNENROLLED),
    (UNENROLLED_TO_ENROLLED, UNENROLLED_TO_ENROLLED),
    (ALLOWEDTOENROLL_TO_UNENROLLED, ALLOWEDTOENROLL_TO_UNENROLLED),
    (UNENROLLED_TO_UNENROLLED, UNENROLLED_TO_UNENROLLED),
    (DEFAULT_TRANSITION_STATE, DEFAULT_TRANSITION_STATE)
)

EVENT_NAME_ENROLLMENT_ACTIVATED = 'edx.course.enrollment.activated'
EVENT_NAME_ENROLLMENT_DEACTIVATED = 'edx.course.enrollment.deactivated'
EVENT_NAME_ENROLLMENT_MODE_CHANGED = 'edx.course.enrollment.mode_changed'


class CourseEnrollmentException(Exception):
    pass


class NonExistentCourseError(CourseEnrollmentException):
    pass


class EnrollmentClosedError(CourseEnrollmentException):
    pass


class CourseFullError(CourseEnrollmentException):
    pass


class AlreadyEnrolledError(CourseEnrollmentException):
    pass


class EnrollmentNotAllowed(CourseEnrollmentException):
    pass


class UnenrollmentNotAllowed(CourseEnrollmentException):
    pass


class CourseEnrollmentManager(models.Manager):
    """
    Custom manager for CourseEnrollment with Table-level filter methods.
    """

    def is_small_course(self, course_id):
        """
        Returns false if the number of enrollments are one greater than 'max_enrollments' else true

        'course_id' is the course_id to return enrollments
        """
        max_enrollments = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")

        enrollment_number = super().get_queryset().filter(
            course_id=course_id,
            is_active=1
        )[:max_enrollments + 1].count()

        return enrollment_number <= max_enrollments

    def num_enrolled_in_exclude_admins(self, course_id):
        """
        Returns the count of active enrollments in a course excluding instructors, staff and CCX coaches.

        Arguments:
            course_id (CourseLocator): course_id to return enrollments (count).

        Returns:
            int: Count of enrollments excluding staff, instructors and CCX coaches.

        """
        # To avoid circular imports.
        from common.djangoapps.student.roles import CourseCcxCoachRole, CourseInstructorRole, CourseStaffRole
        course_locator = course_id

        if getattr(course_id, 'ccx', None):
            course_locator = course_id.to_course_locator()

        staff = CourseStaffRole(course_locator).users_with_role()
        admins = CourseInstructorRole(course_locator).users_with_role()
        coaches = CourseCcxCoachRole(course_locator).users_with_role()

        return super().get_queryset().filter(
            course_id=course_id,
            is_active=1,
        ).exclude(user__in=staff).exclude(user__in=admins).exclude(user__in=coaches).count()

    def is_course_full(self, course):
        """
        Returns a boolean value regarding whether a course has already reached it's max enrollment
        capacity
        """
        is_course_full = False
        if course.max_student_enrollments_allowed is not None:
            is_course_full = self.num_enrolled_in_exclude_admins(course.id) >= course.max_student_enrollments_allowed

        return is_course_full

    def users_enrolled_in(self, course_id, include_inactive=False, verified_only=False):
        """
        Return a queryset of User for every user enrolled in the course.

        Arguments:
            course_id (CourseLocator): course_id to return enrollees for.
            include_inactive (boolean): is a boolean when True, returns both active and inactive enrollees
            verified_only (boolean): is a boolean when True, returns only verified enrollees.

        Returns:
            Returns a User queryset.
        """
        filter_kwargs = {
            'courseenrollment__course_id': course_id,
        }
        if not include_inactive:
            filter_kwargs['courseenrollment__is_active'] = True
        if verified_only:
            filter_kwargs['courseenrollment__mode'] = CourseMode.VERIFIED
        return User.objects.filter(**filter_kwargs)

    def enrollment_counts(self, course_id):
        """
        Returns a dictionary that stores the total enrollment count for a course, as well as the
        enrollment count for each individual mode.
        """
        # Unfortunately, Django's "group by"-style queries look super-awkward
        query = use_read_replica_if_available(
            super().get_queryset().filter(course_id=course_id, is_active=True).values(
                'mode').order_by().annotate(Count('mode')))
        total = 0
        enroll_dict = defaultdict(int)
        for item in query:
            enroll_dict[item['mode']] = item['mode__count']
            total += item['mode__count']
        enroll_dict['total'] = total
        return enroll_dict

    def enrolled_and_dropped_out_users(self, course_id):
        """Return a queryset of Users in the course."""
        return User.objects.filter(
            courseenrollment__course_id=course_id
        )

    @classmethod
    def cache_key_name(cls, user_id, course_key):
        """Return cache key name to be used to cache current configuration.
        Args:
            user_id(int): Id of user.
            course_key(unicode): Unicode of course key

        Returns:
            Unicode cache key
        """
        return cls.COURSE_ENROLLMENT_CACHE_KEY.format(user_id, str(course_key))

    @classmethod
    def _get_enrollment_state(cls, user, course_key):
        """
        Returns the CourseEnrollmentState for the given user
        and course_key, caching the result for later retrieval.
        """
        assert user

        if user.is_anonymous:
            return CourseEnrollmentState(None, None)
        enrollment_state = cls._get_enrollment_in_request_cache(user, course_key)
        if not enrollment_state:
            try:
                record = cls.objects.get(user=user, course_id=course_key)
                enrollment_state = CourseEnrollmentState(record.mode, record.is_active)
            except cls.DoesNotExist:
                enrollment_state = CourseEnrollmentState(None, None)
            cls._update_enrollment_in_request_cache(user, course_key, enrollment_state)
        return enrollment_state

    @classmethod
    def bulk_fetch_enrollment_states(cls, users, course_key):
        """
        Bulk pre-fetches the enrollment states for the given users
        for the given course.
        """
        # before populating the cache with another bulk set of data,
        # remove previously cached entries to keep memory usage low.
        RequestCache(cls.MODE_CACHE_NAMESPACE).clear()

        records = cls.objects.filter(user__in=users, course_id=course_key).select_related('user')
        cache = cls._get_mode_active_request_cache()  # lint-amnesty, pylint: disable=redefined-outer-name
        for record in records:
            enrollment_state = CourseEnrollmentState(record.mode, record.is_active)
            cls._update_enrollment(cache, record.user.id, course_key, enrollment_state)

    @classmethod
    def _get_mode_active_request_cache(cls):
        """
        Returns the request-specific cache for CourseEnrollment as dict.
        """
        return RequestCache(cls.MODE_CACHE_NAMESPACE).data

    @classmethod
    def _get_enrollment_in_request_cache(cls, user, course_key):
        """
        Returns the cached value (CourseEnrollmentState) for the user's
        enrollment in the request cache.  If not cached, returns None.
        """
        return cls._get_mode_active_request_cache().get((user.id, course_key))

    @classmethod
    def _update_enrollment_in_request_cache(cls, user, course_key, enrollment_state):
        """
        Updates the cached value for the user's enrollment in the
        request cache.
        """
        cls._update_enrollment(cls._get_mode_active_request_cache(), user.id, course_key, enrollment_state)

    @classmethod
    def _update_enrollment(cls, cache, user_id, course_key, enrollment_state):  # lint-amnesty, pylint: disable=redefined-outer-name
        """
        Updates the cached value for the user's enrollment in the
        given cache.
        """
        cache[(user_id, course_key)] = enrollment_state

    @classmethod
    def get_active_enrollments_in_course(cls, course_key):
        """
        Retrieves active CourseEnrollments for a given course and
        prefetches user information.
        """
        return cls.objects.filter(
            course_id=course_key,
            is_active=True,
        ).select_related(
            'user',
            'user__profile',
        )


class FBEEnrollmentExclusion(models.Model):
    """
    Disable FBE for enrollments in this table.

    .. no_pii:
    """
    enrollment = models.OneToOneField(
        CourseEnrollment,
        on_delete=models.DO_NOTHING,
    )

    def __str__(self):
        return f"[FBEEnrollmentExclusion] {self.enrollment}"


@receiver(models.signals.post_save, sender=CourseEnrollment)
@receiver(models.signals.post_delete, sender=CourseEnrollment)
def invalidate_enrollment_mode_cache(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Invalidate the cache of CourseEnrollment model.
    """

    cache_key = CourseEnrollment.cache_key_name(
        instance.user.id,
        str(instance.course_id)
    )
    cache.delete(cache_key)


@receiver(models.signals.post_save, sender=CourseEnrollment)
def update_expiry_email_date(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    If the user has enrolled in verified track of a course and has expired ID
    verification then send email to get the ID verified by setting the
    expiry_email_date field.
    """
    email_config = getattr(settings, 'VERIFICATION_EXPIRY_EMAIL', {'DAYS_RANGE': 1, 'RESEND_DAYS': 15})

    if instance.mode == CourseMode.VERIFIED:
        SoftwareSecurePhotoVerification.update_expiry_email_date_for_user(instance.user, email_config)


class ManualEnrollmentAudit(models.Model):
    """
    Table for tracking which enrollments were performed through manual enrollment.

    .. pii: Contains enrolled_email, retired in LMSAccountRetirementView
    .. pii_types: email_address
    .. pii_retirement: local_api
    """
    enrollment = models.ForeignKey(CourseEnrollment, null=True, on_delete=models.CASCADE)
    enrolled_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    enrolled_email = models.CharField(max_length=255, db_index=True)
    time_stamp = models.DateTimeField(auto_now_add=True, null=True)
    state_transition = models.CharField(max_length=255, choices=TRANSITION_STATES)
    reason = models.TextField(null=True)
    role = models.CharField(blank=True, null=True, max_length=64)
    history = HistoricalRecords()

    @classmethod
    def create_manual_enrollment_audit(cls, user, email, state_transition, reason, enrollment=None, role=None):
        """
        saves the student manual enrollment information
        """
        return cls.objects.create(
            enrolled_by=user,
            enrolled_email=email,
            state_transition=state_transition,
            reason=reason,
            enrollment=enrollment,
            role=role,
        )

    @classmethod
    def get_manual_enrollment_by_email(cls, email):
        """
        if matches returns the most recent entry in the table filtered by email else returns None.
        """
        try:
            manual_enrollment = cls.objects.filter(enrolled_email=email).latest('time_stamp')
        except cls.DoesNotExist:
            manual_enrollment = None
        return manual_enrollment

    @classmethod
    def get_manual_enrollment(cls, enrollment):
        """
        Returns the most recent entry for the given enrollment, or None if there are no matches
        """
        try:
            manual_enrollment = cls.objects.filter(enrollment=enrollment).latest('time_stamp')
        except cls.DoesNotExist:
            manual_enrollment = None
        return manual_enrollment

    @classmethod
    def retire_manual_enrollments(cls, user, retired_email):
        """
        Removes PII (enrolled_email and reason) associated with the User passed in. Bubbles up any exceptions.
        """
        # This bit of ugliness is to fix a perfmance issue with Django using a slow
        # sub-select that caused the original query to take several seconds (PLAT-2371).
        # It is possible that this could also be bad if a user has thousands of manual
        # enrollments, but currently that number tends to be very low.
        manual_enrollment_ids = list(cls.objects.filter(enrollment__user=user).values_list('id', flat=True))
        manual_enrollment_audits = cls.objects.filter(id__in=manual_enrollment_ids)

        if not manual_enrollment_audits:
            return False

        for manual_enrollment_audit in manual_enrollment_audits:
            manual_enrollment_audit.history.update(reason="", enrolled_email=retired_email)
        manual_enrollment_audits.update(reason="", enrolled_email=retired_email)
        return True


class CourseEnrollmentAllowed(DeletableByUserValue, models.Model):
    """
    Table of users (specified by email address strings) who are allowed to enroll in a specified course.
    The user may or may not (yet) exist.  Enrollment by users listed in this table is allowed
    even if the enrollment time window is past.  Once an enrollment from this list effectively happens,
    the object is marked with the student who enrolled, to prevent students from changing e-mails and
    enrolling many accounts through the same e-mail.

    .. no_pii:
    """
    email = models.CharField(max_length=255, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    auto_enroll = models.BooleanField(default=0)
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        help_text="First user which enrolled in the specified course through the specified e-mail. "
                  "Once set, it won't change.",
        on_delete=models.CASCADE,
    )

    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)

    class Meta:
        unique_together = (('email', 'course_id'),)

    def __str__(self):
        return f"[CourseEnrollmentAllowed] {self.email}: {self.course_id} ({self.created})"

    @classmethod
    def for_user(cls, user):
        """
        Returns the CourseEnrollmentAllowed objects that can effectively be used by a particular `user`.
        This includes the ones that match the user's e-mail and excludes those CEA which were already consumed
        by a different user.
        """
        return cls.objects.filter(email=user.email).filter(Q(user__isnull=True) | Q(user=user))

    def valid_for_user(self, user):
        """
        Returns True if the CEA is usable by the given user, or False if it was already consumed by another user.
        """
        return self.user is None or self.user == user

    @classmethod
    def may_enroll_and_unenrolled(cls, course_id):
        """
        Return QuerySet of students who are allowed to enroll in a course.

        Result excludes students who have already enrolled in the
        course. Even if they change their emails after registration.

        `course_id` identifies the course for which to compute the QuerySet.
        """
        return CourseEnrollmentAllowed.objects.filter(course_id=course_id, user__isnull=True)


class CourseEnrollmentAttribute(models.Model):
    """
    Provide additional information about the user's enrollment.

    .. no_pii: This stores key/value pairs, of which there is no full list, but the ones currently in use are not PII
    """
    enrollment = models.ForeignKey(CourseEnrollment, related_name="attributes", on_delete=models.CASCADE)
    namespace = models.CharField(
        max_length=255,
        help_text=_("Namespace of enrollment attribute")
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Name of the enrollment attribute")
    )
    value = models.CharField(
        max_length=255,
        help_text=_("Value of the enrollment attribute")
    )

    def __str__(self):
        """Unicode representation of the attribute. """
        return "{namespace}:{name}, {value}".format(
            namespace=self.namespace,
            name=self.name,
            value=self.value,
        )

    @classmethod
    def add_enrollment_attr(cls, enrollment, data_list):
        """
        Delete all the enrollment attributes for the given enrollment and
        add new attributes.

        Args:
            enrollment (CourseEnrollment): 'CourseEnrollment' for which attribute is to be added
            data_list: list of dictionaries containing data to save
        """
        cls.objects.filter(enrollment=enrollment).delete()
        attributes = [
            cls(enrollment=enrollment, namespace=data['namespace'], name=data['name'], value=data['value'])
            for data in data_list
        ]
        cls.objects.bulk_create(attributes)

    @classmethod
    def get_enrollment_attributes(cls, enrollment):
        """Retrieve list of all enrollment attributes.

        Args:
            enrollment(CourseEnrollment): 'CourseEnrollment' for which list is to retrieve

        Returns: list

        Example:
        >>> CourseEnrollmentAttribute.get_enrollment_attributes(CourseEnrollment)
        [
            {
                "namespace": "credit",
                "name": "provider_id",
                "value": "hogwarts",
            },
        ]
        """
        return [
            {
                "namespace": attribute.namespace,
                "name": attribute.name,
                "value": attribute.value,
            }
            for attribute in cls.objects.filter(enrollment=enrollment)
        ]


class EnrollmentRefundConfiguration(ConfigurationModel):
    """
    Configuration for course enrollment refunds.

    .. no_pii:
    """

    # TODO: Django 1.8 introduces a DurationField
    # (https://docs.djangoproject.com/en/1.8/ref/models/fields/#durationfield)
    # for storing timedeltas which uses MySQL's bigint for backing
    # storage. After we've completed the Django upgrade we should be
    # able to replace this field with a DurationField named
    # `refund_window` without having to run a migration or change
    # other code.
    refund_window_microseconds = models.BigIntegerField(
        default=1209600000000,
        help_text=_(
            "The window of time after enrolling during which users can be granted"
            " a refund, represented in microseconds. The default is 14 days."
        )
    )

    @property
    def refund_window(self):
        """Return the configured refund window as a `datetime.timedelta`."""
        return timedelta(microseconds=self.refund_window_microseconds)

    @refund_window.setter
    def refund_window(self, refund_window):
        """Set the current refund window to the given timedelta."""
        self.refund_window_microseconds = int(refund_window.total_seconds() * 1000000)


class BulkUnenrollConfiguration(ConfigurationModel):  # lint-amnesty, pylint: disable=empty-docstring
    """

    """
    csv_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        help_text=_("It expect that the data will be provided in a csv file format with \
                    first row being the header and columns will be as follows: \
                    user_id, username, email, course_id, is_verified, verification_date")
    )


class BulkChangeEnrollmentConfiguration(ConfigurationModel):
    """
    config model for the bulk_change_enrollment_csv command
    """
    csv_file = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        help_text=_("It expect that the data will be provided in a csv file format with \
                    first row being the header and columns will be as follows: \
                    course_id, username, mode")
    )


class CourseEnrollmentCelebration(TimeStampedModel):
    """
    Keeps track of how we've celebrated a user's course progress.

    An example of a celebration is a dialog that pops up after you complete your first section
    in a course saying "good job!". Just some positive feedback like that. (This specific example is
    controlled by the celebrated_first_section field below.)

    In general, if a row does not exist for an enrollment, we don't want to show any celebrations.
    We don't want to suddenly inject celebrations in the middle of a course, because they
    might not make contextual sense and it's an inconsistent experience. The helper methods below
    (starting with "should_") can help by looking up values with appropriate fallbacks.

    See the create_course_enrollment_celebration signal handler for how these get created.

    .. no_pii:
    """
    enrollment = models.OneToOneField(CourseEnrollment, models.CASCADE, related_name='celebration')
    celebrate_first_section = models.BooleanField(default=False)
    celebrate_weekly_goal = models.BooleanField(default=False)

    def __str__(self):
        return (
            '[CourseEnrollmentCelebration] course: {}; user: {}'
        ).format(self.enrollment.course.id, self.enrollment.user.username)

    @staticmethod
    def should_celebrate_first_section(enrollment):
        """
        Returns the celebration value for first_section with appropriate fallback if it doesn't exist.

        The frontend will use this result and additional information calculated to actually determine
        if the first section celebration will render. In other words, the value returned here is
        NOT the final value used.
        """
        if not enrollment:
            return False
        try:
            return enrollment.celebration.celebrate_first_section
        except CourseEnrollmentCelebration.DoesNotExist:
            return False

    @staticmethod
    def should_celebrate_weekly_goal(enrollment):
        """
        Returns the celebration value for weekly_goal with appropriate fallback if it doesn't exist.

        The frontend will use this result directly to determine if the weekly goal celebration
        should be rendered. The value returned here IS the final value used.
        """
        # Avoiding circular import
        from lms.djangoapps.course_goals.models import CourseGoal, UserActivity
        try:
            if not enrollment or not enrollment.celebration.celebrate_weekly_goal:
                return False
        except CourseEnrollmentCelebration.DoesNotExist:
            return False

        try:
            goal = CourseGoal.objects.get(user=enrollment.user, course_key=enrollment.course.id)
            if not goal.days_per_week:
                return False

            today = date.today()
            monday_date = today - timedelta(days=today.weekday())
            week_activity_count = UserActivity.objects.filter(
                user=enrollment.user, course_key=enrollment.course.id, date__gte=monday_date,
            ).count()
            return week_activity_count == goal.days_per_week
        except CourseGoal.DoesNotExist:
            return False
