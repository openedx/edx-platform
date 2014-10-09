import hmac
import hashlib
import os


def intercom(request):
    email = os.environ.get("INTERCOM_USER_EMAIL")
    user_hash = hmac.new(
        os.environ.get("INTERCOM_API_SECRET"),
        email,
        digestmod=hashlib.sha256).hexdigest()
    data = {
        'intercom_user_email': email,
        'intercom_user_hash': user_hash,
        'intercom_app_id': os.environ.get("INTERCOM_APP_ID"),
    }
    return data
