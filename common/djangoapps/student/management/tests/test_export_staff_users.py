"""
Unit tests for export_staff_users management command.
"""
from datetime import timedelta

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from common.djangoapps.student.tests.factories import CourseAccessRoleFactory, UserFactory


class TestExportStaffUsers(TestCase):
    """
    Tests the `export_staff_users` command.
    """

    @staticmethod
    def create_users_data():
        staff_user = UserFactory(last_login=now() - timedelta(days=5))
        instructor_user = UserFactory(last_login=now() - timedelta(days=5))
        course = CourseOverviewFactory(end=now() + timedelta(days=30))
        archived_course = CourseOverviewFactory(end=now() - timedelta(days=30))
        course_ids = [course.id, archived_course.id]
        for course_id in course_ids:
            CourseAccessRoleFactory.create(course_id=course_id, user=staff_user, role="staff")
            CourseAccessRoleFactory.create(course_id=course_id, user=instructor_user, role="instructor")

    def test_export_staff_users(self):
        self.create_users_data()
        self.assertEqual(len(mail.outbox), 0)
        call_command('export_staff_users', days=7)
        self.assertEqual(len(mail.outbox), 1)
