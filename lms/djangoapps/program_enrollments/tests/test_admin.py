"""
Unit tests for the ProgramEnrollment admin classes.
"""


from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from lms.djangoapps.program_enrollments.admin import ProgramCourseEnrollmentAdmin, ProgramEnrollmentAdmin
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment


class ProgramEnrollmentAdminTests(TestCase):
    """
    Unit tests for the ProgramEnrollments app.  This just gives us a little
    protection against exposing high-cardinality fields as drop-downs, exposing
    new fields, etc.
    """
    def setUp(self):
        super().setUp()
        self.program_admin = ProgramEnrollmentAdmin(ProgramEnrollment, AdminSite())
        self.program_course_admin = ProgramCourseEnrollmentAdmin(ProgramCourseEnrollment, AdminSite())

    def test_program_enrollment_admin(self):
        request = mock.Mock()
        expected_list_display = (
            'id', 'status', 'user', 'external_user_key', 'program_uuid', 'curriculum_uuid'
        )
        assert expected_list_display == self.program_admin.get_list_display(request)
        expected_raw_id_fields = ('user',)
        assert expected_raw_id_fields == self.program_admin.raw_id_fields

    def test_program_course_enrollment_admin(self):
        expected_raw_id_fields = ('program_enrollment', 'course_enrollment')
        assert expected_raw_id_fields == self.program_course_admin.raw_id_fields
