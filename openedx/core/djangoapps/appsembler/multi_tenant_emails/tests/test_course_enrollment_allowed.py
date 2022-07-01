"""
Test cases to cover CourseEnrollmentAllowed models (and its feature) with APPSEMBLER_MULTI_TENANT_EMAILS.
"""

import json
from mock import patch
from rest_framework import status
from unittest import skipIf
from xmodule.modulestore.tests.factories import CourseFactory

from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from tahoe_sites.tests.utils import create_organization_mapping

from .test_utils import with_organization_context, lms_multi_tenant_test
from openedx.core.djangoapps.appsembler.api.tests.factories import (
    CourseOverviewFactory,
    OrganizationCourseFactory,
)


@lms_multi_tenant_test
@patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': True})
class TestCourseEnrollmentAllowedMultitenant(ModuleStoreTestCase):
    """
    Unit tests for the CourseEnrollmentAllowed model and related features.
    """

    RED = 'red1'
    BLUE = 'blue2'

    OMAR_EMAIL = 'omar@example.org'
    JOHN_EMAIL = 'johnb@example.org'
    PASSWORD = 'test_password'

    def create_org_course(self, org):
        """
        Create course with organization link.
        """
        course = CourseFactory.create()
        overview = CourseOverviewFactory.create(id=course.id)
        OrganizationCourseFactory(organization=org, course_id=str(overview.id))
        return overview

    def invite(self, org, course_id, email):
        """
        Invite a user by email via the Tahoe Enrollment API endpoint.
        """
        client = self.client_class()
        caller = UserFactory.create(password=self.PASSWORD)
        create_organization_mapping(user=caller, organization=org, is_admin=True)
        client.login(username=caller.username, password=self.PASSWORD)
        url = reverse('tahoe-api:v1:enrollments-list')
        body = json.dumps({
            'action': 'enroll',
            'auto_enroll': True,
            'identifiers': [email],
            'email_learners': True,
            'courses': [str(course_id)],
        })
        response = client.post(url, data=body, content_type='application/json')
        content = response.content.decode('utf-8')
        assert 'error' not in content
        assert response.status_code == status.HTTP_201_CREATED, content
        return response

    def register_user(self, color, email, password):
        """
        Register a user via the registration form API endpoint.
        """
        url = reverse('user_api_registration')
        response = self.client.post(url, {
            'email': email,
            'name': 'Ali',
            'username': 'ali_{}'.format(color),
            'password': password,
            'honor_code': 'true',
        })
        content = response.content.decode('utf-8')
        assert response.status_code == status.HTTP_200_OK, content
        user = User.objects.get(email=email)
        return user

    def test_enrollment_allowed_happy_path(self):
        """
        Basic test for CourseEnrollmentAllowed regardless of APPSEMBLER_MULTI_TENANT_EMAILS.
        """
        with with_organization_context(site_color=self.RED) as org:
            course = self.create_org_course(org)
            assert not CourseEnrollmentAllowed.objects.count(), 'No enrollment allowed yet.'
            self.invite(org, course.id, self.JOHN_EMAIL)
            assert CourseEnrollmentAllowed.objects.get(email=self.JOHN_EMAIL), 'EnrollmentAllowed should be created.'
            john_b = self.register_user(org.name, email=self.JOHN_EMAIL, password=self.PASSWORD)

        assert list(CourseEnrollment.objects.all()), 'Should be enrolled'
        assert CourseEnrollment.is_enrolled(john_b, course.id), 'Should be enrolled'

    def test_enrollment_allowed_no_current_request(self):
        """
        Test CourseEnrollmentAllowed without `request` when the APPSEMBLER_MULTI_TENANT_EMAILS feature is enabled.
        """
        with with_organization_context(site_color=self.RED) as org:
            course = self.create_org_course(org)
            assert not CourseEnrollmentAllowed.objects.count(), 'No enrollment allowed yet.'
            self.invite(org, course.id, self.JOHN_EMAIL)
            john_b = self.register_user(org.name, email='another.email@exmple.com', password=self.PASSWORD)

        assert not CourseEnrollment.is_enrolled(john_b, course.id), 'Should not be enrolled yet'

        john_b.email = self.JOHN_EMAIL  # Change email
        john_b.save()  # Simulate a command-line save.

        assert list(CourseEnrollment.objects.all()), 'Should be enrolled'
        assert CourseEnrollment.is_enrolled(john_b, course.id), 'Should be enrolled'

    def test_enrollment_allowed_two_sites(self):
        """
        Test CourseEnrollmentAllowed when the APPSEMBLER_MULTI_TENANT_EMAILS feature is enabled.

        Story:
         - Both John and Omar are invited for Welcome Course in Red Org.
         - John registers in Red Org, therefore should be enrolled in Welcome Course.
         - Omar registers in Blue Org, therefore should _not_ be enrolled in Welcome Course.
        """
        with with_organization_context(site_color=self.RED) as red_org:
            # Both John and Omar are invited for Welcome Course in Red Org.
            welcome_course = self.create_org_course(red_org)
            self.invite(red_org, welcome_course.id, self.JOHN_EMAIL)
            self.invite(red_org, welcome_course.id, self.OMAR_EMAIL)

            # John registers in Red Org, therefore should be enrolled in Welcome Course.
            red_john = self.register_user(red_org.name, email=self.JOHN_EMAIL, password=self.PASSWORD)
            assert CourseEnrollment.is_enrolled(red_john, welcome_course.id), 'Should be enrolled'

        with with_organization_context(site_color=self.BLUE) as blue_org:
            # Omar registers in Blue Org, therefore should _not_ be enrolled in Welcome Course.
            blue_omar = self.register_user(blue_org.name, email=self.OMAR_EMAIL, password=self.PASSWORD)
            assert not CourseEnrollment.is_enrolled(blue_omar, welcome_course.id), 'Should _not_ be enrolled'
