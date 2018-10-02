from datetime import timedelta

from django.apps import apps
from django.utils import timezone
from django.utils.translation import ugettext as _


from lms.djangoapps.courseware.access_response import AccessError
from lms.djangoapps.courseware.access_utils import ACCESS_GRANTED


class AuditExpiredError(AccessError):
    """
    Access denied because the user's audit timespan has expired
    """
    def __init__(self, user, course, end_date):
        error_code = "audit_expired"
        developer_message = "User {} had access to {} until {}".format(user, course, end_date)
        user_message = _("Your audit access period has expired.")
        super(AuditExpiredError, self).__init__(error_code, developer_message, user_message)


def check_course_expired(user, course):
    # TODO: Only limit audit users
    # TODO: Limit access to instructor paced courses based on end-date, rather than content availability date
    CourseEnrollment = apps.get_model('student.CourseEnrollment')
    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if enrollment is None:
        return ACCESS_GRANTED

    try:
        start_date = enrollment.schedule.start
    except CourseEnrollment.schedule.RelatedObjectDoesNotExist:
        start_date = max(enrollment.created, course.start)

    end_date = start_date + timedelta(days=28)

    if timezone.now() > end_date:
        return AuditExpiredError(user, course, end_date)

    return ACCESS_GRANTED
