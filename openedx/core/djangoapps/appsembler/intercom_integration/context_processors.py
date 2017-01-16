import hmac
import hashlib

from django.conf import settings
from student.auth import user_has_role
from student.roles import CourseCreatorRole


def intercom(request):
    data = {'show_intercom_widget': False}

    intercom_app_id = settings.INTERCOM_APP_ID
    if not intercom_app_id:
        return data

    user = request.user
    # if user is created through AMC
    if user.is_authenticated() and user_has_role(user, CourseCreatorRole()):

        data['show_intercom_widget'] = True
        user_hash = hmac.new(
            str(settings.INTERCOM_APP_SECRET),
            str(user.email),
            digestmod=hashlib.sha256).hexdigest()
        data['intercom_user_hash'] = user_hash
        data['intercom_app_id'] = intercom_app_id
        data['intercom_lms_url'] = request.site.domain

    return data
