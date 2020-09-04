from django.conf import settings
from django.urls import reverse

from lms.djangoapps.onboarding.helpers import (
    get_org_metric_update_prompt,
    get_org_oef_update_prompt,
    is_org_detail_platform_overlay_available,
    is_org_detail_prompt_available,
    is_org_oef_prompt_available
)
from lms.djangoapps.philu_overrides.constants import (
    ACTIVATION_ALERT_TYPE,
    ACTIVATION_ERROR_MSG_FORMAT,
    ORG_DETAILS_UPDATE_ALERT,
    ORG_OEF_UPDATE_ALERT
)


def get_global_alert_messages(request):
    """
    Get application wide messages
    :param request:
    :return: returns list of global messages"
    """

    global_alert_messages = []
    overlay_message = None
    oef_prompt = None

    # metric_update_prompt will tell us if user is responsible for some organization
    metric_update_prompt = get_org_metric_update_prompt(request.user)
    show_org_detail_prompt = metric_update_prompt and is_org_detail_prompt_available(metric_update_prompt)

    if not request.is_ajax():
        if request.user.is_authenticated() and not request.user.is_active and '/activate/' not in request.path:
            global_alert_messages.append({
                'type': ACTIVATION_ALERT_TYPE,
                'alert': ACTIVATION_ERROR_MSG_FORMAT.format(
                    api_endpoint=reverse('resend_activation_email'),
                    user_id=request.user.id
                )
            })

    if '/oef/dashboard' in request.path:
        oef_update_prompt = get_org_oef_update_prompt(request.user)
        show_oef_prompt = oef_update_prompt and is_org_oef_prompt_available(oef_update_prompt)
        if show_oef_prompt:
            global_alert_messages.append({
                'type': ACTIVATION_ALERT_TYPE,
                'alert': ORG_OEF_UPDATE_ALERT
            })
            oef_prompt = True

    elif '/organization/details/' in request.path and show_org_detail_prompt:
        global_alert_messages.append({
            'type': ACTIVATION_ALERT_TYPE,
            'alert': ORG_DETAILS_UPDATE_ALERT
        })

    elif metric_update_prompt and show_org_detail_prompt\
            and is_org_detail_platform_overlay_available(metric_update_prompt):
        overlay_message = True

    return {
        'global_alert_messages': global_alert_messages,
        'overlay_message': overlay_message,
        'oef_prompt': oef_prompt
    }


def add_nodebb_endpoint(request):
    """
    Add our NODEBB_ENDPOINT to the template context so that it can be referenced by any client side code.
    """
    return {'nodebb_endpoint': settings.NODEBB_ENDPOINT}


def get_cdn_link(request):
    """
    return CDN url link to templates
    :return:
    """
    return {'cdn_link': settings.CDN_LINK}
