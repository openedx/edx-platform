"""
Views for user API
"""

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor

from django.shortcuts import redirect
from django.utils import dateparse

from rest_framework import generics, permissions, views
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courseware.views import get_current_child, save_positions_recursively_up

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError

from student.models import CourseEnrollment, User

from mobile_api.utils import mobile_available_when_enrolled

from xblock.fields import Scope
from xblock.runtime import KeyValueStore
from xmodule.modulestore.django import modulestore


from .serializers import CourseEnrollmentSerializer, UserSerializer
from mobile_api import errors


class IsUser(permissions.BasePermission):
    """
    Permission that checks to see if the request user matches the User models
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj


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
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUser)
    queryset = (
        User.objects.all()
        .select_related('profile', 'course_enrollments')
    )
    serializer_class = UserSerializer
    lookup_field = 'username'


@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
class UserCourseStatus(views.APIView):
    """
    Endpoints for getting and setting meta data
    about a user's status within a given course.
    """

    http_method_names = ["get", "patch"]

    def _last_visited_module_id(self, request, course):
        """
        Returns the id of the last module visited by the current user in the given course.
        If there is no such visit returns the default (the first item deep enough down the course tree)
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2)

        course_module = get_module_for_descriptor(request.user, request, course, field_data_cache, course.id)
        current = course_module

        child = current
        while child:
            child = get_current_child(current)
            if child:
                current = child

        return current

    def _process_arguments(self, request, username, course_id, course_handler):
        """
        Checks and processes the arguments to our endpoint
        then passes the processed and verified arguments on to something that
        does the work specific to the individual case
        """
        if username != request.user.username:
            return Response(errors.ERROR_INVALID_USER_ID, status=403)

        course = None
        try:
            course_key = CourseKey.from_string(course_id)
            course = modulestore().get_course(course_key, depth=None)
        except InvalidKeyError:
            pass

        if not course:
            return Response(errors.ERROR_INVALID_COURSE_ID, status=404)  # pylint: disable=lost-exception

        return course_handler(course)

    def get_course_info(self, request, course):
        """
        Returns the course status
        """
        current_module = self._last_visited_module_id(request, course)
        return Response({"last_visited_module_id": unicode(current_module.location)})

    def get(self, request, username, course_id):
        """
        **Use Case**

            Get meta data about user's status within a specific course

        **Example request**:

            GET /api/mobile/v0.5/users/{username}/course_status_info/{course_id}

        **Response Values**

        * last_visited_module_id: The id of the last module visited by the user in the given course

        """

        return self._process_arguments(request, username, course_id, lambda course: self.get_course_info(request, course))

    def _update_last_visited_module_id(self, request, course, module_key, modification_date):
        """
        Saves the module id if the found modification_date is less recent than the passed modification date
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=2)
        module_descriptor = modulestore().get_item(module_key)
        module = get_module_for_descriptor(request.user, request, module_descriptor, field_data_cache, course.id)

        if modification_date:
            key = KeyValueStore.Key(
                scope=Scope.user_state,
                user_id=request.user.id,
                block_scope_id=course.location,
                field_name=None
            )
            student_module = field_data_cache.find(key)
            if student_module:
                original_store_date = student_module.modified
                if modification_date < original_store_date:
                    # old modification date so skip update
                    return self.get_course_info(request, course)

        if module:
            save_positions_recursively_up(request.user, request, field_data_cache, module)
            return self.get_course_info(request, course)
        else:
            return Response(errors.ERROR_INVALID_MODULE_ID, status=400)

    def patch(self, request, username, course_id):
        """
        **Use Case**

            Update meta data about user's status within a specific course

        **Example request**:

            PATCH /api/mobile/v0.5/users/{username}/course_status_info/{course_id}
            body:
                last_visited_module_id={module_id}
                modification_date={date}

            modification_date is optional. If it is present, the update will only take effect
            if modification_date is later than the modification_date saved on the server

        **Response Values**

        The same as doing a GET on this path

        """
        def handle_course(course):
            """
            Updates the course_status once the arguments are checked
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
                return self.get_course_info(request, course)

        return self._process_arguments(request, username, course_id, handle_course)


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
        * course: A collection of data about the course:

          * course_about: The URI to get the data for the course About page.
          * course_updates: The URI to get data for course updates.
          * number: The course number.
          * org: The organization that created the course.
          * video_outline: The URI to get the list of all vides the user can
            access in the course.
          * id: The unique ID of the course.
          * latest_updates:  Reserved for future use.
          * end: The end date of the course.
          * name: The name of the course.
          * course_handouts: The URI to get data for course handouts.
          * start: The data and time the course starts.
          * course_image: The path to the course image.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUser)
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    lookup_field = 'username'

    def get_queryset(self):
        qset = self.queryset.filter(
            user__username=self.kwargs['username'], is_active=True
        ).order_by('created')
        return mobile_course_enrollments(qset, self.request.user)


@api_view(["GET"])
@authentication_classes((OAuth2Authentication, SessionAuthentication))
@permission_classes((IsAuthenticated,))
def my_user_info(request):
    """
    Redirect to the currently-logged-in user's info page
    """
    return redirect("user-detail", username=request.user.username)


def mobile_course_enrollments(enrollments, user):
    """
    Return enrollments only if courses are mobile_available (or if the user has
    privileged (beta, staff, instructor) access)

    :param enrollments is a list of CourseEnrollments.
    """
    for enr in enrollments:
        course = enr.course

        if mobile_available_when_enrolled(course, user):
            yield enr
