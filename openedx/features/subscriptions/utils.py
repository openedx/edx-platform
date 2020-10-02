from courseware.access_utils import ACCESS_DENIED, ACCESS_GRANTED
from openedx.features.subscriptions.models import UserSubscription

from student.models import User
from enrollment import api
from enrollment.data import get_course_enrollment


def track_subscription_enrollment(subscription_id, username, course_id):
    """
    Add user enrollment to valid subscription.
    """
    if subscription_id:
        enrollment = api.get_enrollment(username, course_id)
        user = User.objects.get(username=username)
        valid_user_subscription = UserSubscription.get_valid_subscriptions(user.id).first()
        if valid_user_subscription and valid_user_subscription.subscription_id == subscription_id:
            valid_user_subscription.course_enrollments.add(enrollment)

def is_course_accessible_with_subscription(user, course):
    """
    Check if user has access to a course enrolled through subscription.
    """
    course_enrolled_subscriptions = UserSubscription.objects.filter(user=user, course_enrollments__course__id=course.id)
    if not course_enrolled_subscriptions:
        return ACCESS_GRANTED

    for subscription in course_enrolled_subscriptions:
        if subscription.is_active:
            return ACCESS_GRANTED

    return ACCESS_DENIED
