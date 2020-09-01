"""Api endpoint to fetch & update discussion related settings"""


from django.conf import settings
from django.http import Http404
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from contentstore.views.course import get_course_and_check_access
from models.settings.course_metadata import CourseMetadata
from xmodule.modulestore.django import modulestore

from ..serializers.discussion_settings import DiscussionSettingsSerializer


class DiscussionSettingsViewSet(viewsets.GenericViewSet):
    """Endpoint to Serve & Update discussion related settings"""

    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    lookup_value_regex = settings.COURSE_KEY_REGEX
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = DiscussionSettingsSerializer

    def get_object(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            u'Expected view %s to be called with a URL keyword argument '
            u'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        course_key = CourseKey.from_string(self.kwargs[lookup_url_kwarg])

        if course_key:
            return course_key

        raise Http404

    def get_course_module(self):
        course_key = self.get_object()
        return get_course_and_check_access(course_key, self.request.user)

    def get_settings(self):
        course_module = self.get_course_module()
        return CourseMetadata.fetch(course_module)

    def get_serializer_context(self, *args, **kwargs):
        context = super().get_serializer_context(*args, **kwargs)
        context['course_key'] = self.get_object()
        context['course_module'] = self.get_course_module()
        context['user'] = self.request.user
        return context

    def retrieve(self, request, *args, **kwargs):
        """Return all discussion related settings for a course"""

        settings_dict = self.get_settings()
        serializer = self.get_serializer(settings_dict)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Update discussion settings from request"""

        settings_dict = self.get_settings()
        serializer = self.get_serializer(settings_dict, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.validated_data)
