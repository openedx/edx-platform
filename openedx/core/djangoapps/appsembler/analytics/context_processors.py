import hashlib

from django.conf import settings
from student.auth import user_has_role
from student.roles import CourseCreatorRole

from openedx.core.djangoapps.appsembler.analytics.helpers import (
    should_show_hubspot
)


def google_analytics(request):
    app_id = getattr(settings, 'GOOGLE_ANALYTICS_APP_ID', None)
    data = {
        'GOOGLE_ANALYTICS_APP_ID': app_id,
        'SHOW_GOOGLE_ANALYTICS': bool(app_id),
    }

    user = request.user
    # if user is created through AMC
    if user.is_authenticated and user_has_role(user, CourseCreatorRole()):
        email_hash = hashlib.sha256(request.user.email.encode('utf-8')).hexdigest()
        data['USER_EMAIL_HASH'] = email_hash

    return data


def mixpanel(request):
    app_id = getattr(settings, 'MIXPANEL_APP_ID', None)
    data = {
        'MIXPANEL_APP_ID': app_id,
        'SHOW_MIXPANEL': bool(app_id),
    }
    return data


def hubspot(request):
    hubspot_portal_id = getattr(settings, 'HUBSPOT_PORTAL_ID', None)
    data = {
        'HUBSPOT_PORTAL_ID': hubspot_portal_id,
        'SHOW_HUBSPOT': bool(hubspot_portal_id) and should_show_hubspot(request.user),
    }
    return data
