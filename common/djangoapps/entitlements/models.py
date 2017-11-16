import uuid as uuid_tools

from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel


class CourseEntitlement(TimeStampedModel):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False)
    course_uuid = models.UUIDField(help_text='UUID for the Course, not the Course Run')
    expired_at = models.DateTimeField(
        null=True,
        help_text='The date that an entitlement expired, if NULL the entitlement has not expired.'
    )
    mode = models.CharField(max_length=100, help_text='The mode of the Course that will be applied on enroll.')
    enrollment_course_run = models.ForeignKey(
        'student.CourseEnrollment',
        null=True,
        help_text='The current Course enrollment for this entitlement. If NULL the Learner has not enrolled.'
    )
    order_number = models.CharField(max_length=128, null=True)

    @classmethod
    def get_active_user_course_entitlements(cls, user, course_uuid):
        """
        Returns all the available sessions for a given course.
        """

        try:
            entitlement = cls.objects.get(
                user=user,
                course_uuid=course_uuid,
                expired_at=None,
            )
            return entitlement
        except cls.DoesNotExist:
            return None

    @classmethod
    def set_enrollment(cls, entitlement, enrollment):
        """
        Fulfills an entitlement by specifying a session.
        """
        cls.objects.filter(id=entitlement.id).update(enrollment_course_run=enrollment)
