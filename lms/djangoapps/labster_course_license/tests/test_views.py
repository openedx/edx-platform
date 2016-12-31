"""
Tests labster course license views.
./manage.py lms test --verbosity=1 lms/djangoapps/labster_course_license   --traceback --settings=labster_test
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


class TestSetLicense(CCXCourseTestBase):
    """
    Tests for set_license method.
    """

    def setUp(self):
        super(TestSetLicense, self).setUp()
        self.url = reverse("labster_license_handler", kwargs={'course_id': self.ccx_key})
        self.data = {'license': 'YildVfefwmrTwNPPeapcNrugbkyb34sFoKiolPtk', 'update': True}
        self.client.login(username=self.user.username, password="test")

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_valid_simulation_ids(self, mock_get_consumer_secret, mock_get_licensed_simulations):
        """
        Test that the licence page is returned with no invalid simulations.
        """
        mock_get_consumer_secret.return_value = ('123', '__secret_key__')
        mock_get_licensed_simulations.return_value = ['*']
        # create 3 lti xmodules with valid launch urls
        data = [
            ('https://example.com/simulation/a0Kw0000000/', 'LTI0'),
            ('https://example.com/simulation/a0Kw0000001/', 'LTI1'),
            ('https://example.com/simulation/a0Kw00000002', 'LTI2'),
        ]
        licenced_simulations = [ItemFactory.create(
            category='lti', modulestore=self.store, display_name=display_name,
            metadata={'lti_id': 'correct_lti_id', 'launch_url': url}
        ) for url, display_name in data]

        res = self.client.post(self.url, data=self.data, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn('Please verify LTI URLs are correct for the following simulations', res.content)

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_hides_unlicensed_simulations(self, mock_get_consumer_secret, mock_get_licensed_simulations):
        """
        Ensure hides only unlicensed simulations.
        """
        mock_get_consumer_secret.return_value = ('123', '__secret_key__')
        mock_get_licensed_simulations.return_value = ['a0Kw0000000']

        data = [
            ('https://example.com/simulation/a0Kw0000000/', 'LTI0'),
            ('https://example.com/dashboards/teacher/', 'LTI1'),
            ('http://127.0.0.1/some/path/here/', 'LTI2'),
            ('https://example.com/simulation/a0Kw0000055', 'LTI3'),
            ('https://example.com/simulation/a0Kw0000035', 'LTI4'),
        ]

        chapter = ItemFactory.create(parent=self.course, category='chapter')
        sequential = ItemFactory.create(parent=chapter, category='sequential')
        verticals = [ItemFactory.create(parent=sequential, category='vertical') for i in range(len(data))]

        blocks = [ItemFactory.create(
            parent=verticals[index],
            category='lti', modulestore=self.store, display_name=item[1],
            metadata={'lti_id': 'correct_lti_id', 'launch_url': item[0]}
        ) for index, item in enumerate(data)]

        self.inject_field_overrides()
        res = self.client.post(self.url, data=self.data, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        chapter = self.ccx.course.get_children()[0]
        self.assertFalse(chapter.visible_to_staff_only)
        sequential = chapter.get_children()[0]
        self.assertFalse(sequential.visible_to_staff_only)
        verticals = sequential.get_children()
        self.assertEqual([False, False, False, True, True], [i.visible_to_staff_only for i in verticals])

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_can_hide_all_blocks(self, mock_get_consumer_secret, mock_get_licensed_simulations):
        """
        Test can hide all the blocks if there are no licensed simulations.
        """
        mock_get_consumer_secret.return_value = ('123', '__secret_key__')
        mock_get_licensed_simulations.return_value = []

        data = [
            ('https://example.com/simulation/a0Kw0000000/', 'LTI0'),
            ('https://example.com/dashboards/teacher/', 'LTI1'),
            ('http://127.0.0.1/some/path/here/', 'LTI2'),
            ('https://example.com/simulation/a0Kw0000055', 'LTI3'),
        ]

        chapter = ItemFactory.create(parent=self.course, category='chapter')
        sequential = ItemFactory.create(parent=chapter, category='sequential')
        verticals = [ItemFactory.create(parent=sequential, category='vertical') for i in range(len(data))]

        blocks = [ItemFactory.create(
            parent=verticals[index],
            category='lti', modulestore=self.store, display_name=item[1],
            metadata={'lti_id': 'correct_lti_id', 'launch_url': item[0]}
        ) for index, item in enumerate(data)]

        self.inject_field_overrides()
        res = self.client.post(self.url, data=self.data, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        chapter = self.ccx.course.get_children()[0]
        self.assertTrue(chapter.visible_to_staff_only)

    @mock.patch('labster_course_license.views.get_licensed_simulations')
    @mock.patch('labster_course_license.views.get_consumer_secret')
    def test_invalid_simulation_ids(self, mock_get_consumer_secret, mock_get_licensed_simulations):
        """
        Test that license page is returned with error containing invalid simulations.
        """
        mock_get_consumer_secret.return_value = ('123', '__secret_key__')
        mock_get_licensed_simulations.return_value = ["*"]

        data = [
            ('https://example.com/simulation/a0Kw0000000 /', 'LTI0', 'a0Kw0000000 '),
            ('https://example.com/simulation/a0Kw0000001 ', 'LTI1', 'a0Kw0000001 '),
            ('https://example.com/simulation/ a0Kw0000002/', 'LTI2', ' a0Kw0000002'),
            ('https://example.com/simulation/   a0Kw00000003  /', 'LTI3', '   a0Kw00000003  '),
            ('https://example.com/simulation/a0Kw0000 004/', 'LTI4', 'a0Kw0000 004'),
            ('/simulation/a0Kw0000005', 'LTI5', 'a0Kw0000005'),
            ('localhost/simulation/a0Kw0000006/', 'LTI6', 'a0Kw0000006'),
        ]
        licenced_simulations = [ItemFactory.create(
            category='lti', modulestore=self.store, display_name=display_name,
            metadata={'lti_id': 'correct_lti_id', 'launch_url': url}
        ) for url, display_name, __ in data]

        resp = self.client.post(self.url, data=self.data, follow=True)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(7, resp.content.count('Enter a valid URL.'))
        self.assertEqual(5, resp.content.count('Enter a valid simulation id.'))

        for item in data:
            self.assertContains(resp, item[1])  # Display name
            self.assertContains(resp, item[2])  # Simulation id
