"""
CSV processing and generation utilities for Teams LMS app.
"""

import csv
from collections import Counter

from django.contrib.auth.models import User

from lms.djangoapps.teams.api import OrganizationProtectionStatus, user_organization_protection_status
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from student.models import CourseEnrollment
from .utils import emit_team_event


def load_team_membership_csv(course, response):
    """
    Load a CSV detailing course membership.

    Arguments:
        course (CourseDescriptor): Course module for which CSV
            download has been requested.
        response (HttpResponse): Django response object to which
            the CSV content will be written.
    """
    headers = _get_team_membership_csv_headers(course)
    writer = csv.DictWriter(response, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    team_membership_data = _lookup_team_membership_data(course)
    writer.writerows(team_membership_data)


def _get_team_membership_csv_headers(course):
    """
    Get headers for team membership csv.
    ['user', 'mode', <teamset_id_1>, ..., ,<teamset_id_n>]
    """
    headers = ['user', 'mode']
    for teamset in sorted(course.teams_configuration.teamsets, key=lambda ts: ts.teamset_id):
        headers.append(teamset.teamset_id)
    return headers


def _lookup_team_membership_data(course):
    """
    Returns a list of dicts, in the following form:
    [
        {
            'user': <username>,
            'mode': <student enrollment mode for the given course>,
            <teamset id>: <team name> for each teamset in which the given user is on a team
        }
        for student in course
    ]
    """
    course_students = CourseEnrollment.objects.users_enrolled_in(course.id).order_by('username')
    CourseEnrollment.bulk_fetch_enrollment_states(course_students, course.id)

    course_team_memberships = CourseTeamMembership.objects.filter(
        team__course_id=course.id
    ).select_related('team', 'user').all()
    teamset_memberships_by_user = _group_teamset_memberships_by_user(course_team_memberships)
    team_membership_data = []
    for user in course_students:
        student_row = teamset_memberships_by_user.get(user, dict())
        student_row['user'] = user.username
        student_row['mode'], _ = CourseEnrollment.enrollment_mode_for_user(user, course.id)
        team_membership_data.append(student_row)
    return team_membership_data


def _group_teamset_memberships_by_user(course_team_memberships):
    """
    Parameters:
        - course_team_memberships: a collection of CourseTeamMemberships.

    Returns:
        {
            <User>: {
                <teamset_id>: <team_name>
                for CourseTeamMembership in input corresponding to <User>
            }
            per user represented in input
        }
    """
    teamset_memberships_by_user = dict()
    for team_membership in course_team_memberships:
        user = team_membership.user
        if user not in teamset_memberships_by_user:
            teamset_memberships_by_user[user] = dict()
        topic_id = team_membership.team.topic_id
        team_name = team_membership.team.name
        teamset_memberships_by_user[user][topic_id] = team_name
    return teamset_memberships_by_user


class TeamMembershipImportManager(object):
    """
    A manager class that is responsible the import process of csv file including validation and creation of
    team_courseteam and teams_courseteammembership objects.
    """

    def __init__(self, course):
        self.validation_errors = []
        self.teamset_ids = []
        self.user_ids_by_teamset_id = {}
        self.course = course
        self.max_errors = 0
        self.existing_course_team_memberships = {}
        self.existing_course_teams = {}
        self.user_count_by_team = Counter()
        self.user_to_remove_by_team = Counter()
        self.number_of_learners_assigned = 0

    @property
    def import_succeeded(self):
        """
        Helper wrapper that tells us the status of the import
        """
        return not self.validation_errors

    def set_team_membership_from_csv(self, input_file):
        """
        Assigns team membership based on the content of an uploaded CSV file.
        Returns true if there were no issues.
        """
        reader = csv.DictReader((line.decode('utf-8-sig').strip() for line in input_file.readlines()))
        self.teamset_ids = reader.fieldnames[2:]
        row_dictionaries = []
        csv_usernames = set()
        if not self.validate_header(reader.fieldnames):
            return False
        if not self.validate_teamsets():
            return False
        self.load_user_ids_by_teamset_id()
        self.load_course_team_memberships()
        self.load_course_teams()
        # process student rows:
        for row in reader:
            if not self.validate_teams_have_matching_teamsets(row):
                return False
            username = row['user']
            if not username:
                continue
            if not self.is_username_unique(username, csv_usernames):
                return False
            csv_usernames.add(username)
            user = self.get_user(username)
            if user is None:
                continue
            if not self.validate_user_enrollment_is_valid(user, row['mode']):
                row['user'] = None
                continue
            row['user'] = user
            if not self.validate_user_assignment_to_team_and_teamset(row):
                return False
            self.remove_user_from_team_for_reassignment(row)
            row_dictionaries.append(row)

        if not self.validation_errors:
            for row in row_dictionaries:
                self.add_user_to_team(row)
            self.number_of_learners_assigned = len(row_dictionaries)
            return True
        else:
            return False

    def load_course_team_memberships(self):
        """
        Caches existing team memberships by (user_id, teamset_id)
        """
        for membership in CourseTeamMembership.get_memberships(course_ids=[self.course.id]):
            user_id = membership.user_id
            teamset_id = membership.team.topic_id
            self.existing_course_team_memberships[(user_id, teamset_id)] = membership.team

    def load_course_teams(self):
        """
        Caches existing course teams by (team_name, topic_id)
        """
        for team in CourseTeam.objects.filter(course_id=self.course.id):
            self.existing_course_teams[(team.name, team.topic_id)] = team

    def validate_header(self, header):
        """
        Validates header row to ensure that it contains at a minimum columns called 'user', 'mode'.
        Teamset validation is handled separately
        """
        if 'user' not in header:
            self.validation_errors.append("Header must contain column 'user'.")
            return False
        if 'mode' not in header:
            self.validation_errors.append("Header must contain column 'mode'.")
            return False
        return True

    def validate_teamsets(self):
        """
        Validates team set ids. Returns true if there are no errors.
        The following conditions result in errors:
        Teamset does not exist
        Teamset id is duplicated
        """
        valid_teamset_ids = {ts.teamset_id for ts in self.course.teams_configuration.teamsets}
        dupe_set = set()
        for teamset_id in self.teamset_ids:
            if teamset_id in dupe_set:
                self.validation_errors.append("Teamset with id " + teamset_id + " is duplicated.")
                return False
            dupe_set.add(teamset_id)
            if teamset_id not in valid_teamset_ids:
                self.validation_errors.append("Teamset with id " + teamset_id + " does not exist.")
                return False
        return True

    def load_user_ids_by_teamset_id(self):
        """
        Get users associations with each teamset in a course and
        save to `self.user_ids_by_teamset_id`
        """
        for teamset_id in self.teamset_ids:
            self.user_ids_by_teamset_id[teamset_id] = {
                membership.user_id for membership in
                CourseTeamMembership.objects.filter(
                    team__course_id=self.course.id, team__topic_id=teamset_id
                )
            }

    def validate_user_enrollment_is_valid(self, user, supplied_enrollment):
        """
        Invalid states:
            user not enrolled in course
            enrollment mode from csv doesn't match actual user enrollment
        """
        actual_enrollment_mode, user_enrolled = CourseEnrollment.enrollment_mode_for_user(user, self.course.id)
        if not user_enrolled:
            self.validation_errors.append('User ' + user.username + ' is not enrolled in this course.')
            return False
        if actual_enrollment_mode != supplied_enrollment.strip():
            self.validation_errors.append('User ' + user.username + ' enrollment mismatch.')
            return False

        return True

    def is_username_unique(self, username, usernames_found_so_far):
        """
        Ensures that username exists only once in an input file
        """
        if username in usernames_found_so_far:
            error_message = 'Username {} listed more than once in file.'.format(username)
            if self.add_error_and_check_if_max_exceeded(error_message):
                return False
        return True

    def validate_teams_have_matching_teamsets(self, row):
        """
        It's possible for a user to create a row that has more team names in it
        than there are teamset ids provided in the header.
        In that case, `row` will have one or more null keys mapping to team names, for example:
        {'teamset-1': 'team-a', 'teamset-2': 'team-beta', None: 'team-37'}

        This method will add a validation error and return False if this is the case.
        """
        if None in row:
            error_message = "Team(s) {0} don't have matching teamsets.".format(
                row[None]
            )
            if self.add_error_and_check_if_max_exceeded(error_message):
                return False
        return True

    def validate_user_assignment_to_team_and_teamset(self, row):
        """
        Validates a user entry relative to an existing team.
        row is a dictionary where key is column name and value is the row value
        [andrew],masters,team1,,team3
        [joe],masters,,team2,team3
        """
        user = row['user']
        for teamset_id in self.teamset_ids:
            team_name = row[teamset_id]
            if not team_name:
                # we will be removing a user from their current team in a given teamset
                # decrement the team membership, if it exists
                try:
                    current_team_name = self.existing_course_team_memberships[(user.id, teamset_id)].name
                    if (teamset_id, current_team_name) not in self.user_to_remove_by_team:
                        self.user_to_remove_by_team[(teamset_id, current_team_name)] = 1
                    else:
                        self.user_to_remove_by_team[(teamset_id, current_team_name)] += 1
                except KeyError:
                    # happens when a user is not on any team in a team set
                    pass
                continue
            try:
                # checks for a team inside a specific team set. This way team names can be duplicated across
                # teamsets
                team = self.existing_course_teams[(team_name, teamset_id)]
                if (teamset_id, team_name) not in self.user_count_by_team:
                    self.user_count_by_team[(teamset_id, team_name)] = team.users.count()
            except KeyError:
                pass

            if not self.validate_proposed_team_size_wont_exceed_maximum(team_name, teamset_id):
                return False
        return True

    def validate_proposed_team_size_wont_exceed_maximum(self, team_name, teamset_id):
        """
        Validates that the number of users we want to add to a team won't exceed maximum team size.
        """
        if self.course.teams_configuration.teamsets_by_id[teamset_id].max_team_size is None:
            max_team_size = self.course.teams_configuration.default_max_team_size
        else:
            max_team_size = self.course.teams_configuration.teamsets_by_id[teamset_id].max_team_size

        if max_team_size is not None:
            key = (teamset_id, team_name)
            if (self.user_count_by_team[key] - self.user_to_remove_by_team[key]) + 1 > max_team_size:
                self.add_error_and_check_if_max_exceeded('Team ' + team_name + ' is full.')
                return False
        self.user_count_by_team[(teamset_id, team_name)] += 1
        return True

    def remove_user_from_team_for_reassignment(self, row):
        """
        Remove a user from a team if:
        a. The user's current team is different from the team specified in csv for the same teamset (this user will
           then be assigned to a new team in 'add_user_to_team`.
        b. The team value in the CSV is blank - the user should be removed from the current team in teamset.
        Also, if there is no change in user's membership, the input row's team name will be nulled out so that no
        action will take place further in the processing chain.
        """
        for ts_id in self.teamset_ids:
            if row[ts_id] is None:
                # remove this student from the teamset
                try:
                    membership = CourseTeamMembership.objects.get(
                        user_id=row['user'].id,
                        team__topic_id=ts_id
                    )
                    membership.delete()
                except CourseTeamMembership.DoesNotExist:
                    pass
            else:
                # reassignment happens only if proposed team membership is different from existing team membership
                if (row['user'].id, ts_id) in self.existing_course_team_memberships:
                    current_user_teams_name = self.existing_course_team_memberships[row['user'].id, ts_id].name
                    if current_user_teams_name != row[ts_id]:
                        try:
                            membership = CourseTeamMembership.objects.get(
                                user_id=row['user'].id,
                                team__topic_id=ts_id
                            )
                            membership.delete()
                            del self.existing_course_team_memberships[row['user'].id, ts_id]
                            self.user_ids_by_teamset_id[ts_id].remove(row['user'].id)
                        except CourseTeamMembership.DoesNotExist:
                            pass
                    else:
                        # the user will remain in the same team. In order to avoid validation/attempting
                        # to readd the user, null out the team name
                        row[ts_id] = None

    def add_error_and_check_if_max_exceeded(self, error_message):
        """
        Adds an error to the error collection.
        :param error_message:
        :return: True if maximum error threshold is exceeded and processing must stop
                 False if maximum error threshold is NOT exceeded and processing can continue
        """
        self.validation_errors.append(error_message)
        return len(self.validation_errors) >= self.max_errors

    def add_user_to_team(self, user_row):
        """
        Creates a CourseTeamMembership entry - i.e: a relationship between a user and a team.
        user_row is a dictionary where key is column name and value is the row value.
        {'mode': ' masters','topic_0': '','topic_1': 'team 2','topic_2': None,'user': <user_obj>}
         andrew,masters,team1,,team3
        joe,masters,,team2,team3
        """
        user = user_row['user']
        for teamset_id in self.teamset_ids:
            team_name = user_row[teamset_id]
            if not team_name:
                continue
            if (team_name, teamset_id) not in self.existing_course_teams:
                protection_status = user_organization_protection_status(user, self.course.id)
                team = CourseTeam.create(
                    name=team_name,
                    course_id=self.course.id,
                    description='Import from csv',
                    topic_id=teamset_id,
                    organization_protected=protection_status == OrganizationProtectionStatus.protected
                )
                team.save()
                self.existing_course_teams[(team_name, teamset_id)] = team
            else:
                team = self.existing_course_teams[(team_name, teamset_id)]
            team.add_user(user)
            emit_team_event(
                'edx.team.learner_added',
                team.course_id,
                {
                    'team_id': team.team_id,
                    'user_id': user.id,
                    'add_method': 'team_csv_import'
                }
            )

    def get_user(self, user_name):
        """
        Gets the user object from user_name/email/locator
        user_name: the user_name/email/user locator
        """
        try:
            return User.objects.get(username=user_name)
        except User.DoesNotExist:
            try:
                return User.objects.get(email=user_name)
            except User.DoesNotExist:
                try:
                    user = ProgramEnrollment.objects.get(external_user_key=user_name).user
                    if user is None:
                        return None
                    return user
                except ProgramEnrollment.DoesNotExist:
                    self.validation_errors.append('User name/email/external key: ' + user_name + ' does not exist.')
                    return None
