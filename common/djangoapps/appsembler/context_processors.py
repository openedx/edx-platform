import hmac
import hashlib
import os

from django.conf import settings

from student import roles


def intercom(request):
    data = {'show_intercom_widget': False}

    intercom_app_id = os.environ.get("INTERCOM_APP_ID", "")
    if not intercom_app_id:
        return data

    if settings.PROJECT_ROOT.endswith('edx-platform/cms') or \
            (settings.PROJECT_ROOT.endswith('edx-platform/lms') and request.get_host().startswith('preview.')):
        data['show_intercom_widget'] = True

    if not data['show_intercom_widget'] and request.user.is_authenticated():
        user = request.user

        # TODO: the logic below will need tweaking for sure
        if (user.is_staff or user.is_superuser or
                # the following line doesn't check whether the role is for the current course
                user.courseaccessrole_set.filter(role__in=(roles.CourseStaffRole.ROLE,
                                                           roles.CourseInstructorRole.ROLE)).exists()):
            data['show_intercom_widget'] = True

    if not data['show_intercom_widget']:
        return data

    email = os.environ.get("INTERCOM_USER_EMAIL", "")
    user_hash = hmac.new(
        os.environ.get("INTERCOM_APP_SECRET", ""),
        email,
        digestmod=hashlib.sha256).hexdigest()
    data['intercom_user_email'] = email
    data['intercom_user_hash'] = user_hash
    data['intercom_app_id'] = intercom_app_id

    return data
