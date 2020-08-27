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


class DiscussionSettingsViewSet(viewsets.GenericViewSet):
    """Endpoint to Serve & Update discussion related settings"""

    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    lookup_value_regex = settings.COURSE_KEY_REGEX
    permission_classes = (permissions.IsAdminUser,)

    # relavent keys for discussion related settings
    discussion_settings_keys = [
        'discussion_blackouts',
        'discussion_link',
        'discussion_sort_alpha',
        'allow_anonymous_to_peers',
        'allow_anonymous'
    ]

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

    def _filter_discussion_settings(self, from_dict):
        """Helper method to filter out only discussion related keys from given dictionary"""

        return {key: from_dict[key] for key in self.discussion_settings_keys if key in from_dict}

    def _get_discussion_settings(self, course_module):
        """Find discussion settings from a course"""

        advanced_settings = CourseMetadata.fetch(course_module)
        return self._filter_discussion_settings(advanced_settings)

    def retrieve(self, request, *args, **kwargs):
        """Return all discussion related settings for a course"""

        course_module = self.get_course_module()
        return Response(self._get_discussion_settings(course_module))

    def update(self, request, *args, **kwargs):
        """Update discussion settings"""

        course_key = self.get_object()
        with modulestore().bulk_operations(course_key):
            course_module = self.get_course_module()

            # make sure only discussion related settings are updated
            discussion_dict = self._filter_discussion_settings(request.data)
            is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                course_module,
                discussion_dict,
                user=request.user,
            )
            if is_valid:
                # now update mongo
                modulestore().update_item(course_module, request.user.id)
                updated_discussion_settings = self._filter_discussion_settings(updated_data)
                return Response(updated_discussion_settings)
            else:
                return Response({'errors': errors}, status.HTTP_400_BAD_REQUEST)
