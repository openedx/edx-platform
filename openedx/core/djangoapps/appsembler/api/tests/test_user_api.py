
from unittest import skip

from django.contrib.sites.models import Site
from django.core.urlresolvers import resolve, reverse
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from student.tests.factories import CourseEnrollmentFactory, UserFactory

import ddt
import mock

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

from openedx.core.djangoapps.appsembler.api.sites import (
    get_users_for_site,
)

from openedx.core.djangoapps.appsembler.api.v1.serializers import UserIndexSerializer

from openedx.core.djangoapps.appsembler.api.tests.factories import (
    CourseOverviewFactory,
    OrganizationFactory,
    UserOrganizationMappingFactory,
)

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@mock.patch(APPSEMBLER_API_VIEWS_MODULE + '.UserIndexViewSet.throttle_classes', [])
class UserIndexViewSetTest(TestCase):

    def setUp(self):
        """
        Set up test data for site isolation
        - two sites, our site and the other site
        - two orgs, one per site
        - set of learners in our site
        - one learner in the other site
        - one learner in both sites

        - caller user in our site with admin rights

        """
        super(UserIndexViewSetTest, self).setUp()
        self.my_site = Site.objects.get(domain=u'example.com')
        self.other_site = SiteFactory(domain='other-site.test')
        self.other_site_org = OrganizationFactory(sites=[self.other_site])
        self.my_site_org = OrganizationFactory(sites=[self.my_site])

        # Set up users and enrollments for 'my site'
        self.my_site_users = [UserFactory() for i in range(3)]
        for user in self.my_site_users:
            UserOrganizationMappingFactory(user=user,
                                           organization=self.my_site_org)

        self.other_site_users = [UserFactory()]
        for user in self.other_site_users:
            UserOrganizationMappingFactory(user=user,
                                           organization=self.other_site_org)

        self.caller = UserFactory()
        UserOrganizationMappingFactory(user=self.caller,
                                       organization=self.my_site_org,
                                       is_amc_admin=True)

    def test_serializer(self):
        user = self.my_site_users[0]
        data = UserIndexSerializer(instance=user).data
        assert data['username'] == user.username
        assert data['fullname'] == user.profile.name
        assert data['email'] == user.email

    def test_get_all_users_for_site(self):
        url = reverse('tahoe-api:v1:users-list')
        request = APIRequestFactory().get(url)
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)

        view = resolve(url).func
        response = view(request)
        response.render()
        results = response.data['results']

        response_count = len(results)
        expected_users = get_users_for_site(self.my_site)

        user_ids = [rec['id'] for rec in results]
        assert set(user_ids) == set([obj.id for obj in expected_users])

    @skip("Need to implement user filter")
    def test_get_all_enrolled_learners_for_site(self):

        # Set up enrollment data

        url = reverse('tahoe-api:v1:users-list')
        request = APIRequestFactory().get(url)
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)

        view = resolve(url).func
        response = view(request)
        response.render()
        results = response.data['results']

        response_count = len(results)
        user_ids = [rec['id'] for rec in results]
        assert set(user_ids) == set([obj.id for obj in self.my_site_users])
