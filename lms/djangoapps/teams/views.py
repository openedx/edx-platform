"""HTTP endpoints for the Teams API."""

import logging

from django.shortcuts import get_object_or_404, render_to_response
from django.http import Http404
from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework import status
from rest_framework import permissions
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django_countries import countries
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.permissions import IsStaffOrReadOnly
from openedx.core.lib.api.view_utils import (
    RetrievePatchAPIView,
    add_serializer_errors,
    build_api_error,
    ExpandableFieldViewMixin
)
from openedx.core.lib.api.paginators import paginate_search_results, DefaultPagination
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from courseware.courses import get_course_with_access, has_access
from student.models import CourseEnrollment, CourseAccessRole
from student.roles import CourseStaffRole
from django_comment_client.utils import has_discussion_privileges
from util.model_utils import truncate_fields
from . import is_feature_enabled
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from .serializers import (
    CourseTeamSerializer,
    CourseTeamCreationSerializer,
    TopicSerializer,
    BulkTeamCountTopicSerializer,
    MembershipSerializer,
    add_team_count
)
from .search_indexes import CourseTeamIndexer
from .errors import AlreadyOnTeamInCourse, ElasticSearchConnectionError, NotEnrolledInCourseForTeam
from .utils import emit_team_event

TEAM_MEMBERSHIPS_PER_PAGE = 2
TOPICS_PER_PAGE = 12
MAXIMUM_SEARCH_SIZE = 100000

log = logging.getLogger(__name__)


@receiver(post_save, sender=CourseTeam)
def team_post_save_callback(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """ Emits signal after the team is saved. """
    changed_fields = instance.field_tracker.changed()
    # Don't emit events when we are first creating the team.
    if not kwargs['created']:
        for field in changed_fields:
            if field not in instance.FIELD_BLACKLIST:
                truncated_fields = truncate_fields(unicode(changed_fields[field]), unicode(getattr(instance, field)))
                truncated_fields['team_id'] = instance.team_id
                truncated_fields['field'] = field

                emit_team_event(
                    'edx.team.changed',
                    instance.course_id,
                    truncated_fields
                )


class TeamAPIPagination(DefaultPagination):
    """
    Pagination format used by the teams API.
    """
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(TeamAPIPagination, self).get_paginated_response(data)

        # Add the current page to the response.
        # It may make sense to eventually move this field into the default
        # implementation, but for now, teams is the only API that uses this.
        response.data["current_page"] = self.page.number

        # This field can be derived from other fields in the response,
        # so it may make sense to have the JavaScript client calculate it
        # instead of including it in the response.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


class TopicsPagination(TeamAPIPagination):
    """Paginate topics. """
    page_size = TOPICS_PER_PAGE


class MyTeamsPagination(TeamAPIPagination):
    """Paginate the user's teams. """
    page_size = TEAM_MEMBERSHIPS_PER_PAGE


class TeamsDashboardView(GenericAPIView):
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

        user = request.user

        # Even though sorting is done outside of the serializer, sort_order needs to be passed
        # to the serializer so that the paginated results indicate how they were sorted.
        sort_order = 'name'
        topics = get_alphabetical_topics(course)

        # Paginate and serialize topic data
        # BulkTeamCountPaginatedTopicSerializer will add team counts to the topics in a single
        # bulk operation per page.
        topics_data = self._serialize_and_paginate(
            TopicsPagination,
            topics,
            request,
            BulkTeamCountTopicSerializer,
            {'course_id': course.id},
        )
        topics_data["sort_order"] = sort_order

        user = request.user

        user_teams = CourseTeam.objects.filter(membership__user=user)
        user_teams_data = self._serialize_and_paginate(
            MyTeamsPagination,
            user_teams,
            request,
            CourseTeamSerializer,
            {'expand': ('user',)}
        )

        context = {
            "course": course,
            "topics": topics_data,
            # It is necessary to pass both privileged and staff because only privileged users can
            # administer discussion threads, but both privileged and staff users are allowed to create
            # multiple teams (since they are not automatically added to teams upon creation).
            "user_info": {
                "username": user.username,
                "privileged": has_discussion_privileges(user, course_key),
                "staff": bool(has_access(user, 'staff', course_key)),
                "teams": user_teams_data
            },
            "topic_url": reverse(
                'topics_detail', kwargs={'topic_id': 'topic_id', 'course_id': str(course_id)}, request=request
            ),
            "topics_url": reverse('topics_list', request=request),
            "teams_url": reverse('teams_list', request=request),
            "teams_detail_url": reverse('teams_detail', args=['team_id']),
            "team_memberships_url": reverse('team_membership_list', request=request),
            "my_teams_url": reverse('teams_list', request=request),
            "team_membership_detail_url": reverse('team_membership_detail', args=['team_id', user.username]),
            "languages": [[lang[0], _(lang[1])] for lang in settings.ALL_LANGUAGES],  # pylint: disable=translation-of-non-string
            "countries": list(countries),
            "disable_courseware_js": True,
            "teams_base_url": reverse('teams_dashboard', request=request, kwargs={'course_id': course_id}),
        }
        return render_to_response("teams/teams.html", context)

    def _serialize_and_paginate(self, pagination_cls, queryset, request, serializer_cls, serializer_ctx):
        """
        Serialize and paginate objects in a queryset.

        Arguments:
            pagination_cls (pagination.Paginator class): Django Rest Framework Paginator subclass.
            queryset (QuerySet): Django queryset to serialize/paginate.
            serializer_cls (serializers.Serializer class): Django Rest Framework Serializer subclass.
            serializer_ctx (dict): Context dictionary to pass to the serializer

        Returns: dict

        """
        # Django Rest Framework v3 requires that we pass the request
        # into the serializer's context if the serialize contains
        # hyperlink fields.
        serializer_ctx["request"] = request

        # Instantiate the paginator and use it to paginate the queryset
        paginator = pagination_cls()
        page = paginator.paginate_queryset(queryset, request)

        # Serialize the page
        serializer = serializer_cls(page, context=serializer_ctx, many=True)

        # Use the paginator to construct the response data
        # This will use the pagination subclass for the view to add additional
        # fields to the response.
        # For example, if the input data is a list, the output data would
        # be a dictionary with keys "count", "next", "previous", and "results"
        # (where "results" is set to the value of the original list)
        return paginator.get_paginated_response(serializer.data).data


def has_team_api_access(user, course_key, access_username=None):
    """Returns True if the user has access to the Team API for the course
    given by `course_key`. The user must either be enrolled in the course,
    be course staff, be global staff, or have discussion privileges.

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
    if has_discussion_privileges(user, course_key):
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

            * text_search: Searches for full word matches on the name, description,
              country, and language fields. NOTES: Search is on full names for countries
              and languages, not the ISO codes. Text_search cannot be requested along with
              with order_by.

            * order_by: Cannot be called along with with text_search. Must be one of the following:

                * name: Orders results by case insensitive team name (default).

                * open_slots: Orders results by most open slots (for tie-breaking,
                  last_activity_at is used, with most recent first).

                * last_activity_at: Orders result by team activity, with most active first
                  (for tie-breaking, open_slots is used, with most open slots first).

            * username: Return teams whose membership contains the given user.

            * page_size: Number of results to return per page.

            * page: Page number to retrieve.

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

                * discussion_topic_id: The unique id of the comments service
                  discussion topic associated with this team.

                * name: The name of the team.

                * course_id: The identifier for the course this team belongs to.

                * topic_id: Optionally specifies which topic the team is associated
                  with.

                * date_created: Date and time when the team was created.

                * description: A description of the team.

                * country: Optionally specifies which country the team is
                  associated with.

                * language: Optionally specifies which language the team is
                  associated with.

                * last_activity_at: The date of the last activity of any team member
                  within the team.

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

            If the server is unable to connect to Elasticsearch, and
            the text_search parameter is supplied, a 503 error is returned.

        **Response Values for POST**

            Any logged in user who has verified their email address can create
            a team. The format mirrors that of a GET for an individual team,
            but does not include the id, date_created, or membership fields.
            id is automatically computed based on name.

            If the user is not logged in, a 401 error is returned.

            If the user is not enrolled in the course, is not course or
            global staff, or does not have discussion privileges a 403 error
            is returned.

            If the course_id is not valid or extra fields are included in the
            request, a 400 error is returned.

            If the specified course does not exist, a 404 error is returned.
    """

    # OAuth2Authentication must come first to return a 401 for unauthenticated users
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CourseTeamSerializer
    pagination_class = TeamAPIPagination

    def get(self, request):
        """GET /api/team/v0/teams/"""
        result_filter = {}

        if 'course_id' in request.query_params:
            course_id_string = request.query_params['course_id']
            try:
                course_key = CourseKey.from_string(course_id_string)
                # Ensure the course exists
                course_module = modulestore().get_course(course_key)
                if course_module is None:
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

        text_search = request.query_params.get('text_search', None)
        if text_search and request.query_params.get('order_by', None):
            return Response(
                build_api_error(ugettext_noop("text_search and order_by cannot be provided together")),
                status=status.HTTP_400_BAD_REQUEST
            )

        username = request.query_params.get('username', None)
        if username is not None:
            result_filter.update({'membership__user__username': username})
        topic_id = request.query_params.get('topic_id', None)
        if topic_id is not None:
            if topic_id not in [topic['id'] for topic in course_module.teams_configuration['topics']]:
                error = build_api_error(
                    ugettext_noop('The supplied topic id {topic_id} is not valid'),
                    topic_id=topic_id
                )
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            result_filter.update({'topic_id': topic_id})
        if text_search and CourseTeamIndexer.search_is_enabled():
            try:
                search_engine = CourseTeamIndexer.engine()
            except ElasticSearchConnectionError:
                return Response(
                    build_api_error(ugettext_noop('Error connecting to elasticsearch')),
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            result_filter.update({'course_id': course_id_string})

            search_results = search_engine.search(
                query_string=text_search,
                field_dictionary=result_filter,
                size=MAXIMUM_SEARCH_SIZE,
            )

            paginated_results = paginate_search_results(
                CourseTeam,
                search_results,
                self.paginator.get_page_size(request),
                self.get_page()
            )
            emit_team_event('edx.team.searched', course_key, {
                "number_of_results": search_results['total'],
                "search_text": text_search,
                "topic_id": topic_id,
            })

            page = self.paginate_queryset(paginated_results)
            serializer = self.get_serializer(page, many=True)
            order_by_input = None
        else:
            queryset = CourseTeam.objects.filter(**result_filter)
            order_by_input = request.query_params.get('order_by', 'name')
            if order_by_input == 'name':
                # MySQL does case-insensitive order_by.
                queryset = queryset.order_by('name')
            elif order_by_input == 'open_slots':
                queryset = queryset.order_by('team_size', '-last_activity_at')
            elif order_by_input == 'last_activity_at':
                queryset = queryset.order_by('-last_activity_at', 'team_size')
            else:
                return Response({
                    'developer_message': "unsupported order_by value {ordering}".format(ordering=order_by_input),
                    # Translators: 'ordering' is a string describing a way
                    # of ordering a list. For example, {ordering} may be
                    # 'name', indicating that the user wants to sort the
                    # list by lower case name.
                    'user_message': _(u"The ordering {ordering} is not supported").format(ordering=order_by_input),
                }, status=status.HTTP_400_BAD_REQUEST)

            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)

        response = self.get_paginated_response(serializer.data)
        if order_by_input is not None:
            response.data['sort_order'] = order_by_input
        return response

    def post(self, request):
        """POST /api/team/v0/teams/"""
        field_errors = {}
        course_key = None

        course_id = request.data.get('course_id')
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
            return Response({
                'field_errors': field_errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Course and global staff, as well as discussion "privileged" users, will not automatically
        # be added to a team when they create it. They are allowed to create multiple teams.
        team_administrator = (has_access(request.user, 'staff', course_key)
                              or has_discussion_privileges(request.user, course_key))
        if not team_administrator and CourseTeamMembership.user_in_team_for_course(request.user, course_key):
            error_message = build_api_error(
                ugettext_noop('You are already in a team in this course.'),
                course_id=course_id
            )
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        if course_key and not has_team_api_access(request.user, course_key):
            return Response(status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['course_id'] = course_key

        serializer = CourseTeamCreationSerializer(data=data)
        add_serializer_errors(serializer, data, field_errors)

        if field_errors:
            return Response({
                'field_errors': field_errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            team = serializer.save()
            emit_team_event('edx.team.created', course_key, {
                'team_id': team.team_id
            })
            if not team_administrator:
                # Add the creating user to the team.
                team.add_user(request.user)
                emit_team_event(
                    'edx.team.learner_added',
                    course_key,
                    {
                        'team_id': team.team_id,
                        'user_id': request.user.id,
                        'add_method': 'added_on_create'
                    }
                )

            data = CourseTeamSerializer(team, context={"request": request}).data
            return Response(data)

    def get_page(self):
        """ Returns page number specified in args, params, or defaults to 1. """
        # This code is taken from within the GenericAPIView#paginate_queryset method.
        # We need need access to the page outside of that method for our paginate_search_results method
        page_kwarg = self.kwargs.get(self.paginator.page_query_param)
        page_query_param = self.request.query_params.get(self.paginator.page_query_param)
        return page_kwarg or page_query_param or 1


class IsEnrolledOrIsStaff(permissions.BasePermission):
    """Permission that checks to see if the user is enrolled in the course or is staff."""

    def has_object_permission(self, request, view, obj):
        """Returns true if the user is enrolled or is staff."""
        return has_team_api_access(request.user, obj.course_id)


class IsStaffOrPrivilegedOrReadOnly(IsStaffOrReadOnly):
    """
    Permission that checks to see if the user is global staff, course
    staff, or has discussion privileges. If none of those conditions are
    met, only read access will be granted.
    """

    def has_object_permission(self, request, view, obj):
        return (
            has_discussion_privileges(request.user, obj.course_id) or
            super(IsStaffOrPrivilegedOrReadOnly, self).has_object_permission(request, view, obj)
        )


class TeamsDetailView(ExpandableFieldViewMixin, RetrievePatchAPIView):
    """
        **Use Cases**

            Get, update, or delete a course team's information. Updates are supported
            only through merge patch.

        **Example Requests**:

            GET /api/team/v0/teams/{team_id}}

            PATCH /api/team/v0/teams/{team_id} "application/merge-patch+json"

            DELETE /api/team/v0/teams/{team_id}

        **Query Parameters for GET**

            * expand: Comma separated list of types for which to return
              expanded representations. Supports "user" and "team".

        **Response Values for GET**

            If the user is logged in, the response contains the following fields:

                * id: The team's unique identifier.

                * discussion_topic_id: The unique id of the comments service
                  discussion topic associated with this team.

                * name: The name of the team.

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

                * last_activity_at: The date of the last activity of any team member
                  within the team.

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
            If the user is not course or global staff, does not have discussion
            privileges, and the team does exist, a 403 is returned.

            If "application/merge-patch+json" is not the specified content type,
            a 415 error is returned.

            If the update could not be completed due to validation errors, this
            method returns a 400 error with all error messages in the
            "field_errors" field of the returned JSON.

        **Response Values for DELETE**

            Only staff can delete teams. When a team is deleted, all
            team memberships associated with that team are also
            deleted. Returns 204 on successful deletion.

            If the user is anonymous or inactive, a 401 is returned.

            If the user is not course or global staff and does not
            have discussion privileges, a 403 is returned.

            If the user is logged in and the team does not exist, a 404 is returned.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsStaffOrPrivilegedOrReadOnly, IsEnrolledOrIsStaff,)
    lookup_field = 'team_id'
    serializer_class = CourseTeamSerializer
    parser_classes = (MergePatchParser,)

    def get_queryset(self):
        """Returns the queryset used to access the given team."""
        return CourseTeam.objects.all()

    def delete(self, request, team_id):
        """DELETE /api/team/v0/teams/{team_id}"""
        team = get_object_or_404(CourseTeam, team_id=team_id)
        self.check_object_permissions(request, team)
        # Note: list() forces the queryset to be evualuated before delete()
        memberships = list(CourseTeamMembership.get_memberships(team_id=team_id))

        # Note: also deletes all team memberships associated with this team
        team.delete()
        log.info('user %d deleted team %s', request.user.id, team_id)
        emit_team_event('edx.team.deleted', team.course_id, {
            'team_id': team_id,
        })
        for member in memberships:
            emit_team_event('edx.team.learner_removed', team.course_id, {
                'team_id': team_id,
                'remove_method': 'team_deleted',
                'user_id': member.user_id
            })
        return Response(status=status.HTTP_204_NO_CONTENT)


class TopicListView(GenericAPIView):
    """
        **Use Cases**

            Retrieve a list of topics associated with a single course.

        **Example Requests**

            GET /api/team/v0/topics/?course_id={course_id}

        **Query Parameters for GET**

            * course_id: Filters the result to topics belonging to the given
              course (required).

            * order_by: Orders the results. Currently only 'name' and 'team_count' are supported;
              the default value is 'name'. If 'team_count' is specified, topics are returned first sorted
              by number of teams per topic (descending), with a secondary sort of 'name'.

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
    pagination_class = TopicsPagination

    def get(self, request):
        """GET /api/team/v0/topics/?course_id={course_id}"""
        course_id_string = request.query_params.get('course_id', None)
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

        ordering = request.query_params.get('order_by', 'name')
        if ordering not in ['name', 'team_count']:
            return Response({
                'developer_message': "unsupported order_by value {ordering}".format(ordering=ordering),
                # Translators: 'ordering' is a string describing a way
                # of ordering a list. For example, {ordering} may be
                # 'name', indicating that the user wants to sort the
                # list by lower case name.
                'user_message': _(u"The ordering {ordering} is not supported").format(ordering=ordering),
            }, status=status.HTTP_400_BAD_REQUEST)

        # Always sort alphabetically, as it will be used as secondary sort
        # in the case of "team_count".
        topics = get_alphabetical_topics(course_module)
        if ordering == 'team_count':
            add_team_count(topics, course_id)
            topics.sort(key=lambda t: t['team_count'], reverse=True)
            page = self.paginate_queryset(topics)
            serializer = TopicSerializer(
                page,
                context={'course_id': course_id},
                many=True,
            )
        else:
            page = self.paginate_queryset(topics)
            # Use the serializer that adds team_count in a bulk operation per page.
            serializer = BulkTeamCountTopicSerializer(page, context={'course_id': course_id}, many=True)

        response = self.get_paginated_response(serializer.data)
        response.data['sort_order'] = ordering

        return response


def get_alphabetical_topics(course_module):
    """Return a list of team topics sorted alphabetically.

    Arguments:
        course_module (xmodule): the course which owns the team topics

    Returns:
        list: a list of sorted team topics
    """
    return sorted(course_module.teams_topics, key=lambda t: t['name'].lower())


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

        serializer = TopicSerializer(topics[0], context={'course_id': course_id})
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

            * course_id: Returns membership records only for the specified
              course. Username must have access to this course, or else team_id
              must be in this course.

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

                * last_activity_at: The date of the last activity of the user
                  within the team.

            For all text fields, clients rendering the values should take care
            to HTML escape them to avoid script injections, as the data is
            stored exactly as specified. The intention is that plain text is
            supported, not HTML.

            If the user is not logged in and active, a 401 error is returned.

            If neither team_id nor username are provided, a 400 error is
            returned.

            If team_id is provided but the team does not exist, a 404 error is
            returned.

            If the specified course_id is invalid, a 404 error is returned.

            This endpoint uses 404 error codes to avoid leaking information
            about team or user existence. Specifically, a 404 error will be
            returned if a logged in user specifies a team_id for a course
            they are not enrolled in.

            Additionally, when username is specified the list of returned
            memberships will be filtered to memberships in teams associated
            with courses that the requesting user is enrolled in.

            If the course specified by course_id does not contain the team
            specified by team_id, a 400 error is returned.

            If the user is not enrolled in the course specified by course_id,
            and does not have staff access to the course, a 400 error is
            returned.

        **Response Values for POST**

            Any logged in user enrolled in a course can enroll themselves in a
            team in the course. Course staff, global staff, and discussion
            privileged users can enroll any user in a team, with a few
            exceptions noted below.

            If the user is not logged in and active, a 401 error is returned.

            If username and team are not provided in the posted JSON, a 400
            error is returned describing the missing fields.

            If the specified team does not exist, a 404 error is returned.

            If the user is not staff, does not have discussion privileges,
            and is not enrolled in the course associated with the team they
            are trying to join, or if they are trying to add a user other
            than themselves to a team, a 404 error is returned. This is to
            prevent leaking information about the existence of teams and users.

            If the specified user does not exist, a 404 error is returned.

            If the user is already a member of a team in the course associated
            with the team they are trying to join, a 400 error is returned.
            This applies to both staff and students.

            If the user is not enrolled in the course associated with the team
            they are trying to join, a 400 error is returned. This can occur
            when a staff or discussion privileged user posts a request adding
            another user to a team.
    """

    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MembershipSerializer

    def get(self, request):
        """GET /api/team/v0/team_membership"""
        specified_username_or_team = False
        username = None
        team_id = None
        requested_course_id = None
        requested_course_key = None
        accessible_course_ids = None

        if 'course_id' in request.query_params:
            requested_course_id = request.query_params['course_id']
            try:
                requested_course_key = CourseKey.from_string(requested_course_id)
            except InvalidKeyError:
                return Response(status=status.HTTP_404_NOT_FOUND)

        if 'team_id' in request.query_params:
            specified_username_or_team = True
            team_id = request.query_params['team_id']
            try:
                team = CourseTeam.objects.get(team_id=team_id)
            except CourseTeam.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if requested_course_key is not None and requested_course_key != team.course_id:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if not has_team_api_access(request.user, team.course_id):
                return Response(status=status.HTTP_404_NOT_FOUND)

        if 'username' in request.query_params:
            specified_username_or_team = True
            username = request.query_params['username']
            if not request.user.is_staff:
                enrolled_courses = (
                    CourseEnrollment.enrollments_for_user(request.user).values_list('course_id', flat=True)
                )
                staff_courses = (
                    CourseAccessRole.objects.filter(user=request.user, role='staff').values_list('course_id', flat=True)
                )
                accessible_course_ids = [item for sublist in (enrolled_courses, staff_courses) for item in sublist]
                if requested_course_id is not None and requested_course_id not in accessible_course_ids:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        if not specified_username_or_team:
            return Response(
                build_api_error(ugettext_noop("username or team_id must be specified.")),
                status=status.HTTP_400_BAD_REQUEST
            )

        course_keys = None
        if requested_course_key is not None:
            course_keys = [requested_course_key]
        elif accessible_course_ids is not None:
            course_keys = [CourseKey.from_string(course_string) for course_string in accessible_course_ids]

        queryset = CourseTeamMembership.get_memberships(username, course_keys, team_id)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """POST /api/team/v0/team_membership"""
        field_errors = {}

        if 'username' not in request.data:
            field_errors['username'] = build_api_error(ugettext_noop("Username is required."))

        if 'team_id' not in request.data:
            field_errors['team_id'] = build_api_error(ugettext_noop("Team id is required."))

        if field_errors:
            return Response({
                'field_errors': field_errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            team = CourseTeam.objects.get(team_id=request.data['team_id'])
        except CourseTeam.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        username = request.data['username']
        if not has_team_api_access(request.user, team.course_id, access_username=username):
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        course_module = modulestore().get_course(team.course_id)
        if course_module.teams_max_size is not None and team.users.count() >= course_module.teams_max_size:
            return Response(
                build_api_error(ugettext_noop("This team is already full.")),
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership = team.add_user(user)
            emit_team_event(
                'edx.team.learner_added',
                team.course_id,
                {
                    'team_id': team.team_id,
                    'user_id': user.id,
                    'add_method': 'joined_from_team_view' if user == request.user else 'added_by_another_user'
                }
            )
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

            * last_activity_at: The date of the last activity of any team member
                within the team.

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
            a team in the course. Course staff, global staff, and discussion
            privileged users can remove any user from a team. Successfully
            deleting a membership will return a 204 response with no content.

            If the user is not logged in and active, a 401 error is returned.

            If the specified team or username does not exist, a 404 error is
            returned.

            If the user is not staff or a discussion privileged user and is
            attempting to remove another user from a team, a 404 error is
            returned. This prevents leaking information about team and user
            existence.

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
            removal_method = 'self_removal'
            if 'admin' in request.query_params:
                removal_method = 'removed_by_admin'
            membership.delete()
            emit_team_event(
                'edx.team.learner_removed',
                team.course_id,
                {
                    'team_id': team.team_id,
                    'user_id': membership.user.id,
                    'remove_method': removal_method
                }
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
