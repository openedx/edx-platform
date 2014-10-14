from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from rest_framework import authentication
from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError
from user_api.serializers import UserSerializer, UserPreferenceSerializer
from user_api.models import UserPreference
from django_comment_common.models import Role
from opaque_keys.edx.locations import SlashSeparatedCourseKey


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


class LoginSessionView(APIView):
    """TODO"""

    def get(self, request):
        """Render a form for allowing a user to log in.

        TODO
        """
        return HttpResponse()

    def post(self, request):
        """Authenticate a user and log them in.

        TODO
        """
        # Initially, this should be a shim to student views,
        # since it will be too much work to re-implement everything there.
        # Eventually, we'll want to pull out that functionality into this Django app.
        return HttpResponse()

    def delete(self, request):
        """ Log the user out.

        TODO
        """
        return HttpResponse()


class RegistrationView(APIView):
    """TODO"""

    def get(self, request):
        """Render a form for allowing the user to register.

        This must use preferences to

        TODO
        """
        return HttpResponse()

    def post(self, request):
        """Create the user's account.

        TODO
        """
        # Initially, this should be a shim to student views.
        # Eventually, we'll want to pull that functionality into this API.
        return HttpResponse()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = User.objects.all().prefetch_related("preferences")
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class ForumRoleUsersListView(generics.ListAPIView):
    """
    Forum roles are represented by a list of user dicts
    """
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        """
        Return a list of users with the specified role/course pair
        """
        name = self.kwargs['name']
        course_id_string = self.request.QUERY_PARAMS.get('course_id')
        if not course_id_string:
            raise ParseError('course_id must be specified')
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id_string)
        role = Role.objects.get_or_create(course_id=course_id, name=name)[0]
        users = role.users.all()
        return users


class UserPreferenceViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    queryset = UserPreference.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ("key", "user")
    serializer_class = UserPreferenceSerializer
    paginate_by = 10
    paginate_by_param = "page_size"


class PreferenceUsersListView(generics.ListAPIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (ApiKeyHeaderPermission,)
    serializer_class = UserSerializer
    paginate_by = 10
    paginate_by_param = "page_size"

    def get_queryset(self):
        return User.objects.filter(preferences__key=self.kwargs["pref_key"]).prefetch_related("preferences")

