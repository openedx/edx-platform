"""
Views for user API
"""

# TODO: remove unused
from rest_framework import generics, permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# TODO: myimports
from django.utils import simplejson
from django.http import HttpResponse

class IsUser(permissions.BasePermission):
    """
    Permission that checks to see if the request user matches the User models
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj

class JsonResponse(HttpResponse):
    """
        JSON response 
    """
    def __init__(self, content, mimetype='application/json', status=None, content_type=None):
        super(JsonResponse, self).__init__(
            content=simplejson.dumps(content),
            mimetype=mimetype,
            status=status,
            content_type=content_type,
        )

class Social(generics.RetrieveAPIView): 
    """
    **Use Case**

        TODO

    **Example request**:

        TODO

    **Response Values**

        TODO
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response(
            {"app secret": "This is the app secret"}
        )
