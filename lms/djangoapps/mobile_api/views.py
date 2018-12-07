# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AppVersionConfig


class APPLastVersionView(APIView):
    """
    Get last version of mobile client.

    ```
    http://localhost:18000/api/mobile/v0.5/app_version/last/?platform=android
    ```
    """

    def get(self, request, *args, **kwargs):
        platform = request.query_params.get('platform', '')
        if not platform:
            return Response(_("Missing requested parameter {}.".format(platform)))

        latest_version_config = AppVersionConfig.objects.filter(platform=platform, enabled=True).first()
        if latest_version_config:
            return Response({
                "last_version": {
                    "platform": latest_version_config.platform,
                    "version": latest_version_config.version,
                    "created_at": latest_version_config.created_at,
                    "download_url": latest_version_config.download_url,
                    "release_notes": latest_version_config.release_notes,
                    "version_code": latest_version_config.version_code,
                    "is_audited_passed": latest_version_config.is_audited_passed
                }
            })
        else:
            return Response(_('Unable to find information about the latest version of the platform'))

