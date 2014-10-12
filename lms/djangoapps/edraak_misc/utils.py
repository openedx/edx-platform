from courseware.access import has_access
from django.conf import settings


def is_certificate_allowed(user, course):
    return (course.has_ended()
            and settings.FEATURES.get('ENABLE_ISSUE_CERTIFICATE')
            or has_access(user, 'staff', course.id))
