from django.http import Http404
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django_countries import countries
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from w3lib.url import add_or_replace_parameter

from django_comment_client.utils import has_discussion_privileges
from courseware.courses import has_access
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from lms.djangoapps.teams import is_feature_enabled
from nodebb.models import TeamGroupChat
from student.models import CourseEnrollment, CourseAccessRole
from lms.djangoapps.teams.serializers import (
    BulkTeamCountTopicSerializer,
)
from lms.djangoapps.teams.views import get_alphabetical_topics

from .helpers import serialize, validate_team_topic, make_embed_url, get_user_recommended_team, \
    get_user_course_with_access
from .serializers import CustomCourseTeamSerializer


@login_required
def browse_teams(request, course_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    if not is_feature_enabled(course):
        raise Http404

    if not CourseEnrollment.is_enrolled(user, course.id) and \
            not has_access(user, 'staff', course, course.id):
        raise Http404

    # Even though sorting is done outside of the serializer, sort_order needs to be passed
    # to the serializer so that the paginated results indicate how they were sorted.
    topics = get_alphabetical_topics(course)

    topics_data = serialize(
        topics,
        request,
        BulkTeamCountTopicSerializer,
        {'course_id': course.id},
    )

    recommended_teams = serialize(
        get_user_recommended_team(course.id, user),
        request,
        CustomCourseTeamSerializer,
        {'expand': ('user',)}
    )

    context = {
        'course': course,
        'topics': topics_data,
        'recommended_teams': recommended_teams,
        'user_country': user.profile.country.name.format()
    }

    return render_to_response("teams/browse_teams.html", context)


@login_required
def browse_topic_teams(request, course_id, topic_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    topics = [t for t in course.teams_topics if t['id'] == topic_id]

    if len(topics) == 0:
        raise Http404

    topic_teams = CourseTeam.objects.filter(course_id=course.id, topic_id=topics[0]['id']).all()

    teams = serialize(
        topic_teams,
        request,
        CustomCourseTeamSerializer,
        {'expand': ('user',)}
    )

    is_member_of_any_team = CourseTeamMembership.user_in_team_for_course(user, course.id)

    context = {
        'course': course,
        'user_country': user.profile.country.name.format(),
        'topic': topics[0],
        'teams': teams,
        'show_create_card': not is_member_of_any_team
    }

    return render_to_response("teams/browse_topic_teams.html", context)


@login_required
def create_team(request, course_id, topic_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    is_topic_valid = validate_team_topic(course, topic_id)
    if not is_topic_valid:
        raise Http404

    is_member_of_any_team = CourseTeamMembership.user_in_team_for_course(user, course.id)

    context = {
        'course': course,
        'user_has_privilege': not is_member_of_any_team,
        'countries': list(countries),
        'languages': [[lang[0], _(lang[1])] for lang in settings.ALL_LANGUAGES],
        'topic_id': topic_id,
        'template_view': 'create'
    }

    return render_to_response("teams/create_update_team.html", context)


@login_required
def my_team(request, course_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    try:
        team = CourseTeam.objects.get(course_id=course.id, users=user)
        topic_url = request.GET.get('topic_url', None)
        url = reverse('view_team', args=[course_id, team.team_id])

        if topic_url:
            url = add_or_replace_parameter(url, 'topic_url', topic_url)

        return redirect(url)

    except CourseTeam.DoesNotExist:
        pass

    return render_to_response("teams/my_team.html", {'course': course})


@login_required
def view_team(request, course_id, team_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    try:
        team = CourseTeam.objects.get(team_id=team_id)
    except CourseTeam.DoesNotExist:
        raise Http404

    team_group_chat = TeamGroupChat.objects.filter(team=team).first()

    if not team_group_chat:
        raise Http404

    topic_url = request.GET.get('topic_url', None)
    embed_url = make_embed_url(team_group_chat, user, topic_url)
    leave_team_url = reverse('team_membership_detail', args=[team_id, user.username])

    team_administrator = (has_access(user, 'staff', course.id)
                          or has_discussion_privileges(user, course.id))

    is_member_of_any_team = CourseTeamMembership.user_in_team_for_course(user, course.id)

    is_user_member_of_this_team = bool(CourseTeamMembership.objects.filter(team=team, user=user).first())

    context = {
        'course': course,
        'user_has_team': is_member_of_any_team,
        'is_team_full': course.teams_max_size <= len(team.users.all()),
        'is_user_member_of_this_team': is_user_member_of_this_team,
        'room_url': embed_url,
        'join_team_url': reverse('team_membership_list'),
        'team': team,
        'team_administrator': team_administrator,
        'leave_team_url': leave_team_url,
        'country': str(countries.countries[team.country]),
        'language': dict(settings.ALL_LANGUAGES)[team.language],
    }

    return render_to_response("teams/view_team.html", context)


@login_required
def update_team(request, course_id, team_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    team_administrator = (has_access(user, 'staff', course.id)
                          or has_discussion_privileges(user, course.id))
    if not team_administrator:
        raise Http404

    try:
        team = CourseTeam.objects.get(team_id=team_id)
    except CourseTeam.DoesNotExist:
        raise Http404

    context = {
        'course': course,
        'team': team,
        'countries': list(countries),
        'languages': [[lang[0], _(lang[1])] for lang in settings.ALL_LANGUAGES],
        'user_has_privilege': team_administrator,
        'template_view': 'update'
    }

    return render_to_response("teams/create_update_team.html", context)


@login_required
def edit_team_memberships(request, course_id, team_id):
    user = request.user
    course = get_user_course_with_access(course_id, user)

    team_administrator = (has_access(user, 'staff', course.id)
                          or has_discussion_privileges(user, course.id))
    if not team_administrator:
        raise Http404

    try:
        team = CourseTeam.objects.get(team_id=team_id)
    except CourseTeam.DoesNotExist:
        raise Http404

    team_data = serialize(
        team,
        request,
        CustomCourseTeamSerializer,
        {'expand': ('user',)},
        many=False
    )

    context = {
        'course': course,
        'members': team_data['membership'],
        'team_id': team_id
    }

    return render_to_response("teams/edit_memberships.html", context)
