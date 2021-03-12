
import unittest

from django.contrib.sites.models import Site
from django.urls import resolve, reverse
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from student.tests.factories import UserFactory

import ddt
import mock

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

from openedx.core.djangoapps.appsembler.api.sites import (
    get_users_for_site,
)

from openedx.core.djangoapps.appsembler.api.v1.serializers import UserIndexSerializer

from openedx.core.djangoapps.appsembler.api.tests.factories import (
    OrganizationFactory,
    UserOrganizationMappingFactory,
)

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@ddt.ddt
@mock.patch(APPSEMBLER_API_VIEWS_MODULE + '.UserIndexViewSet.throttle_classes', [])
class UserIndexViewSetTest(TestCase):

    # Fixtures to be used for filtering
    JANE_DUE_USERNAME = 'jane.due'
    JANE_DUE_EMAIL = '{username}@user.api.example.com'.format(username=JANE_DUE_USERNAME)
    NON_USER_EMAIL = 'not.for.a.user@user.api.example.com'

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
        self.my_site = Site.objects.get(domain='example.com')
        self.other_site = SiteFactory(domain='other-site.test')
        self.other_site_org = OrganizationFactory(sites=[self.other_site])
        self.my_site_org = OrganizationFactory(sites=[self.my_site])

        # Set up users and enrollments for 'my site'
        self.my_site_users = [
            UserFactory.create(email=self.JANE_DUE_EMAIL, username=self.JANE_DUE_USERNAME),
            UserFactory.create(),
            UserFactory.create(),
        ]

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

        expected_users = get_users_for_site(self.my_site)

        user_ids = [rec['id'] for rec in results]
        assert set(user_ids) == set([obj.id for obj in expected_users])

    @ddt.unpack
    @ddt.data(
        {'email': JANE_DUE_EMAIL.lower(),
         'expected_count': 1,
         'msg': 'Should find Jane (lower case) in the users'},
        {'email': JANE_DUE_EMAIL.upper(),
         'expected_count': 1,
         'msg': 'Should find Jane (upper case) in the users'},
        {'email': JANE_DUE_USERNAME,
         'expected_count': 0,
         'msg': 'Should not do partial matching'},
        {'email': NON_USER_EMAIL,
         'expected_count': 0,
         'msg': 'Should not match any user.'},
    )
    def test_filter_by_email(self, email, expected_count, msg):
        """
        Test the email filters matching.
        """
        url = reverse('tahoe-api:v1:users-list')
        request = APIRequestFactory().get(url, {'email_exact': email})
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)

        view = resolve(url).func
        response = view(request)
        response.render()
        results = response.data['results']

        assert len(results) == expected_count, msg
        if expected_count:
            # Ignore the email case
            assert results[0]['email'].lower() == email.lower(), msg

    @unittest.expectedFailure
    def test_get_all_enrolled_learners_for_site(self):
        """
        Need to implement enrollments filtering in the ViewSet
        """
        # Set up enrollment data

        url = reverse('tahoe-api:v1:users-list')
        request = APIRequestFactory().get(url)
        request.META['HTTP_HOST'] = self.my_site.domain
        force_authenticate(request, user=self.caller)

        view = resolve(url).func
        response = view(request)
        response.render()
        results = response.data['results']

        user_ids = [rec['id'] for rec in results]
        assert set(user_ids) == set([obj.id for obj in self.my_site_users])
