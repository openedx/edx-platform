from lms.djangoapps.onboarding.helpers import (
    get_org_metric_update_prompt,
    get_org_oef_update_prompt,
    is_org_detail_platform_overlay_available,
    is_org_detail_prompt_available,
    is_org_oef_prompt_available
)
from lms.djangoapps.philu_overrides.constants import (
    CDN_LINK_DICT,
    NODEBB_END_POINT_DICT,
    ORG_DETAILS_UPDATE_ALERT_MSG_DICT,
    ORG_OEF_UPDATE_ALERT_MSG_DICT
)
from lms.djangoapps.philu_overrides.helpers import get_activation_alert_error_msg_dict


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
            global_alert_message = get_activation_alert_error_msg_dict(request.user.id)
            global_alert_messages.append(global_alert_message)

    if '/oef/dashboard' in request.path:
        oef_update_prompt = get_org_oef_update_prompt(request.user)
        show_oef_prompt = oef_update_prompt and is_org_oef_prompt_available(oef_update_prompt)
        if show_oef_prompt:
            global_alert_messages.append(ORG_OEF_UPDATE_ALERT_MSG_DICT)
            oef_prompt = True

    elif '/organization/details/' in request.path and show_org_detail_prompt:
        global_alert_messages.append(ORG_DETAILS_UPDATE_ALERT_MSG_DICT)

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
    return NODEBB_END_POINT_DICT


def get_cdn_link(request):
    """
    Return CDN url link to templates
    """
    return CDN_LINK_DICT
