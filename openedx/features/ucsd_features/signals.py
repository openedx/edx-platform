from logging import getLogger

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from lms.djangoapps.verify_student.models import ManualVerification
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile


logger = getLogger(__name__)


@receiver(post_save, sender=UserProfile)
def generate_manual_verification_for_user(sender, instance, created, **kwargs):
    """
    Generate ManualVerification for the User (whose UserProfile instance has been created).
    """
    if not (settings.FEATURES.get('AUTOMATIC_PERMANENT_ACCOUNT_VERIFICATION') and created):
        return

    logger.info('Generating ManualVerification for user: {}'.format(instance.user.email))
    try:
        ManualVerification.objects.create(
            user=instance.user,
            status='approved',
            reason='SKIP_IDENTITY_VERIFICATION',
            name=instance.name
        )
    except Exception:  # pylint: disable=broad-except
        logger.error('Error while generating ManualVerification for user: %s', instance.user.email, exc_info=True)


@receiver(pre_save, sender=CourseOverview)
def course_image_change(sender, instance, **kwargs):
    """
    Change the default course image whenever new course is created
    """
    if instance.course_image_url.endswith('images_course_image.jpg'):
        instance.course_image_url = "/static/" + settings.DEFAULT_COURSE_ABOUT_IMAGE_URL
