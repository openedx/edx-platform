"""
Utils for subscriptions.
"""
from urllib.parse import urljoin
import waffle
from django.conf import settings

from courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED
from openedx.core.djangoapps.site_configuration.helpers import get_value
from openedx.features.subscriptions.models import UserSubscription

from student.models import CourseEnrollment


def track_subscription_enrollment(subscription_id, user, course_id, site):
    """
    Add user enrollment to valid subscription.
    """
    if subscription_id:
        try:
            enrollment = CourseEnrollment.objects.get(
                user=user, course_id=course_id
            )
        except CourseEnrollment.DoesNotExist:
            enrollment = None
        valid_user_subscription = UserSubscription.get_valid_subscriptions(site, username=user.username).first()
        if valid_user_subscription and valid_user_subscription.subscription_id == subscription_id:
            valid_user_subscription.course_enrollments.add(enrollment)
            valid_user_subscription.save()


def is_course_accessible_with_subscription(user, course):
    """
    Check if user has access to a course enrolled through subscription.
    """
    if not waffle.switch_is_active(settings.ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH):
        return ACCESS_GRANTED

    if not user or not user.is_authenticated:
        return ACCESS_GRANTED

    course_enrolled_subscriptions = UserSubscription.objects.filter(user=user, course_enrollments__course__id=course.id)
    if not course_enrolled_subscriptions:
        return ACCESS_GRANTED
    else:
        for subscription in course_enrolled_subscriptions:
            if subscription.is_active:
                return ACCESS_GRANTED

        return ACCESS_DENIED


def get_subscription_renew_url(subscription_id, user, ecommerce_url):
    """
    Get subscription renew url if given subscription is renewable.
    """
    renew_subscription_path = ''
    try:
        subscription = UserSubscription.objects.get(subscription_id=subscription_id, user=user)
    except UserSubscription.DoesNotExist:
        return renew_subscription_path

    if subscription.subscription_type != UserSubscription.FULL_ACCESS_COURSES:
        return renew_subscription_path

    renew_subscription_path = 'subscriptions/renew_subscription/?subscription_id={subscription_id}'.format(
        subscription_id=subscription_id
    )
    return urljoin(ecommerce_url + '/', renew_subscription_path)
