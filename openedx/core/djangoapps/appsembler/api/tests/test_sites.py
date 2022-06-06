"""

TODO: Make this module tests more robust

1. Implement multiple sites in addition to the 'my_site' and default 'example.com'
   site
2. Add checks that objects we create in our sites don't show up in the other site.
   This may be a bit "belt and suspenders", but given the importance, is worthwhile

"""
import ddt
import mock
import pytest

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from organizations.models import Organization

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory,
    SiteFactory,
)

from student.tests.factories import UserFactory

from openedx.core.djangoapps.appsembler.api import sites as aapi_sites
from openedx.core.djangoapps.appsembler.api.helpers import as_course_key

from openedx.core.djangoapps.appsembler.api.tests.factories import (
    CourseOverviewFactory,
    OrganizationFactory,
    OrganizationCourseFactory,
    UserOrganizationMappingFactory,
)


def create_org_users(org, new_user_count):
    return [UserOrganizationMappingFactory(
        organization=org).user for i in range(new_user_count)]


@ddt.ddt
class SitesModuleTests(TestCase):
    def setUp(self):
        """
        The default site already created is u'example.com'
        """
        self.other_site = Site.objects.get(domain='example.com')
        self.my_site = SiteFactory(domain='foo.test')
        self.other_site_org = OrganizationFactory(linked_site=self.other_site)
        self.my_site_org = OrganizationFactory(linked_site=self.my_site)
        self.my_course_overviews = [
            CourseOverviewFactory(),
            CourseOverviewFactory()
        ]
        OrganizationCourseFactory(organization=self.my_site_org,
                                  course_id=str(self.my_course_overviews[0].id))
        OrganizationCourseFactory(organization=self.my_site_org,
                                  course_id=str(self.my_course_overviews[1].id))

        self.other_course_overviews = [CourseOverviewFactory()]
        OrganizationCourseFactory(organization=self.other_site_org,
                                  course_id=str(self.other_course_overviews[0].id))

    def test_get_course_keys_for_site(self):
        course_keys = aapi_sites.get_course_keys_for_site(self.my_site)
        expected_ids = [str(co.id) for co in self.my_course_overviews]
        self.assertEqual(set([str(key) for key in course_keys]), set(expected_ids))

    @ddt.data(Organization.DoesNotExist, Organization.MultipleObjectsReturned)
    def test_get_course_keys_for_site_with_handled_exception(self, side_effect):
        with mock.patch(
            'openedx.core.djangoapps.appsembler.api.sites.get_organization_by_site',
            side_effect=side_effect
        ):
            self.assertEqual(aapi_sites.get_course_keys_for_site(mock.Mock()), [])

    def test_get_courses_for_site(self):
        courses = aapi_sites.get_courses_for_site(self.my_site)
        expected_ids = [str(co.id) for co in self.my_course_overviews]
        self.assertEqual(set([str(course.id) for course in courses]), set(expected_ids))

    def test_get_site_for_course(self):
        course_id = self.my_course_overviews[0].id
        site = aapi_sites.get_site_for_course(course_id)
        self.assertEqual(site, self.my_site)

    def get_enrollments_for_site(self):
        course_keys = aapi_sites.get_course_keys_for_site(self.site)
        return CourseEnrollment.objects.filter(course_id__in=course_keys)

    def test_my_course_belongs_to_my_site(self):
        for co in self.my_course_overviews:
            assert aapi_sites.course_belongs_to_site(site=self.my_site,
                                                     course_id=co.id)

    def test_my_course_not_belongs_to_other_site(self):
        for co in self.my_course_overviews:
            assert not aapi_sites.course_belongs_to_site(site=self.other_site,
                                                         course_id=co.id)

    def test_other_course_not_belongs_to_my_site(self):
        for co in self.other_course_overviews:
            assert not aapi_sites.course_belongs_to_site(site=self.my_site,
                                                         course_id=co.id)

    def test_invalid_course_not_belongs_to_site(self):
        for site in Site.objects.all():
            for course_id in [None, '', 'globber-fruzzle']:
                assert not aapi_sites.course_belongs_to_site(site=site,
                                                             course_id=course_id)

    def test_course_not_belongs_to_invalid_site(self):
        for site in [None, '', self.my_site_org]:
            with self.assertRaises(ValueError):
                aapi_sites.course_belongs_to_site(site=site,
                                                  course_id=self.my_course_overviews[0])

    def test_get_users_for_site(self):
        my_users = create_org_users(org=self.my_site_org, new_user_count=3)
        other_users = create_org_users(org=self.other_site_org, new_user_count=2)
        retrieved_users = aapi_sites.get_users_for_site(self.my_site)
        assert set(retrieved_users) == set(my_users)
        assert set(retrieved_users).isdisjoint(set(other_users))

    def test_get_users_for_site_with_handled_exceptions(self):
        with mock.patch(
            'openedx.core.djangoapps.appsembler.api.sites.get_organization_by_site',
            mock.Mock(side_effect=Organization.DoesNotExist)
        ):
            result = aapi_sites.get_users_for_site(mock.Mock())
            assert isinstance(result, QuerySet)
            assert result.count() == 0
