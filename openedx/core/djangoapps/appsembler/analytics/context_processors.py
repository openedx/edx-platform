import hashlib

from django.conf import settings
from student.auth import user_has_role
from student.roles import CourseCreatorRole

from openedx.core.djangoapps.appsembler.analytics.helpers import should_show_hubspot


def google_analytics(request):
    data = {
        'GOOGLE_ANALYTICS_APP_ID': getattr(settings, 'GOOGLE_ANALYTICS_APP_ID', None),
        'SHOW_GOOGLE_ANALYTICS': getattr(settings, 'GOOGLE_ANALYTICS_APP_ID', None),
    }

    user = request.user
    # if user is created through AMC
    if user.is_authenticated and user_has_role(user, CourseCreatorRole()):
        data['USER_EMAIL_HASH'] = hashlib.sha256(request.user.email).hexdigest()

    return data


def mixpanel(request):
    data = {
        'MIXPANEL_APP_ID': getattr(settings, 'MIXPANEL_APP_ID', None),
        'SHOW_MIXPANEL': getattr(settings, 'MIXPANEL_APP_ID', None),
    }
    return data


def hubspot(request):
    hubspot_portal_id = getattr(settings, 'HUBSPOT_PORTAL_ID', None)
    data = {
        'HUBSPOT_PORTAL_ID': hubspot_portal_id,
        'SHOW_HUBSPOT': hubspot_portal_id and should_show_hubspot(request.user),
    }
    return data
