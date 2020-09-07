"""Api endpoint to fetch & update discussion related settings"""


from django.conf import settings
from django.http import Http404
from opaque_keys.edx.keys import CourseKey
from rest_framework import viewsets
from rest_framework.response import Response

from cms.djangoapps.contentstore.api.views.utils import course_author_access_required
from models.settings.course_metadata import CourseMetadata
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore

from ..serializers.discussion_settings import DiscussionSettingsSerializer


@view_auth_classes()
class DiscussionSettingsViewSet(viewsets.GenericViewSet):
    """Endpoint to Serve & Update discussion related settings"""

    lookup_field = 'course_id'
    lookup_value_regex = settings.COURSE_KEY_REGEX
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
        return modulestore().get_course(course_key)

    def get_settings(self):
        course_module = self.get_course_module()
        return {key: val['value'] for key, val in CourseMetadata.fetch(course_module).items()}

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['course_key'] = self.get_object()
        context['course_module'] = self.get_course_module()
        context['user'] = self.request.user
        return context

    @course_author_access_required
    def retrieve(self, request, *args, **kwargs):
        """Return all discussion related settings for a course"""

        settings_dict = self.get_settings()
        serializer = self.get_serializer(settings_dict)
        return Response(serializer.data)

    @course_author_access_required
    def update(self, request, *args, **kwargs):
        """Update discussion settings from request"""

        settings_dict = self.get_settings()
        serializer = self.get_serializer(settings_dict, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.validated_data)
