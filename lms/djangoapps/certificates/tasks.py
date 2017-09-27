from celery import task
from logging import getLogger
import logging

from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from edx_ace import ace
from edx_ace.message import MessageType
from edx_ace.recipient import Recipient

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .api import generate_user_certificates
from certificates.views.shipping_information import shipping_information

logger = getLogger(__name__)


class _BaseCertificateTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseCertificateTask, bind=True, default_retry_delay=30, max_retries=2)
def generate_certificate(self, **kwargs):
    """
    Generates a certificate for a single user.

    kwargs:
        - student: The student for whom to generate a certificate.
        - course_key: The course key for the course that the student is
            receiving a certificate in.
        - expected_verification_status: The expected verification status
            for the user.  When the status has changed, we double check
            that the actual verification status is as expected before
            generating a certificate, in the off chance that the database
            has not yet updated with the user's new verification status.
    """
    original_kwargs = kwargs.copy()
    student = User.objects.get(id=kwargs.pop('student'))
    course_key = CourseKey.from_string(kwargs.pop('course_key'))
    expected_verification_status = kwargs.pop('expected_verification_status', None)
    if expected_verification_status:
        actual_verification_status, _ = SoftwareSecurePhotoVerification.user_status(student)
        if expected_verification_status != actual_verification_status:
            raise self.retry(kwargs=original_kwargs)
    generate_user_certificates(student=student, course_key=course_key, **kwargs)


ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


class PassedCourse(MessageType):
    pass


@task(ignore_result=True, routing_key=ACE_ROUTING_KEY)
def send_passing_learner_message(user_id, course_key_str):
    try:
        user = User.objects.get(id=user_id)
        course_key = CourseKey.from_string(course_key_str)
        course = CourseOverview.get_from_id(course_key)

        def absolute_url(relative_path):
            return u'{}{}'.format(settings.LMS_ROOT_URL, urlquote(relative_path))

        context = {
            'shipping_address_form_url': absolute_url(reverse('certificates:shipping_information')),
            'course_name': course.display_name,
        }

        msg = PassedCourse().personalize(
            Recipient(
                user.username,
                user.email,
            ),
            course.language,
            context,
        )

        ace.send(msg)
    except:
        logger.exception('')
