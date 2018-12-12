# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from rest_framework import status
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
            return Response(
                _("Missing requested parameter 'platform'"),
                status=status.HTTP_400_BAD_REQUEST
            )

        latest_version_config = AppVersionConfig.objects.filter(platform=platform, enabled=True).first()
        if latest_version_config:
            return Response({
                "last_version": {
                    "platform": latest_version_config.platform,
                    "last_version": latest_version_config.version,
                    "is_audited": latest_version_config.is_audited
                }
            })
        else:
            return Response(
                _('Unable to find information about the latest version of the platform'),
                status=status.HTTP_404_NOT_FOUND
            )

