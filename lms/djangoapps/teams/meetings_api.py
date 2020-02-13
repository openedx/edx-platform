"""
A module to do all of the interactions with Chime, like:
- get/list meetings under our account.
- create new meetings
- list attendees
- create attendees

Any of the creation actions above should result in
an associated creation of either CourseTeamMeetings
or CourseTeamMeetingAttendees.
"""
import boto3
from django.conf import settings

from lms.djangoapps.teams.models import CourseTeam, CourseTeamMeeting


def _chime_client():
    return boto3.client(
        'chime',
        aws_access_key_id=settings.CHIME_AWS_ACCESS_KEY,
        aws_secret_access_key=settings.CHIME_AWS_SECRET_ACCESS_KEY,
    )


def get_account_id(course_id=None):
    if course_id:
        pass
    else:
        return DEFAULT_CHIME_ACCOUNT_ID


def get_chime_meeting(meeting_id):
    try:
        return _chime_client().get_meeting(MeetingId=str(meeting_id))
    except:
        return


def current_meeting_for_team(team):
    course_team_meeting = CourseTeamMeeting.latest_for_team(team)
    chime_meeting = get_chime_meeting(course_team_meeting.meeting_id)
    if chime_meeting:
        return course_team_meeting
    # return null if there's no meeting in progress for the team
    return None


def new_meeting_for_team(team):
    chime_meeting = _chime_client().create_meeting()
    meeting_id = chime_meeting['Meeting']['MeetingId']
    course_team_meeting = CourseTeamMeeting.objects.create(
        team=team,
        meeting_id=meeting_id,
    )
    return course_team_meeting


def chime_attendees_for_meeting(meeting_id):
    return _chime_client().list_attendees(MeetingId=str(meeting_id))


def attendees_for_meeting(course_team_meeting):
    attendees = chime_attendees_for_meeting(course_team_meeting.meeting_id)
    users_by_username = {
        user.username: user
        for user in course_team_meeting.team.users.all()
    }
    return [
        users_by_username[attendee['ExternalUserId']]
        for attendee in attendees['Attendees']
        if attendee['ExternalUserId'] in users_by_username
    ]


def create_attendees_for_meeting(course_team_meeting, users=None):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/chime.html?highlight=chime#Chime.Client.batch_create_attendee
    """
    if not users:
        users = course_team_meeting.team.users.all()

    kwargs = {
        'MeetingId': str(course_team_meeting.meeting_id),
        'Attendees': [
            {'ExternalUserId': user.username}
            for user in users
        ],
    }

    response = _chime_client().batch_create_attendee(**kwargs)
    # TODO: handle errors, a list keyed by 'Errors' in response
    attendees_by_username = {
        attendee['ExternalUserId']: attendee
        for attendee in response['Attendees']
    }
    return attendees_by_username


"""
from lms.djangoapps.teams.meetings_api import *
from lms.djangoapps.teams.models import *
team = CourseTeam.objects.get(id=1)
current_meeting = current_meeting_for_team(team)
meeting = new_meeting_for_team(team)
current_attendees = attendees_for_meeting(current_meeting)
new_attendees = create_attendees_for_meeting(current_meeting)
"""
