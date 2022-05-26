"""Middleware to change name of an incoming cookie"""
from django.conf import settings

from edx_django_utils.monitoring import set_custom_attribute


class CookieNameChange:
    """Changes name of an incoming cookie"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Changes the names of a cookie in request.COOKIES

        For this middleware to run:
        - set COOKIE_NAME_CHANGE_ACTIVATE =  True
        - COOKIE_NAME_CHANGE_EXPAND_INFO is a dict and has following info:
          - "current": Cookie name that will be used by relying code
          - "alternate": Other cookie name, to be renamed to current name if present

        Actions taken by middleware, during request phase:
        - Delete alternate-name cookie from request.COOKIES
        - Preserve any cookie with current name, or create one with value of
          cookie with alternate name (if alt cookie was present)

        To perform a seamless name change for a cookie, follow this
        expand-contract procedure:

        1. Baseline configuration::

             SOME_COOKIE_NAME: old

        2. Enable servers to understand both names by renaming the *new* name
           to the *old* (current) name, which should have no immediate effect::

             COOKIE_NAME_CHANGE_ACTIVATE: True
             COOKIE_NAME_CHANGE_EXPAND_INFO:
               current: old
               alternate: new
             SOME_COOKIE_NAME: old

        3. Swap the new and old cookie names in all three places they occur (the
           main setting and the two dictionary elements), now that all servers
           are capable of reading either name::

             COOKIE_NAME_CHANGE_ACTIVATE: True
             COOKIE_NAME_CHANGE_EXPAND_INFO:
               current: new
               alternate: old
             SOME_COOKIE_NAME: new

        4. After some time period to allow old cookies to age out, remove the
           transition settings::

             SOME_COOKIE_NAME: new
        """

        # .. toggle_name: COOKIE_NAME_CHANGE_ACTIVATE
        # .. toggle_implementation: DjangoSetting
        # .. toggle_default: False
        # .. toggle_description: Used to enable CookieNameChange middleware which changes a cookie name in request.COOKIES
        # .. toggle_warning: This should be set at the same time you set COOKIE_NAME_CHANGE_EXPAND_INFO setting
        # .. toggle_use_cases: temporary
        # .. toggle_creation_date: 2021-08-04
        # .. toggle_target_removal_date: 2021-10-01
        # .. toggle_tickets: https://openedx.atlassian.net/browse/ARCHBOM-1872
        if getattr(settings, "COOKIE_NAME_CHANGE_ACTIVATE", False):
            alt_cookie_in_request = False
            expand_settings = getattr(settings, "COOKIE_NAME_CHANGE_EXPAND_INFO", None)

            if (
                expand_settings is not None
                and isinstance(expand_settings, dict)
                and "current" in expand_settings
                and "alternate" in expand_settings
            ):
                if expand_settings["alternate"] in request.COOKIES:
                    alt_cookie_in_request = True
                    alt_cookie_value = request.COOKIES[expand_settings["alternate"]]
                    del request.COOKIES[expand_settings["alternate"]]
                    # Adding custom attribute: cookie.change_name
                    # if cookie.change_name in transaction and equal 0,
                    #     cookie with alternate name was detected and deleted
                    # if cookie.change_name in transaction and equal 1,
                    #     cookie with current name was added
                    set_custom_attribute("cookie.change_name", 0)

                if (
                    expand_settings["current"] not in request.COOKIES
                    and alt_cookie_in_request
                ):
                    request.COOKIES[expand_settings["current"]] = alt_cookie_value
                    set_custom_attribute("cookie.change_name", 1)

        response = self.get_response(request)
        return response
