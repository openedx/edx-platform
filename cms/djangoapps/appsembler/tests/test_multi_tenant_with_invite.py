"""
Tests for APPSEMBLER_MULTI_TENANT_EMAILS in Studio for course team invite.
"""

from mock import patch
import json

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import LibraryFactory

from contentstore.views import course_team_handler
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from django.test.utils import override_settings
from student.roles import CourseInstructorRole, LibraryUserRole
from organizations.models import OrganizationCourse
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    with_organization_context,
    create_org_user,
)

from student.roles import CourseCreatorRole, CourseAccessRole


@patch.dict('django.conf.settings.FEATURES', {'APPSEMBLER_MULTI_TENANT_EMAILS': True})
@override_settings(DEFAULT_SITE_THEME='edx-theme-codebase')  # Needed override for Studio tests
class MultiTenantStudioCourseTeamTestCase(ModuleStoreTestCase):
    """
    Testing the Course Team management when the APPSEMBLER_MULTI_TENANT_EMAILS feature is enabled in Studio.
    """

    BLUE = 'blue1'
    RED = 'red2'
    EMAIL = 'customer@example.com'
    PASSWORD = 'xyz'
    ROLE = CourseInstructorRole.ROLE

    def setUp(self):
        super(MultiTenantStudioCourseTeamTestCase, self).setUp()
        with with_organization_context(site_color=self.BLUE) as blue_org:
            self.blue_customer = create_org_user(blue_org, email=self.EMAIL, password=self.PASSWORD)
        self.blue_course = CourseOverviewFactory.create()
        self.blue_course_key = self.blue_course.id
        self.blue_library = LibraryFactory.create()
        CourseInstructorRole(self.blue_course_key).add_users(self.blue_customer)
        CourseInstructorRole(self.blue_library.location.library_key).add_users(self.blue_customer)

        self.blue_learner_email = 'learner1@example.com'
        with with_organization_context(site_color=self.BLUE) as blue_org:
            self.blue_learner = create_org_user(blue_org, email=self.blue_learner_email)

        OrganizationCourse.objects.create(organization=blue_org, course_id=str(self.blue_course_key))

    def url(self, email, key):
        self.url = reverse('course_team_handler', kwargs={
            # URL to add team member to a course
            'course_key_string': str(key),
            'email': email,
        })

    def add_to_team(self, email, key):
        """
        Invite a user to the team of a course (or a library).
        """
        url = self.url(email, key)
        body = json.dumps({'role': self.ROLE})
        request = RequestFactory().post(url, content_type='application/json', data=body)
        request.user = self.blue_customer
        response = course_team_handler(request, course_key_string=str(key), email=email)
        return response

    def test_invite_course_staff_not_found(self):
        """
        Ensure the invite works regardless of the APPSEMBLER_MULTI_TENANT_EMAILS feature.
        """
        non_existent_email = 'non_existent_email@example.com'
        response = self.add_to_team(non_existent_email, self.blue_course.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.content

    def test_invite_course_staff(self):
        """
        Ensure the invite works regardless of the APPSEMBLER_MULTI_TENANT_EMAILS feature.
        """
        learner = self.blue_learner
        roles_before = CourseAccessRole.objects.filter(role=self.ROLE, course_id=self.blue_course_key, user=learner)
        assert not roles_before.exists(), 'Not added yet'
        response = self.add_to_team(self.blue_learner_email, self.blue_course.id)
        assert response.status_code == status.HTTP_204_NO_CONTENT, response.content
        roles_after = CourseAccessRole.objects.filter(role=self.ROLE, course_id=self.blue_course_key, user=learner)
        assert roles_after.exists(), 'Should be added'

    def test_invite_library_staff(self):
        """
        Ensure the invite works for library regardless of the APPSEMBLER_MULTI_TENANT_EMAILS feature.
        """
        learner = self.blue_learner
        library_key = self.blue_library.location.library_key
        roles_before = CourseAccessRole.objects.filter(role=self.ROLE, course_id=library_key, user=learner)
        assert not roles_before.exists(), 'should not be added yet to library team'
        response = self.add_to_team(self.blue_learner_email, library_key)

        assert response.status_code == status.HTTP_204_NO_CONTENT, response.content

        roles_after = CourseAccessRole.objects.filter(role=self.ROLE, course_id=library_key, user=learner)
        assert roles_after.exists(), 'Should be added to library team'

    def test_invite_course_staff_registered_twice(self):
        """
        Ensure the invite works for a learner with accounts on two sites.

        Ensure the invite works with the APPSEMBLER_MULTI_TENANT_EMAILS feature enabled.
        """
        with with_organization_context(site_color=self.RED) as org:
            # Register in Red site with the same email as the Blue site
            _red_learner = create_org_user(org, email=self.blue_learner_email)

        response = self.add_to_team(self.blue_learner_email, self.blue_course.id)
        assert response.status_code == status.HTTP_204_NO_CONTENT, response.content
        roles_after = CourseAccessRole.objects.filter(
            role=self.ROLE,
            course_id=self.blue_course_key,
            user=self.blue_learner,
        )
        assert roles_after.exists(), 'Should be added'

    def test_invite_user_from_other_site(self):
        """
        Ensure the invite _not work_ for learner with an account on another site.

        Ensure the invite works with the APPSEMBLER_MULTI_TENANT_EMAILS feature enabled.
        """
        red_learner_email = 'red_learner@example.com'
        with with_organization_context(site_color=self.RED) as org:
            # Register in Red site with the same email as the Blue site
            _red_learner = create_org_user(org, email=red_learner_email)

        response = self.add_to_team(red_learner_email, self.blue_course.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.content
