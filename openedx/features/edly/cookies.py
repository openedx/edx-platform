from django.conf import settings

from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings
from openedx.features.edly.models import EdlySubOrganization
from openedx.features.edly.utils import encode_edly_user_info_cookie


def set_logged_in_edly_cookies(request, response, user):
    """
    Set cookies for edly users at the time of login.

    Arguments:
        request (HttpRequest): The request to the view, used to calculate
            the cookie's expiration date based on the session expiration date.
        response (HttpResponse): The response on which the cookie will be set.
        user (User): The currently logged in user.

    Returns:
        HttpResponse

    """
    if user.is_authenticated and not user.is_anonymous:
        cookie_settings = standard_cookie_settings(request)
        edly_cookie_string = _get_edly_user_info_cookie_string(request)

        response.set_cookie(
            settings.EDLY_USER_INFO_COOKIE_NAME,
            edly_cookie_string,
            **cookie_settings
        )

    return response


def delete_logged_in_edly_cookies(response):
    """
    Delete edly user info cookie.

    Arguments:
        response (HttpResponse): The response sent to the client.

    Returns:
        HttpResponse
    """
    response.delete_cookie(settings.EDLY_USER_INFO_COOKIE_NAME)

    return response

def _get_edly_user_info_cookie_string(request):
    """
    Returns JWT encoded cookie string with edly user info.

    Arguments:
        request (HttpRequest): Django request object

    Returns:
        string
    """
    try:
        edly_sub_organization = request.site.edly_sub_org_for_lms
        edly_user_info_cookie_data = {
            'edly-org': edly_sub_organization.edly_organization.slug,
            'edly-sub-org': edly_sub_organization.slug,
            'edx-org': edly_sub_organization.edx_organization.short_name
        }
        return encode_edly_user_info_cookie(edly_user_info_cookie_data)
    except EdlySubOrganization.DoesNotExist:
        return ''
