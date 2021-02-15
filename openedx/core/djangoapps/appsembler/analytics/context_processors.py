import hashlib

from django.conf import settings
from student.auth import user_has_role
from student.roles import CourseCreatorRole

from openedx.core.djangoapps.appsembler.analytics.helpers import (
    should_show_hubspot
)


def google_analytics(request):
    app_id = getattr(settings, 'GOOGLE_ANALYTICS_APP_ID', None)
    show_app = True if app_id else False

    data = {
        'GOOGLE_ANALYTICS_APP_ID': app_id,
        'SHOW_GOOGLE_ANALYTICS': show_app,
    }

    user = request.user
    # if user is created through AMC
    if user.is_authenticated and user_has_role(user, CourseCreatorRole()):
        email_hash = hashlib.sha256(request.user.email.encode('utf-8')).hexdigest()
        data['USER_EMAIL_HASH'] = email_hash

    return data


def mixpanel(request):
    app_id = getattr(settings, 'MIXPANEL_APP_ID', None)
    show_app = True if app_id else False
    data = {
        'MIXPANEL_APP_ID': app_id,
        'SHOW_MIXPANEL': show_app,
    }
    return data


def hubspot(request):
    hubspot_portal_id = getattr(settings, 'HUBSPOT_PORTAL_ID', None)
    if hubspot_portal_id and should_show_hubspot(request.user):
        show_app = True
    else:
        show_app = False
    data = {
        'HUBSPOT_PORTAL_ID': hubspot_portal_id,
        'SHOW_HUBSPOT': show_app,
    }
    return data
