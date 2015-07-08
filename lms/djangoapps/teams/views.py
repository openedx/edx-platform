"""HTTP endpoints for the Teams API."""

from django.shortcuts import render_to_response
from courseware.courses import get_course_with_access, has_access
from django.http import Http404
from django.conf import settings
from django.core.paginator import Paginator
from django.views.generic.base import View

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.authentication import (
    SessionAuthentication,
    OAuth2Authentication
)
from rest_framework import status
from rest_framework import permissions

from django.db.models import Count
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop

from student.models import CourseEnrollment, CourseAccessRole
from student.roles import CourseStaffRole

from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.permissions import IsStaffOrReadOnly
from openedx.core.lib.api.view_utils import (
    RetrievePatchAPIView,
    add_serializer_errors,
    build_api_error,
    ExpandableFieldViewMixin
)
from openedx.core.lib.api.serializers import PaginationSerializer

from xmodule.modulestore.django import modulestore

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .models import CourseTeam, CourseTeamMembership
from .serializers import CourseTeamSerializer, CourseTeamCreationSerializer, TopicSerializer, MembershipSerializer
from .errors import AlreadyOnTeamInCourse, NotEnrolledInCourseForTeam


# Constants
TOPICS_PER_PAGE = 12


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

        sort_order = 'name'
        topics = get_ordered_topics(course, sort_order)
        topics_page = Paginator(topics, TOPICS_PER_PAGE).page(1)
        topics_serializer = PaginationSerializer(instance=topics_page, context={'sort_order': sort_order})
        context = {
            "course": course, "topics": topics_serializer.data, "topics_url": reverse('topics_list', request=request)
        }
        return render_to_response("teams/teams.html", context)


def is_feature_enabled(course):
    """
    Returns True if the teams feature is enabled.
    """
    return settings.FEATURES.get('ENABLE_TEAMS', False) and course.teams_enabled


def has_team_api_access(user, course_key, access_username=None):
    """Returns True if the user has access to the Team API for the course
    given by `course_key`. The user must either be enrolled in the course,
    be course staff, or be global staff.

    Args:
      user (User): The user to check access for.
      course_key (CourseKey): The key to the course which we are checking access to.
      access_username (string): If provided, access_username must match user.username for non staff access.

    Returns:
      bool: True if the user has access, False otherwise.
    """
    if user.is_staff:
        return True
    if CourseStaffRole(course_key).has_user(user):
        return True
    if not access_username or access_username == user.username:
        return CourseEnrollment.is_enrolled(user, course_key)
    return False


class TeamsListView(ExpandableFieldViewMixin, GenericAPIView):
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

            * expand: Comma separated list of types for which to return
              expanded representations. Supports "user" and "team".

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

            If the user is not logged in, a 401 error is returned.

            If the user is not enrolled in the course specified by course_id or
            is not course or global staff, a 403 error is returned.

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

            If the user is not logged in, a 401 error is returned.

            If the user is not enrolled in the course, or is not course or
            global staff, a 403 error is returned.

            If the course_id is not valid or extra fields are included in the
            request, a 400 error is returned.

            If the specified course does not exist, a 404 error is returned.
    """

    # OAuth2Authentication must come first to return a 401 for unauthenticated users
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = CourseTeamSerializer

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
                error = build_api_error(
                    ugettext_noop("The supplied course id {course_id} is not valid."),
                    course_id=course_id_string,
                )
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

            if not has_team_api_access(request.user, course_key):
                return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(
                build_api_error(ugettext_noop("course_id must be provided")),
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'topic_id' in request.QUERY_PARAMS:
            result_filter.update({'topic_id': request.QUERY_PARAMS['topic_id']})
        if 'include_inactive' in request.QUERY_PARAMS and request.QUERY_PARAMS['include_inactive'].lower() == 'true':
            del result_filter['is_active']
        if 'text_search' in request.QUERY_PARAMS:
            return Response(
                build_api_error(ugettext_noop("text_search is not yet supported.")),
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = CourseTeam.objects.filter(**result_filter)

        order_by_input = request.QUERY_PARAMS.get('order_by', 'name')
        if order_by_input == 'name':
            queryset = queryset.extra(select={'lower_name': "lower(name)"})
            order_by_field = 'lower_name'
        elif order_by_input == 'open_slots':
            queryset = queryset.annotate(team_size=Count('users'))
            order_by_field = 'team_size'
        elif order_by_input == 'last_activity':
            return Response(
                build_api_error(ugettext_noop("last_activity is not yet supported")),
                status=status.HTTP_400_BAD_REQUEST
            )

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
            field_errors['course_id'] = build_api_error(
                ugettext_noop('The supplied course_id {course_id} is not valid.'),
                course_id=course_id
            )

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


class TeamsDetailView(ExpandableFieldViewMixin, RetrievePatchAPIView):
    """
        **Use Cases**

            Get or update a course team's information. Updates are supported
            only through merge patch.

        **Example Requests**:

            GET /api/team/v0/teams/{team_id}}

            PATCH /api/team/v0/teams/{team_id} "application/merge-patch+json"

        **Query Parameters for GET**

            * expand: Comma separated list of types for which to return
              expanded representations. Supports "user" and "team".

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

            If the user is not logged in, a 401 error is returned.

            If the user is not course or global staff, a 403 error is returned.

            If the specified team does not exist, a 404 error is returned.

        **Response Values for PATCH**

            Only staff can patch teams.

            If the user is anonymous or inactive, a 401 is returned.

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

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
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

            If the user is not logged in, a 401 error is returned.

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

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = TOPICS_PER_PAGE
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = TopicSerializer

    def get(self, request):
        """GET /api/team/v0/topics/?course_id={course_id}"""
        course_id_string = request.QUERY_PARAMS.get('course_id', None)
        if course_id_string is None:
            return Response({
                'field_errors': {
                    'course_id': build_api_error(
                        ugettext_noop("The supplied course id {course_id} is not valid."),
                        course_id=course_id_string
                    )
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

        ordering = request.QUERY_PARAMS.get('order_by', 'name')
        if ordering == 'name':
            topics = get_ordered_topics(course_module, ordering)
        else:
            return Response({
                'developer_message': "unsupported order_by value {}".format(ordering),
                'user_message': _(u"The ordering {} is not supported").format(ordering),
            }, status=status.HTTP_400_BAD_REQUEST)

        page = self.paginate_queryset(topics)
        serializer = self.get_pagination_serializer(page)
        serializer.context = {'sort_order': ordering}
        return Response(serializer.data)  # pylint: disable=maybe-no-member


def get_ordered_topics(course_module, ordering):
    """Return a sorted list of team topics.

    Arguments:
        course_module (xmodule): the course which owns the team topics
        ordering (str): the key belonging to topic dicts by which we sort

    Returns:
        list: a list of sorted team topics
    """
    return sorted(course_module.teams_topics, key=lambda t: t[ordering].lower())


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

            If the user is not logged in, a 401 error is returned.

            If the topic_id course_id are not given or an unsupported value is
            passed for order_by, returns a 400 error.

            If the user is not enrolled in the course, or is not course or
            global staff, returns a 403 error.

            If the course does not exist, returns a 404 error.

            Otherwise, a 200 response is returned containing the following fields:

            * id: The topic's unique identifier.

            * name: The name of the topic.

            * description: A description of the topic.

    """

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
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


class MembershipListView(ExpandableFieldViewMixin, GenericAPIView):
    """
        **Use Cases**

            List course team memberships or add a user to a course team.

        **Example Requests**:

            GET /api/team/v0/team_membership

            POST /api/team/v0/team_membership

        **Query Parameters for GET**

            At least one of username and team_id must be provided.

            * username: Returns membership records only for the specified user.
              If the requesting user is not staff then only memberships for
              teams associated with courses in which the requesting user is
              enrolled are returned.

            * team_id: Returns only membership records associated with the
              specified team. The requesting user must be staff or enrolled in
              the course associated with the team.

            * page_size: Number of results to return per page.

            * page: Page number to retrieve.

            * expand: Comma separated list of types for which to return
              expanded representations. Supports "user" and "team".

        **Response Values for GET**

            If the user is logged in and enrolled, the response contains:

            * count: The total number of memberships matching the request.

            * next: The URL to the next page of results, or null if this is the
              last page.

            * previous: The URL to the previous page of results, or null if this
              is the first page.

            * num_pages: The total number of pages in the result.

            * results: A list of the memberships matching the request.

                * user: The user associated with the membership. This field may
                  contain an expanded or collapsed representation.

                * team: The team associated with the membership. This field may
                  contain an expanded or collapsed representation.

                * date_joined: The date and time the membership was created.

            For all text fields, clients rendering the values should take care
            to HTML escape them to avoid script injections, as the data is
            stored exactly as specified. The intention is that plain text is
            supported, not HTML.

            If the user is not logged in and active, a 401 error is returned.

            If neither team_id nor username are provided, a 400 error is
            returned.

            If team_id is provided but the team does not exist, a 404 error is
            returned.

            This endpoint uses 404 error codes to avoid leaking information
            about team or user existence. Specifically, a 404 error will be
            returned if a logged in user specifies a team_id for a course
            they are not enrolled in.

            Additionally, when username is specified the list of returned
            memberships will be filtered to memberships in teams associated
            with courses that the requesting user is enrolled in.

        **Response Values for POST**

            Any logged in user enrolled in a course can enroll themselves in a
            team in the course. Course and global staff can enroll any user in
            a team, with a few exceptions noted below.

            If the user is not logged in and active, a 401 error is returned.

            If username and team are not provided in the posted JSON, a 400
            error is returned describing the missing fields.

            If the specified team does not exist, a 404 error is returned.

            If the user is not staff and is not enrolled in the course
            associated with the team they are trying to join, or if they are
            trying to add a user other than themselves to a team, a 404 error
            is returned. This is to prevent leaking information about the
            existence of teams and users.

            If the specified user does not exist, a 404 error is returned.

            If the user is already a member of a team in the course associated
            with the team they are trying to join, a 400 error is returned.
            This applies to both staff and students.

            If the user is not enrolled in the course associated with the team
            they are trying to join, a 400 error is returned. This can occur
            when a staff user posts a request adding another user to a team.
    """

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = MembershipSerializer

    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer

    def get(self, request):
        """GET /api/team/v0/team_membership"""
        queryset = CourseTeamMembership.objects.all()

        specified_username_or_team = False

        if 'team_id' in request.QUERY_PARAMS:
            specified_username_or_team = True
            team_id = request.QUERY_PARAMS['team_id']
            try:
                team = CourseTeam.objects.get(team_id=team_id)
            except CourseTeam.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if not has_team_api_access(request.user, team.course_id):
                return Response(status=status.HTTP_404_NOT_FOUND)
            queryset = queryset.filter(team__team_id=team_id)

        if 'username' in request.QUERY_PARAMS:
            specified_username_or_team = True
            if not request.user.is_staff:
                enrolled_courses = (
                    CourseEnrollment.enrollments_for_user(request.user).values_list('course_id', flat=True)
                )
                staff_courses = (
                    CourseAccessRole.objects.filter(user=request.user, role='staff').values_list('course_id', flat=True)
                )
                valid_courses = [
                    CourseKey.from_string(course_key_string)
                    for course_list in [enrolled_courses, staff_courses]
                    for course_key_string in course_list
                ]
                queryset = queryset.filter(team__course_id__in=valid_courses)
            queryset = queryset.filter(user__username=request.QUERY_PARAMS['username'])

        if not specified_username_or_team:
            return Response(
                build_api_error(ugettext_noop("username or team_id must be specified.")),
                status=status.HTTP_400_BAD_REQUEST
            )

        page = self.paginate_queryset(queryset)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)  # pylint: disable=maybe-no-member

    def post(self, request):
        """POST /api/team/v0/team_membership"""
        field_errors = {}

        if 'username' not in request.DATA:
            field_errors['username'] = build_api_error(ugettext_noop("Username is required."))

        if 'team_id' not in request.DATA:
            field_errors['team_id'] = build_api_error(ugettext_noop("Team id is required."))

        if field_errors:
            return Response({
                'field_errors': field_errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            team = CourseTeam.objects.get(team_id=request.DATA['team_id'])
        except CourseTeam.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        username = request.DATA['username']
        if not has_team_api_access(request.user, team.course_id, access_username=username):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            membership = team.add_user(user)
        except AlreadyOnTeamInCourse:
            return Response(
                build_api_error(
                    ugettext_noop("The user {username} is already a member of a team in this course."),
                    username=username
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        except NotEnrolledInCourseForTeam:
            return Response(
                build_api_error(
                    ugettext_noop("The user {username} is not enrolled in the course associated with this team."),
                    username=username
                ),
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance=membership)
        return Response(serializer.data)


class MembershipDetailView(ExpandableFieldViewMixin, GenericAPIView):
    """
        **Use Cases**

            Gets individual course team memberships or removes a user from a course team.

        **Example Requests**:

            GET /api/team/v0/team_membership/{team_id},{username}

            DELETE /api/team/v0/team_membership/{team_id},{username}

        **Query Parameters for GET**

            * expand: Comma separated list of types for which to return
              expanded representations. Supports "user" and "team".

        **Response Values for GET**

            If the user is logged in and enrolled, or is course or global staff
            the response contains:

            * user: The user associated with the membership. This field may
              contain an expanded or collapsed representation.

            * team: The team associated with the membership. This field may
              contain an expanded or collapsed representation.

            * date_joined: The date and time the membership was created.

            For all text fields, clients rendering the values should take care
            to HTML escape them to avoid script injections, as the data is
            stored exactly as specified. The intention is that plain text is
            supported, not HTML.

            If the user is not logged in and active, a 401 error is returned.

            If specified team does not exist, a 404 error is returned.

            If the user is logged in but is not enrolled in the course
            associated with the specified team, or is not staff, a 404 error is
            returned. This avoids leaking information about course or team
            existence.

            If the membership does not exist, a 404 error is returned.

        **Response Values for DELETE**

            Any logged in user enrolled in a course can remove themselves from
            a team in the course. Course and global staff can remove any user
            from a team. Successfully deleting a membership will return a 204
            response with no content.

            If the user is not logged in and active, a 401 error is returned.

            If the specified team or username does not exist, a 404 error is
            returned.

            If the user is not staff and is attempting to remove another user
            from a team, a 404 error is returned. This prevents leaking
            information about team and user existence.

            If the membership does not exist, a 404 error is returned.
    """

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = MembershipSerializer

    def get_team(self, team_id):
        """Returns the team with team_id, or throws Http404 if it does not exist."""
        try:
            return CourseTeam.objects.get(team_id=team_id)
        except CourseTeam.DoesNotExist:
            raise Http404

    def get_membership(self, username, team):
        """Returns the membership for the given user and team, or throws Http404 if it does not exist."""
        try:
            return CourseTeamMembership.objects.get(user__username=username, team=team)
        except CourseTeamMembership.DoesNotExist:
            raise Http404

    def get(self, request, team_id, username):
        """GET /api/team/v0/team_membership/{team_id},{username}"""
        team = self.get_team(team_id)
        if not has_team_api_access(request.user, team.course_id):
            return Response(status=status.HTTP_404_NOT_FOUND)

        membership = self.get_membership(username, team)

        serializer = self.get_serializer(instance=membership)
        return Response(serializer.data)

    def delete(self, request, team_id, username):
        """DELETE /api/team/v0/team_membership/{team_id},{username}"""
        team = self.get_team(team_id)
        if has_team_api_access(request.user, team.course_id, access_username=username):
            membership = self.get_membership(username, team)
            membership.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
