"""
Management command to update is_prerequisite_courses_passed flag in ApplicationHub
"""
import logging
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from openedx.adg.lms.applications.helpers import (
    bulk_update_application_hub_flag,
    get_users_with_active_enrollments_from_course_groups,
    has_user_passed_given_courses
)
from openedx.adg.lms.applications.models import MultilingualCourseGroup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Updates is_prerequisite_courses_passed flag in ApplicationHub.
    """

    def handle(self, *args, **kwargs):  # pylint: disable=unused-argument
        prereq_course_groups = MultilingualCourseGroup.objects.program_prereq_course_groups()

        if not prereq_course_groups:
            sys.exit('Exiting!!! No open pre-req courses found but there must be some pre-reqs. Please add from admin')

        user_ids_with_program_pre_reqs_not_passed = self.get_user_ids_with_program_pre_reqs_not_marked_as_passed()
        users_to_be_checked_for_update = get_users_with_active_enrollments_from_course_groups(
            user_ids_with_program_pre_reqs_not_passed, prereq_course_groups
        )

        if not users_to_be_checked_for_update:
            logger.info('No new user has passed pre-req courses')
            sys.exit(0)

        eligible_users = self.get_users_eligible_for_update(users_to_be_checked_for_update)
        bulk_update_application_hub_flag('is_prerequisite_courses_passed', eligible_users)

    def get_user_ids_with_program_pre_reqs_not_marked_as_passed(self):
        """
        Get ids of users who have completed their written application but not passed the program prereq courses

        Returns:
            A querySet of user ids whose program pre req courses are not yet marked as passed
        """
        return User.objects.filter(
            application_hub__is_written_application_completed=True,
            application_hub__is_prerequisite_courses_passed=False
        ).values_list('id', flat=True)

    def get_users_eligible_for_update(self, users_to_be_checked_for_update):
        """
        Returns the list of users that have passed the program prerequisite courses

        Args:
            users_to_be_checked_for_update(list): list of users

        Returns:
            eligible_users(list): filtered users that are eligible for update
        """
        eligible_users = []

        for user in users_to_be_checked_for_update:
            courses = MultilingualCourseGroup.objects.get_user_program_prereq_courses(user)
            if has_user_passed_given_courses(user, courses):
                eligible_users.append(user)

        return eligible_users
