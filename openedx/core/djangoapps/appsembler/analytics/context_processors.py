import hashlib

from django.conf import settings
from student.auth import user_has_role
from student.roles import CourseCreatorRole


def google_analytics(request):
    data = {
        'GOOGLE_ANALYTICS_APP_ID': settings.GOOGLE_ANALYTICS_APP_ID,
        'SHOW_GOOGLE_ANALYTICS': settings.GOOGLE_ANALYTICS_APP_ID,
    }

    user = request.user
    # if user is created through AMC
    if user.is_authenticated() and user_has_role(user, CourseCreatorRole()):
        data['USER_EMAIL_HASH'] = hashlib.sha256(request.user.email).hexdigest()

    return data


def mixpanel(request):
    data = {
        'MIXPANEL_APP_ID': settings.MIXPANEL_APP_ID,
        'SHOW_MIXPANEL': settings.MIXPANEL_APP_ID,
    }
    return data


def hubspot(request):
    user = request.user
    data = {
        'HUBSPOT_PORTAL_ID': settings.HUBSPOT_PORTAL_ID,
        'SHOW_HUBSPOT': settings.HUBSPOT_PORTAL_ID and user.is_authenticated() and user_has_role(user, CourseCreatorRole()),
    }
    return data
