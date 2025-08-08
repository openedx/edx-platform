"""
MFE API Views for useful information related to mfes.
"""

import edx_api_doc_tools as apidocs
from django.conf import settings
from django.http import HttpResponseNotFound, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.views import APIView

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class MFEConfigView(APIView):
    """
    Provides an API endpoint to get the MFE configuration from settings (or site configuration).
    """

    @method_decorator(cache_page(settings.MFE_CONFIG_API_CACHE_TIMEOUT))
    @apidocs.schema(
        parameters=[
            apidocs.query_parameter(
                'mfe',
                str,
                description="Name of an MFE (a.k.a. an APP_ID).",
            ),
        ],
    )
    def get(self, request):
        """
        Return the MFE configuration, optionally including MFE-specific overrides.
        The following hierarchy is used, in the order from most specific to least specific:
        1. site MFE_CONFIG_OVERRIDES
        2. settings MFE_CONFIG_OVERRIDES
        3. site MFE_CONFIG
        4. settings MFE_CONFIG
        5. site config plain value
        6. settings plain value

        **Usage**

          Get common config:
          GET /api/mfe_config/v1

          Get app config (common + app-specific overrides):
          GET /api/mfe_config/v1?mfe=name_of_mfe

        **GET Response Values**
        ```
        {
            "BASE_URL": "https://name_of_mfe.example.com",
            "LANGUAGE_PREFERENCE_COOKIE_NAME": "example-language-preference",
            "CREDENTIALS_BASE_URL": "https://credentials.example.com",
            "DISCOVERY_API_BASE_URL": "https://discovery.example.com",
            "LMS_BASE_URL": "https://courses.example.com",
            "LOGIN_URL": "https://courses.example.com/login",
            "LOGOUT_URL": "https://courses.example.com/logout",
            "STUDIO_BASE_URL": "https://studio.example.com",
            "LOGO_URL": "https://courses.example.com/logo.png",
            "ENABLE_COURSE_SORTING_BY_START_DATE": True,
            "HOMEPAGE_COURSE_MAX": 10,
            ... and so on
        }
        ```
        """

        if not settings.ENABLE_MFE_CONFIG_API:
            return HttpResponseNotFound()

        # Get values from django settings (level 6) or site configuration (level 5)
        base_config = self._get_base_config()

        # Get values from mfe configuration, either from django settings (level 4) or site configuration (level 3)
        mfe_config = configuration_helpers.get_value("MFE_CONFIG", settings.MFE_CONFIG)

        # Get values from mfe overrides, either from django settings (level 2) or site configuration (level 1)
        mfe_config_overrides = {}
        if request.query_params.get("mfe"):
            mfe = str(request.query_params.get("mfe"))
            app_config = configuration_helpers.get_value(
                "MFE_CONFIG_OVERRIDES",
                settings.MFE_CONFIG_OVERRIDES,
            )
            mfe_config_overrides = app_config.get(mfe, {})

        # Merge the three configs in the order of precedence
        merged_config = base_config | mfe_config | mfe_config_overrides

        return JsonResponse(merged_config, status=status.HTTP_200_OK)

    @staticmethod
    def _get_base_config() -> dict:
        """
        Return configuration values available in either site configuration or django settings.
        """
        return {
            "ENABLE_COURSE_SORTING_BY_START_DATE": configuration_helpers.get_value(
                "ENABLE_COURSE_SORTING_BY_START_DATE",
                settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]
            ),
            "SHOW_HOMEPAGE_PROMO_VIDEO": configuration_helpers.get_value(
                "show_homepage_promo_video",
                False
            ),
            "HOMEPAGE_PROMO_VIDEO_YOUTUBE_ID": configuration_helpers.get_value(
                "homepage_promo_video_youtube_id",
                "your-youtube-id"
            ),
            "HOMEPAGE_COURSE_MAX": configuration_helpers.get_value(
                "HOMEPAGE_COURSE_MAX",
                settings.HOMEPAGE_COURSE_MAX
            ),
            "COURSE_ABOUT_TWITTER_ACCOUNT": configuration_helpers.get_value(
                "course_about_twitter_account",
                settings.PLATFORM_TWITTER_ACCOUNT
            ),
            "IS_COSMETIC_PRICE_ENABLED": settings.FEATURES.get("ENABLE_COSMETIC_DISPLAY_PRICE"),
            "COURSES_ARE_BROWSABLE": settings.FEATURES.get("COURSES_ARE_BROWSABLE")
        }
