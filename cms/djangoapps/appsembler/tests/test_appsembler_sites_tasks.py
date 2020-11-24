"""
Tests for appsembler.sites.tasks.
"""
import datetime
import unittest

from django.conf import settings
from django.test import override_settings
from organizations.models import UserOrganizationMapping
from organizations.tests.factories import OrganizationFactory

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.appsembler.sites.tasks import import_course_on_site_creation_apply_async
from student.roles import CourseAccessRole
from student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


COURSE_NAME = 'TahoeWelcome'
IMPORT_SETTINGS = {
    'TAHOE_DEFAULT_COURSE_NAME': COURSE_NAME,

    # If these tests fail double check that the URL below is still working:
    #  - https://github.com/appsembler/first-course/archive/v0.0.1.tar.gz
    'TAHOE_DEFAULT_COURSE_GITHUB_ORG': 'appsembler',
    'TAHOE_DEFAULT_COURSE_GITHUB_NAME': 'first-course',
    'TAHOE_DEFAULT_COURSE_VERSION': 'v0.0.1',
}


@override_settings(**IMPORT_SETTINGS)
@unittest.skipIf(settings.TAHOE_TEMP_MONKEYPATCHING_JUNIPER_TESTS, 'fix stuck test')
class ImportCourseOnSiteCreationTestCase(ModuleStoreTestCase):
    """
    Integration tests for the `import_course_on_site_creation` task.
    """

    organization_name = 'blue'

    def setUp(self):
        super(ImportCourseOnSiteCreationTestCase, self).setUp()
        self.m_store = modulestore()
        self.user = UserFactory.create()
        self.organization = OrganizationFactory.create(short_name=self.organization_name)
        UserOrganizationMapping.objects.create(
            user=self.user,
            organization=self.organization,
            is_amc_admin=True,
        )

    def get_course_id(self, use_new_format=False):
        """
        Get the textual course ID in old `Org/Course/Run` format.

        :param use_new_format: Use the new `course-v1:Org+Course+Run` format.

        # TODO: (Juniper??) Fix this and ONLY use new course format once Open edX test modulestore fix it
        """
        this_year = datetime.datetime.now().year
        if use_new_format:
            id_format = 'course-v1:{}+{}+{}'
        else:
            id_format = '{}/{}/{}'
        return id_format.format(
            self.organization_name,
            COURSE_NAME,
            this_year,
        )

    @property
    def course_key(self):
        """
        Get CourseKey object using the old `Org/Course/Run` format.

        :return: CourseKey.
        """
        return CourseKey.from_string(self.get_course_id())

    def test_course_do_not_exist(self):
        """
        Sanity check to ensure course don't exist before importing.
        """
        assert not self.m_store.get_course(self.course_key), 'The course is not created yet!'
        assert not self.m_store.get_courses(), 'An empty module store on every test.'
        assert not CourseAccessRole.objects.count(), 'No course staff roles yet.'

    def test_import_course_on_site_creation(self):
        """
        Ensure the task run properly.
        """
        result = import_course_on_site_creation_apply_async(self.organization)
        assert not result.failed(), 'Task should succeed instead of returning: "{}"'.format(result.result)

        courses = self.m_store.get_courses()
        assert len(courses) == 1, 'Should import just one course'
        assert self.m_store.get_course(self.course_key), (
            'Should use the correct ID "{}"'.format(str(courses[0].id))
        )

        access_role = CourseAccessRole.objects.get(
            user=self.user,
        )

        assert access_role.role == 'instructor', 'Set the permission to instructor (aka Course Admin).'
        assert access_role.org == self.organization_name, 'Correct org is used'  # TODO: Not sure if that's needed
        assert str(access_role.course_id) == self.get_course_id(use_new_format=True)
