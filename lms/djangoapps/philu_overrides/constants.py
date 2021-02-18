"""
Constants for `philu_overrides` app
"""
from django.conf import settings

ACTIVATION_ERROR_MSG_FORMAT = """
<span id="resend-activation-span">
    Your account has not been activated. Please check your email to activate your account.
    <a id="resend-activation-link" class="click-here-link" href="{api_endpoint}" data-user-id={user_id}>
        Resend Activation Email
    </a>
</span>
"""

ORG_DETAILS_UPDATE_ALERT = 'It has been more than a year since you updated these numbers. Are they still correct?'
ORG_OEF_UPDATE_ALERT = 'It has been more than a year since you submitted your OEF assessment. Time to submit a new one!'
ACTIVATION_ALERT_TYPE = 'activation'
ENROLL_SHARE_TITLE_FORMAT = "Let's take this {} course together"
ENROLL_SHARE_DESC_FORMAT = "I just enrolled in Philanthropy University's {} course. Let's take it together!"

ORG_OEF_UPDATE_ALERT_MSG_DICT = {'type': ACTIVATION_ALERT_TYPE, 'alert': ORG_OEF_UPDATE_ALERT}
ORG_DETAILS_UPDATE_ALERT_MSG_DICT = {'type': ACTIVATION_ALERT_TYPE, 'alert': ORG_DETAILS_UPDATE_ALERT}

NODEBB_END_POINT_DICT = {'nodebb_endpoint': settings.NODEBB_ENDPOINT}
CDN_LINK_DICT = {'cdn_link': settings.CDN_LINK}
