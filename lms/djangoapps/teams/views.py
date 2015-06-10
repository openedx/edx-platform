"""HTTP endpoints for the Teams API."""

from django.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access, has_access
from django.http import Http404
from django.conf import settings
from django.views.generic.base import View

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import (
    SessionAuthentication,
    OAuth2Authentication
)
from rest_framework import status
from rest_framework import permissions

from django.db.models import Count
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop

from student.models import CourseEnrollment
from student.roles import CourseStaffRole

from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.permissions import IsStaffOrReadOnly
from openedx.core.lib.api.view_utils import RetrievePatchAPIView, add_serializer_errors
from openedx.core.lib.api.serializers import PaginationSerializer

from xmodule.modulestore.django import modulestore

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .models import CourseTeam
from .serializers import CourseTeamSerializer, CourseTeamCreationSerializer, TopicSerializer


class TeamsDashboardView(View):
    """
    View methods related to the teams dashboard.
    """

    def get(self, request, course_id):
        """
        Renders the teams dashboard, which is shown on the "Teams" tab.

        Raises a 404 if the course specified by course_id does not exist, the
        user is not registered for the course, or the teams feature is not enabled.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)

        if not is_feature_enabled(course):
            raise Http404

        if not CourseEnrollment.is_enrolled(request.user, course.id) and \
                not has_access(request.user, 'staff', course, course.id):
            raise Http404

        context = {"course": course}
        return render_to_response("teams/teams.html", context)


def is_feature_enabled(course):
    """
    Returns True if the teams feature is enabled.
    """
    return settings.FEATURES.get('ENABLE_TEAMS', False) and course.teams_enabled


def has_team_api_access(user, course_key):
    """Returns True if the user has access to the Team API for the course
    given by `course_key`. The user must either be enrolled in the course,
    be course staff, or be global staff.

    Args:
      user (User): The user to check access for.
      course_key (CourseKey): The key to the course which we are checking access to.

    Returns:
      bool: True if the user has access, False otherwise.
    """
    return (CourseEnrollment.is_enrolled(user, course_key) or
            CourseStaffRole(course_key).has_user(user) or
            user.is_staff)


class TeamsListView(GenericAPIView):
    """
        **Use Cases**

            Get or create a course team.

        **Example Requests**:

            GET /api/team/v0/teams

            POST /api/team/v0/teams

        **Query Parameters for GET**

            * course_id: Filters the result to teams belonging to the given
              course. Required.

            * topic_id: Filters the result to teams associated with the given
              topic.

            * text_search: Currently not supported.

            * order_by: Must be one of the following:

                * name: Orders results by case insensitive team name (default).

                * open_slots: Orders results by most open slots.

                * last_activity: Currently not supported.

            * page_size: Number of results to return per page.

            * page: Page number to retrieve.

            * include_inactive: If true, inactive teams will be returned. The
              default is to not include inactive teams.

        **Response Values for GET**

            If the user is logged in and enrolled, the response contains:

            * count: The total number of teams matching the request.

            * next: The URL to the next page of results, or null if this is the
              last page.

            * previous: The URL to the previous page of results, or null if this
              is the first page.

            * num_pages: The total number of pages in the result.

            * results: A list of the teams matching the request.

                * id: The team's unique identifier.

                * name: The name of the team.

                * is_active: True if the team is currently active. If false, the
                  team is considered "soft deleted" and will not be included by
                  default in results.

                * course_id: The identifier for the course this team belongs to.

                * topic_id: Optionally specifies which topic the team is associated
                  with.

                * date_created: Date and time when the team was created.

                * description: A description of the team.

                * country: Optionally specifies which country the team is
                  associated with.

                * language: Optionally specifies which language the team is
                  associated with.

                * membership: A list of the users that are members of the team.
                  See membership endpoint for more detail.

            For all text fields, clients rendering the values should take care
            to HTML escape them to avoid script injections, as the data is
            stored exactly as specified. The intention is that plain text is
            supported, not HTML.

            If the user is not logged in and enrolled in the course specified by
            course_id or is not course or global staff, a 403 error is returned.

            If the specified course_id is not valid or the user attempts to
            use an unsupported query parameter, a 400 error is returned.

            If the response does not exist, a 404 error is returned. For
            example, the course_id may not reference a real course or the page
            number may be beyond the last page.

        **Response Values for POST**

            Any logged in user who has verified their email address can create
            a team. The format mirrors that of a GET for an individual team,
            but does not include the id, is_active, date_created, or membership
            fields. id is automatically computed based on name.

            If the user is not logged in, is not enrolled in the course, or is
            not course or global staff, a 403 error is returned.

            If the course_id is not valid or extra fields are included in the
            request, a 400 error is returned.

            If the specified course does not exist, a 404 error is returned.
    """

    # SessionAuthentication must come first to return a 403 for unauthenticated users
    authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = CourseTeamSerializer

    def get_serializer_context(self):
        """Adds expand information from query parameters to the serializer context to support expandable fields."""
        result = super(TeamsListView, self).get_serializer_context()
        result['expand'] = [x for x in self.request.QUERY_PARAMS.get('expand', '').split(',') if x]
        return result

    def get(self, request):
        """GET /api/team/v0/teams/"""
        result_filter = {
            'is_active': True
        }

        if 'course_id' in request.QUERY_PARAMS:
            course_id_string = request.QUERY_PARAMS['course_id']
            try:
                course_key = CourseKey.from_string(course_id_string)
                # Ensure the course exists
                if not modulestore().has_course(course_key):
                    return Response(status=status.HTTP_404_NOT_FOUND)
                result_filter.update({'course_id': course_key})
            except InvalidKeyError:
                error_message = ugettext_noop("The supplied course id {course_id} is not valid.").format(
                    course_id=course_id_string
                )
                return Response({
                    'developer_message': error_message,
                    'user_message': _(error_message)  # pylint: disable=translation-of-non-string
                }, status=status.HTTP_400_BAD_REQUEST)

            if not has_team_api_access(request.user, course_key):
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            error_message = ugettext_noop('course_id must be provided')
            return Response({
                'developer_message': error_message,
                'user_message': _(error_message),  # pylint: disable=translation-of-non-string
            }, status=status.HTTP_400_BAD_REQUEST)

        if 'topic_id' in request.QUERY_PARAMS:
            result_filter.update({'topic_id': request.QUERY_PARAMS['topic_id']})
        if 'include_inactive' in request.QUERY_PARAMS and request.QUERY_PARAMS['include_inactive'].lower() == 'true':
            del result_filter['is_active']
        if 'text_search' in request.QUERY_PARAMS:
            error_message = ugettext_noop('text_search is not yet supported')
            return Response({
                'developer_message': error_message,
                'user_message': _(error_message),  # pylint: disable=translation-of-non-string
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = CourseTeam.objects.filter(**result_filter)

        order_by_input = request.QUERY_PARAMS.get('order_by', 'name')
        if order_by_input == 'name':
            queryset = queryset.extra(select={'lower_name': "lower(name)"})
            order_by_field = 'lower_name'
        elif order_by_input == 'open_slots':
            queryset = queryset.annotate(team_size=Count('users'))
            order_by_field = 'team_size'
        elif order_by_input == 'last_activity':
            return Response({
                'developer_message': "last_activity is not yet supported",
                'user_message': _("The last_activity parameter is not yet supported."),
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = queryset.order_by(order_by_field)

        if not queryset:
            return Response(status=status.HTTP_404_NOT_FOUND)

        page = self.paginate_queryset(queryset)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)  # pylint: disable=maybe-no-member

    def post(self, request):
        """POST /api/team/v0/teams/"""
        field_errors = {}
        course_key = None

        course_id = request.DATA.get('course_id')
        try:
            course_key = CourseKey.from_string(course_id)
            # Ensure the course exists
            if not modulestore().has_course(course_key):
                return Response(status=status.HTTP_404_NOT_FOUND)
        except InvalidKeyError:
            field_errors['course_id'] = {
                'developer_message': "course_id {} is not valid.".format(course_id),
                'user_message': _("The supplied course_id {} is not valid.").format(course_id),
            }

        if course_key and not has_team_api_access(request.user, course_key):
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.DATA.copy()
        data['course_id'] = course_key

        serializer = CourseTeamCreationSerializer(data=data)
        add_serializer_errors(serializer, data, field_errors)

        if field_errors:
            return Response({
                'field_errors': field_errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            team = serializer.save()
            return Response(CourseTeamSerializer(team).data)


class TeamsDetailView(RetrievePatchAPIView):
    """
        **Use Cases**

            Get or update a course team's information. Updates are supported
            only through merge patch.

        **Example Requests**:

            GET /api/team/v0/teams/{team_id}}

            PATCH /api/team/v0/teams/{team_id} "application/merge-patch+json"

        **Response Values for GET**

            If the user is logged in, the response contains the following fields:

                * id: The team's unique identifier.

                * name: The name of the team.

                * is_active: True if the team is currently active. If false, the team
                  is considered "soft deleted" and will not be included by default in
                  results.

                * course_id: The identifier for the course this team belongs to.

                * topic_id: Optionally specifies which topic the team is
                  associated with.

                * date_created: Date and time when the team was created.

                * description: A description of the team.

                * country: Optionally specifies which country the team is
                  associated with.

                * language: Optionally specifies which language the team is
                  associated with.

                * membership: A list of the users that are members of the team. See
                  membership endpoint for more detail.

            For all text fields, clients rendering the values should take care
            to HTML escape them to avoid script injections, as the data is
            stored exactly as specified. The intention is that plain text is
            supported, not HTML.

            If the user is not logged in or is not course or global staff, a 403
            error is returned.

            If the specified team does not exist, a 404 error is returned.

        **Response Values for PATCH**

            Only staff can patch teams.

            If the user is anonymous or inactive, a 403 is returned.
            If the user is logged in and the team does not exist, a 404 is returned.
            If the user is not course or global staff and the team does exist,
            a 403 is returned.

            If "application/merge-patch+json" is not the specified content type,
            a 415 error is returned.

            If the update could not be completed due to validation errors, this
            method returns a 400 error with all error messages in the
            "field_errors" field of the returned JSON.
    """

    class IsEnrolledOrIsStaff(permissions.BasePermission):
        """Permission that checks to see if the user is enrolled in the course or is staff."""

        def has_object_permission(self, request, view, obj):
            """Returns true if the user is enrolled or is staff."""
            return has_team_api_access(request.user, obj.course_id)

    authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly, IsEnrolledOrIsStaff,)
    lookup_field = 'team_id'
    serializer_class = CourseTeamSerializer
    parser_classes = (MergePatchParser,)

    def get_queryset(self):
        """Returns the queryset used to access the given team."""
        return CourseTeam.objects.all()


class TopicListView(GenericAPIView):
    """
        **Use Cases**

            Retrieve a list of topics associated with a single course.

        **Example Requests**

            GET /api/team/v0/topics/?course_id={course_id}

        **Query Parameters for GET**

            * course_id: Filters the result to topics belonging to the given
              course (required).

            * order_by: Orders the results. Currently only 'name' is supported,
              and is also the default value.

            * page_size: Number of results to return per page.

            * page: Page number to retrieve.

        **Response Values for GET**

            If the course_id is not given or an unsupported value is passed for
            order_by, returns a 400 error.

            If the user is not logged in, is not enrolled in the course, or is
            not course or global staff, returns a 403 error.

            If the course does not exist, returns a 404 error.

            Otherwise, a 200 response is returned containing the following
            fields:

            * count: The total number of topics matching the request.

            * next: The URL to the next page of results, or null if this is the
              last page.

            * previous: The URL to the previous page of results, or null if this
              is the first page.

            * num_pages: The total number of pages in the result.

            * results: A list of the topics matching the request.

                * id: The topic's unique identifier.

                * name: The name of the topic.

                * description: A description of the topic.

    """

    authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = TopicSerializer

    def get(self, request):
        """GET /api/team/v0/topics/?course_id={course_id}"""
        course_id_string = request.QUERY_PARAMS.get('course_id', None)
        if course_id_string is None:
            return Response({
                'field_errors': {
                    'course_id': {
                        'developer_message': "course_id {} is not valid.".format(course_id_string),
                        'user_message': _('The supplied course_id {} is not valid.').format(course_id_string)
                    }
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            course_id = CourseKey.from_string(course_id_string)
        except InvalidKeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Ensure the course exists
        course_module = modulestore().get_course(course_id)
        if course_module is None:  # course is None if not found
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not has_team_api_access(request.user, course_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        topics = course_module.teams_topics

        ordering = request.QUERY_PARAMS.get('order_by', 'name')
        if ordering == 'name':
            topics = sorted(topics, key=lambda t: t['name'].lower())
        else:
            return Response({
                'developer_message': "unsupported order_by value {}".format(ordering),
                'user_message': _(u"The ordering {} is not supported").format(ordering),
            }, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(topics)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)  # pylint: disable=maybe-no-member


class TopicDetailView(APIView):
    """
        **Use Cases**

            Retrieve a single topic from a course.

        **Example Requests**

            GET /api/team/v0/topics/{topic_id},{course_id}

        **Query Parameters for GET**

            * topic_id: The ID of the topic to retrieve (required).

            * course_id: The ID of the course to retrieve the topic from
              (required).

        **Response Values for GET**

            If the topic_id course_id are not given or an unsupported value is
            passed for order_by, returns a 400 error.

            If the user is not logged in, is not enrolled in the course, or is
            not course or global staff, returns a 403 error.

            If the course does not exist, returns a 404 error.

            Otherwise, a 200 response is returned containing the following fields:

            * id: The topic's unique identifier.

            * name: The name of the topic.

            * description: A description of the topic.

    """

    authentication_classes = (SessionAuthentication, OAuth2Authentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, topic_id, course_id):
        """GET /api/team/v0/topics/{topic_id},{course_id}/"""
        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # Ensure the course exists
        course_module = modulestore().get_course(course_id)
        if course_module is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not has_team_api_access(request.user, course_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        topics = [t for t in course_module.teams_topics if t['id'] == topic_id]

        if len(topics) == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = TopicSerializer(topics[0])
        return Response(serializer.data)
