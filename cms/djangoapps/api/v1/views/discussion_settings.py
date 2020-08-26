"""Api endpoint to fetch & update discussion related settings"""


from django.core.exceptions import PermissionDenied
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.response import Response

from models.settings.course_metadata import CourseMetadata
from student.auth import has_studio_read_access
from xmodule.modulestore.django import modulestore


@api_view(['GET', 'POST', 'PUT'])
@authentication_classes([SessionAuthentication, JwtAuthentication])
def discussion_settings_handler(request, course_key_string):
    """Returns discussion related settings on GET & update on POST or PUT request."""

    # relavent keys for discussion related settings
    discussion_settings_keys = [
        'discussion_blackouts',
        'discussion_link',
        'discussion_sort_alpha',
        'allow_anonymous_to_peers',
        'allow_anonymous'
    ]

    course_key = CourseKey.from_string(course_key_string)

    # check if user has permission
    if not has_studio_read_access(request.user, course_key):
        raise PermissionDenied()

    with modulestore().bulk_operations(course_key):
        course_module = modulestore().get_course(course_key)

        if request.method == 'GET':
            advanced_dict = CourseMetadata.fetch(course_module)
            # filter out only discussion related settings
            discussion_dict = {key: advanced_dict[key] for key in discussion_settings_keys}
            return Response(discussion_dict)
        else:
            # from request, filter keys that are related to discussion settings
            discussion_dict = {key: request.data[key] for key in discussion_settings_keys if key in request.data}
            is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
                course_module,
                discussion_dict,
                user=request.user,
            )
            if is_valid:
                # now update mongo
                modulestore().update_item(course_module, request.user.id)
                updated_discussion_settings = {key: updated_data[key] for key in discussion_settings_keys}
                return Response(updated_discussion_settings)
            else:
                return Response({'errors': errors}, status.HTTP_400_BAD_REQUEST)
