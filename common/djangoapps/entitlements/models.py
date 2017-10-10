import uuid as uuid_tools

from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from course_modes.models import CourseMode


class CourseEntitlement(TimeStampedModel):
    """
    Represents a Student's Entitlement to a Course Run for a given Course.
    """

    user = models.ForeignKey(User)
    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False)
    course_uuid = models.UUIDField()

    # The date that an the entitlement expired
    # if NULL the entitlement has not expired
    expired_at = models.DateTimeField(null=True)

    # The mode of the Course that will be applied
    mode = models.CharField(default=CourseMode.DEFAULT_MODE_SLUG, max_length=100)

    # The ID of the course enrollment for this Entitlement
    # if NULL the entitlement is not in use
    enrollment_course_run = models.ForeignKey('student.CourseEnrollment', null=True)
    order_number = models.CharField(max_length=128, null=True)

    @classmethod
    def entitlements_for_user(cls, user):
        """
        Retrieve all the Entitlements for a User

        Arguments:
            user: A Django User object identifying the current user

        Returns:
            All of the Entitlements for the User
        """
        return cls.objects.filter(user=user)

    @classmethod
    def get_user_course_entitlement(cls, user, course_uuid):
        """
        Retrieve The entitlement for the given parent course id if it exists for the User

        Arguments:
            user: A Django User object identifying the current user
            course_uuid(string): The parent course uuid

        Returns:
            The single entitlement for the requested parent course id
        """
        return cls.objects.filter(user=user, course_uuid=course_uuid).first()

    @classmethod
    def update_or_create_new_entitlement(cls, user, course_uuid, entitlement_data):
        """
        Updates or creates a new Course Entitlement

        Arguments:
            user: A Django User object identifying the current user
            course_uuid(string): The parent course uuid
            entitlement_data(dict): The dictionary containing all the data for the entitlement
                e.g. entitlement_data = {
                        'user': user,
                        'course_uuid': course_uuid
                        'enroll_end_date': '2017-09-14 11:47:58.000000',
                        'mode': 'verified',
                    }

        Returns:
            stored_entitlement: The new or updated CourseEntitlement object
            is_created (bool): Boolean representing whether or not the Entitlement was created or updated
        """
        stored_entitlement, is_created = cls.objects.update_or_create(
            user=user,
            course_uuid=course_uuid,
            defaults=entitlement_data
        )
        return stored_entitlement, is_created

    @classmethod
    def update_entitlement_enrollment(cls, user, course_uuid, course_run_enrollment):
        """
        Sets the enrollment course for a given entitlement

        Arguments:
            user: A Django User object identifying the current user
            course_uuid(string): The parent course uuid
            course_run_enrollment (CourseEnrollment): The CourseEnrollment object to store, None to clear the Enrollment
        """
        return cls.objects.filter(
            user=user,
            course_uuid=course_uuid
        ).update(enrollment_course_run_id=course_run_enrollment)
