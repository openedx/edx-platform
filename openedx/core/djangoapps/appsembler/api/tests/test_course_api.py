"""
Tests for openedx.core.djangoapps.appsembler.api.v1.views.CourseViewSet

These tests adapted from Appsembler enterprise `appsembler_api` tests

"""

# from django.contrib.sites.models import Site
from django.urls import resolve, reverse

from django.test import RequestFactory, TestCase
from django.test.utils import override_settings

from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory, force_authenticate

import ddt
import mock

from student.tests.factories import UserFactory
from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory,
    SiteFactory,
)


from openedx.core.djangoapps.appsembler.api.tests.factories import (
    CourseOverviewFactory,
    OrganizationFactory,
    OrganizationCourseFactory,
    UserOrganizationMappingFactory,
)


APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@mock.patch(APPSEMBLER_API_VIEWS_MODULE + '.CourseViewSet.throttle_classes', [])
class CourseApiTest(TestCase):

    def setUp(self):
        self.my_site = SiteFactory(domain='my-site.test')
        self.other_site = SiteFactory(domain='other-site.test')
        self.other_site_org = OrganizationFactory(linked_site=self.other_site)
        self.my_site_org = OrganizationFactory(linked_site=self.my_site)

        self.my_course_overviews = [
            CourseOverviewFactory(),
            CourseOverviewFactory()
        ]
        for co in self.my_course_overviews:
            OrganizationCourseFactory(organization=self.my_site_org,
                                      course_id=str(co.id))

        self.other_course_overviews = [CourseOverviewFactory()]
        OrganizationCourseFactory(organization=self.other_site_org,
                                  course_id=str(self.other_course_overviews[0].id))

        self.caller = UserFactory()
        UserOrganizationMappingFactory(user=self.caller,
                                       organization=self.my_site_org,
                                       is_amc_admin=True)

    def test_get_list(self):
        url = reverse('tahoe-api:v1:courses-list')
        request = APIRequestFactory().get(url)
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)
        view = resolve(url).func
        response = view(request)
        response.render()
        results = response.data['results']
        self.assertEqual(response.status_code, 200)
        expected_keys = [str(co.id) for co in self.my_course_overviews]
        self.assertEqual(set([obj['id'] for obj in results]), set(expected_keys))

    def test_get_single(self):
        course_id = str(self.my_course_overviews[0].id)
        url = reverse('tahoe-api:v1:courses-detail', args=[course_id])
        request = APIRequestFactory().get(url)
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)
        view = resolve(url)
        response = view.func(request, pk=course_id)
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], course_id)
