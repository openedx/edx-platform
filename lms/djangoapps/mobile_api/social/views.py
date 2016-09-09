"""
Views for user API
"""


from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import simplejson
from django.http import HttpResponse

from ..mobile_settings import _APP_SECRET, _APP_ID


class AppSecret(generics.RetrieveAPIView): 
    """
    **Use Case**

        Support for retrieving the app secret for a given app id.

    **Example request**:

        /api/mobile/v0.5/social/app-secret/<app-id>

    **Response Values**

        {"app-secret": "12345677890"}

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        secret = 'Null'
        if kwargs['app_id'] == _APP_ID:
            secret = _APP_SECRET
        return Response( {"app-secret": secret} )
