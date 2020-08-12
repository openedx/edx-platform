# -*- coding: utf-8 -*-
"""
olx_rest_api Django application initialization.
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class OlxRestApiAppConfig(AppConfig):
    """
    Configuration for the olx_rest_api Django plugin application.
    See: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """

    name = 'openedx.core.djangoapps.olx_rest_api'
    verbose_name = 'Modulestore OLX REST API'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                # The namespace to provide to django's urls.include.
                PluginURLs.NAMESPACE: 'olx_rest_api',
            },
        },
    }
