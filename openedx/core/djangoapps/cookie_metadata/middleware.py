"""Middleware to changes name of an incoming cookie"""
from django.conf import settings


class CookieNameChange:
    """Changes name of an incoming cookie"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Changes the names of a cookie in request.COOKIES

        For this middleware to run:
        - set COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE =  True
        - COOKIE_NAME_CHANGE_EXPAND_INFO is a dict and has following info:
            "old_name": Previous name of cookie
            "new_name": New name of cookie
            if you also want to delete the cookie in user's browser, set "old_domain" as well

        Actions taken by middleware:
            - will delete any cookie with "old_name"
            - if create a new cookie with "new_name" and set its value to value of "old_name" cookie
                + it will not modify cookie with "new_name" if it already exists in request.COOKIES
        """

        # .. toggle_name: COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE
        # .. toggle_implementation: SettingToggle
        # .. toggle_default: False
        # .. toggle_description: Used to enable CookieNameChange middleware which changes a cookie name in request.COOKIES
        # .. toggle_warnings: This should be set at the same time you set COOKIE_NAME_CHANGE_EXPAND_INFO setting
        # .. toggle_use_cases: temporary
        # .. toggle_creation_date: 2021-08-04
        # .. toggle_removal_date: 2021-09-01
        # .. toggle_tickets: TODO
        if getattr(settings, "COOKIE_NAME_CHANGE_ACTIVATE_EXPAND_PHASE", False):
            old_cookie_in_request = False
            expand_settings = getattr(settings, "COOKIE_NAME_CHANGE_EXPAND_INFO", None)

            if (
                expand_settings is not None
                and type(expand_settings) is dict
                and "new_name" in expand_settings
                and "old_name" in expand_settings
            ):
                if expand_settings["old_name"] in request.COOKIES:
                    old_cookie_in_request = True
                    old_cookie_value = request.COOKIES[expand_settings["old_name"]]
                    del request.COOKIES[expand_settings["old_name"]]

                if (
                    expand_settings["new_name"] not in request.COOKIES
                    and old_cookie_in_request
                ):
                    request.COOKIES[expand_settings["new_name"]] = old_cookie_value

        response = self.get_response(request)
        return response
