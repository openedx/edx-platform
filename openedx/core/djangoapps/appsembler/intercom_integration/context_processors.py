import hmac
import hashlib

from django.conf import settings

from openedx.core.djangoapps.appsembler.intercom_integration.helpers import (
    should_show_intercom_widget
)


def intercom(request):
    data = {'show_intercom_widget': False}

    intercom_app_id = getattr(settings, 'INTERCOM_APP_ID', None)
    if not intercom_app_id:
        return data

    user = request.user
    if should_show_intercom_widget(user):
        data['show_intercom_widget'] = True
        user_hash = hmac.new(
            str(settings.INTERCOM_APP_SECRET).encode('utf-8'),
            str(user.email).encode('utf-8'),
            digestmod=hashlib.sha256).hexdigest()
        data['intercom_user_hash'] = user_hash
        data['intercom_app_id'] = intercom_app_id
        data['intercom_lms_url'] = request.site.domain

    return data
