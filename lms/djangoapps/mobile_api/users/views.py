"""
Views for user API
"""

from django.shortcuts import redirect
from django.utils import dateparse

from rest_framework import generics, views
from rest_framework.decorators import api_view
from rest_framework.response import Response

from opaque_keys.edx.keys import UsageKey
from opaque_keys import InvalidKeyError

from courseware.access import is_mobile_available_for_user
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from courseware.views import get_current_child, save_positions_recursively_up
from student.models import CourseEnrollment, User

from xblock.fields import Scope
from xblock.runtime import KeyValueStore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .serializers import CourseEnrollmentSerializer, UserSerializer
from .. import errors
from ..utils import mobile_view, mobile_course_access


@mobile_view(is_user=True)
class UserDetail(generics.RetrieveAPIView):
    """
    **Use Case**

        Get information about the specified user and
        access other resources the user has permissions for.

        Users are redirected to this endpoint after logging in.

        You can use the **course_enrollments** value in
        the response to get a list of courses the user is enrolled in.

    **Example request**:

        GET /api/mobile/v0.5/users/{username}


    **Response Values**

        * id: The ID of the user.

        * username: The username of the currently logged in user.

        * email: The email address of the currently logged in user.

        * name: The full name of the currently logged in user.

        * course_enrollments: The URI to list the courses the currently logged
          in user is enrolled in.
    """
    queryset = (
        User.objects.all()
        .select_related('profile', 'course_enrollments')
    )
    serializer_class = UserSerializer
    lookup_field = 'username'


@mobile_view(is_user=True)
class UserCourseStatus(views.APIView):
    """
    **Use Case**

        Get or update the ID of the module that the specified user last visited in the specified course.

    **Example request**:

        GET /api/mobile/v0.5/users/{username}/course_status_info/{course_id}

        PATCH /api/mobile/v0.5/users/{username}/course_status_info/{course_id}

            body:
                last_visited_module_id={module_id}
                modification_date={date}

            The modification_date is optional. If it is present, the update will only take effect
            if the modification_date is later than the modification_date saved on the server.

    **Response Values**

        * last_visited_module_id: The ID of the last module visited by the user in the course.

        * last_visited_module_path: The ID of the modules in the path from the
          last visited module to the course module.
    """

    http_method_names = ["get", "patch"]

    def _last_visited_module_path(self, request, course):
        """
        Returns the path from the last module visited by the current user in the given course up to
        the course module. If there is no such visit, the first item deep enough down the course
        tree is used.
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2)

        course_module = get_module_for_descriptor(
            request.user, request, course, field_data_cache, course.id, course=course
        )

        path = [course_module]
        chapter = get_current_child(course_module, min_depth=2)
        if chapter is not None:
            path.append(chapter)
            section = get_current_child(chapter, min_depth=1)
            if section is not None:
                path.append(section)

        path.reverse()
        return path

    def _get_course_info(self, request, course):
        """
        Returns the course status
        """
        path = self._last_visited_module_path(request, course)
        path_ids = [unicode(module.location) for module in path]
        return Response({
            "last_visited_module_id": path_ids[0],
            "last_visited_module_path": path_ids,
        })

    def _update_last_visited_module_id(self, request, course, module_key, modification_date):
        """
        Saves the module id if the found modification_date is less recent than the passed modification date
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2)
        try:
            module_descriptor = modulestore().get_item(module_key)
        except ItemNotFoundError:
            return Response(errors.ERROR_INVALID_MODULE_ID, status=400)
        module = get_module_for_descriptor(
            request.user, request, module_descriptor, field_data_cache, course.id, course=course
        )

        if modification_date:
            key = KeyValueStore.Key(
                scope=Scope.user_state,
                user_id=request.user.id,
                block_scope_id=course.location,
                field_name='position'
            )
            original_store_date = field_data_cache.last_modified(key)
            if original_store_date is not None and modification_date < original_store_date:
                # old modification date so skip update
                return self._get_course_info(request, course)

        save_positions_recursively_up(request.user, request, field_data_cache, module, course=course)
        return self._get_course_info(request, course)

    @mobile_course_access(depth=2)
    def get(self, request, course, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get the ID of the module that the specified user last visited in the specified course.
        """

        return self._get_course_info(request, course)

    @mobile_course_access(depth=2)
    def patch(self, request, course, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Update the ID of the module that the specified user last visited in the specified course.
        """
        module_id = request.DATA.get("last_visited_module_id")
        modification_date_string = request.DATA.get("modification_date")
        modification_date = None
        if modification_date_string:
            modification_date = dateparse.parse_datetime(modification_date_string)
            if not modification_date or not modification_date.tzinfo:
                return Response(errors.ERROR_INVALID_MODIFICATION_DATE, status=400)

        if module_id:
            try:
                module_key = UsageKey.from_string(module_id)
            except InvalidKeyError:
                return Response(errors.ERROR_INVALID_MODULE_ID, status=400)

            return self._update_last_visited_module_id(request, course, module_key, modification_date)
        else:
            # The arguments are optional, so if there's no argument just succeed
            return self._get_course_info(request, course)


@mobile_view(is_user=True)
class UserCourseEnrollmentsList(generics.ListAPIView):
    """
    **Use Case**

        Get information about the courses the currently logged in user is
        enrolled in.

    **Example request**:

        GET /api/mobile/v0.5/users/{username}/course_enrollments/

    **Response Values**

        * created: The date the course was created.
        * mode: The type of certificate registration for this course:  honor or
          certified.
        * is_active: Whether the course is currently active; true or false.
        * certificate: Information about the user's earned certificate in the course.
          * url: URL to the downloadable version of the certificate, if exists.
        * course: A collection of data about the course:

          * course_updates: The URI to get data for course updates.
          * number: The course number.
          * org: The organization that created the course.
          * video_outline: The URI to get the list of all vides the user can
            access in the course.
          * id: The unique ID of the course.
          * subscription_id: A unique "clean" (alphanumeric with '_') ID of the course.
          * latest_updates:  Reserved for future use.
          * end: The end date of the course.
          * name: The name of the course.
          * course_handouts: The URI to get data for course handouts.
          * start: The data and time the course starts.
          * course_image: The path to the course image.
    """
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    lookup_field = 'username'

    def get_queryset(self):
        enrollments = self.queryset.filter(
            user__username=self.kwargs['username'],
            is_active=True
        ).order_by('created').reverse()
        return [
            enrollment for enrollment in enrollments
            if enrollment.course_overview and
            is_mobile_available_for_user(self.request.user, enrollment.course_overview)
        ]


@api_view(["GET"])
@mobile_view()
def my_user_info(request):
    """
    Redirect to the currently-logged-in user's info page
    """
    return redirect("user-detail", username=request.user.username)
