"""
Tests labster course license views
"""
import random
import string
import mock
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.test import Client
from rest_framework import status
from openedx.core.djangoapps.labster.tests.base import CCXCourseTestBase
from xmodule.modulestore.tests.factories import ItemFactory


def item_factory(store, valid=True):
    """
    Return simulation with specified parameters.
    """
    simulation_id = 'a0Kw000000{}'.format(
        ''.join(random.choice(string.ascii_uppercase + string.digits) for num in range(8))
    )
    url = 'https://example.com/simulation/{}/'.format(simulation_id)
    if not valid:
        url = '	{}	'.format(url)
    ItemFactory.create(
        category='lti',
        modulestore=store,
        display_name='LTI%s' % simulation_id,
        metadata={
            'lti_id': 'correct_lti_id',
            'launch_url': url
        }
    )
    return simulation_id


class TestSetLicense(CCXCourseTestBase):
    """
    Tests for set_license method.
    """

    def setUp(self):
        super(TestSetLicense, self).setUp()
        self.request_factory = RequestFactory()
        self.license = 'YildVfefwmrTwNPPeapcNrugbkyb34sFoKiolPtk'
        self.url = reverse("labster_license_handler", kwargs={'course_id': self.ccx_key})
        self.data = {'license': self.license, 'update': True}
        self.client = Client()
        self.client.login(username=self.user.username, password="test")

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_valid_simulation_ids(self, get_consumer_secret, get_licensed_simulations):
        """
        Test that the licence page is returned with no invalid simulations.
        """
        # create 5 lti xmodules with valid launch urls
        licenced_simulations = []
        for num in range(5):
            licenced_simulations.append(item_factory(self.store))
        get_consumer_secret.return_value = ('123', '__secret_key__')
        get_licensed_simulations.return_value = licenced_simulations
        res = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('value="YildVfefwmrTwNPPeapcNrugbkyb34sFoKiolPtk"', res.content)
        self.assertNotIn('Please verify LTI URLs  are correct for the following simulations', res.content)

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_invalid_simulation_ids(self, get_consumer_secret, get_licensed_simulations):
        """
        Test that license page is returned with error containing invalid simulations.
        """
        # create 5 lti xmodules with few invalid launch urls
        licenced_simulations = []
        is_valid = [True, True, False, True, False]
        for valid in is_valid:
            licenced_simulations.append(item_factory(self.store, valid))
        get_consumer_secret.return_value = ('123', '__secret_key__')
        get_licensed_simulations.return_value = licenced_simulations
        res = self.client.post(self.url, data=self.data, follow=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('value="YildVfefwmrTwNPPeapcNrugbkyb34sFoKiolPtk"', res.content)
        self.assertIn('Please verify LTI URLs  are correct for the following simulations', res.content)
        self.assertIn(licenced_simulations[2], res.content)
        self.assertIn(licenced_simulations[4], res.content)
