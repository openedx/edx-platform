from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import viewsets
from user_api.models import UserPreference
from user_api.serializers import UserSerializer, UserPreferenceSerializer


class ApiKeyHeaderPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Check for permissions by matching the configured API key and header

        If settings.DEBUG is True and settings.EDX_API_KEY is not set or None,
        then allow the request. Otherwise, allow the request if and only if
        settings.EDX_API_KEY is set and the X-Edx-Api-Key HTTP header is
        present in the request and matches the setting.
        """
        api_key = getattr(settings, "EDX_API_KEY", None)
        return (
            (settings.DEBUG and api_key is None) or
            (api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key)
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class UserPreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = UserPreference.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ("key", "user")
    serializer_class = UserPreferenceSerializer
    paginate_by = 10
    paginate_by_param = "page_size"
