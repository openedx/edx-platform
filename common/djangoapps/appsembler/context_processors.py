import os


def intercom(request):
    data = {
        'intercom_user_email': os.environ.get("INTERCOM_USER_EMAIL"),
        'intercom_app_id': os.environ.get("INTERCOM_APP_ID"),
    }
    return data
