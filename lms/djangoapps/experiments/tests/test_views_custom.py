"""
Tests for experimentation views
"""
from __future__ import absolute_import

from django.urls import reverse
from mock import Mock, patch
from rest_framework.test import APITestCase

from course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from student.tests.factories import UserFactory

from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from xmodule.modulestore.tests.factories import CourseFactory, SampleCourseFactory, ToyCourseFactory

# from openedx.core.djangoapps.catalog.tests.factories import (
#     CourseFactory,
#     CourseRunFactory,
#     EntitlementFactory,
#     ProgramFactory,
#     SeatFactory,
#     generate_course_run_key
# )

from lms.djangoapps.experiments.views_custom import MOBILE_UPSELL_FLAG

CROSS_DOMAIN_REFERER = 'https://ecommerce.edx.org'


class Rev934LoggedOutTests(APITestCase):
    def test_not_logged_in(self):
        """Test mobile app upsell API"""
        url = reverse('api_experiments:rev_934')

        # Not-logged-in returns 401
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)


class Rev934Tests(APITestCase, ModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(Rev934Tests, cls).setUpClass()
        cls.url = reverse('api_experiments:rev_934')

    def setUp(self):
        super(Rev934Tests, self).setUp()
        user = UserFactory(username='robot-mue-1-6pnjv')  # robot-mue-0-l23fi
        self.client.login(
            username=user.username,
            password=UserFactory._DEFAULT_PASSWORD,  # pylint: disable=protected-access
        )

    @override_waffle_flag(MOBILE_UPSELL_FLAG, active=False)
    def test_flag_off(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['show_upsell'], False)
        self.assertEqual(response.data['upsell_flag'], False)

    @override_waffle_flag(MOBILE_UPSELL_FLAG, active=True)
    def test_no_course_id(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    @override_waffle_flag(MOBILE_UPSELL_FLAG, active=True)
    def test_bad_course_id(self):
        response = self.client.get(self.url, {'course_id': 'junk'})
        self.assertEqual(response.status_code, 400)

    # @override_waffle_flag(MOBILE_UPSELL_FLAG, active=True)
    # def test_simple_course(self):
    #     course = CourseFactory.create()
    #     response = self.client.get(self.url, {'course_id': course.id})
    #     self.assertEqual(response.status_code, 200)
    #     expected = {
    #         'show_upsell': False,
    #         'upsell_flag': True,
    #         'experiment_bucket': 1,
    #         'could_upsell': False,
    #     }
    #     self.assertEqual(response.data, expected)

    @override_waffle_flag(MOBILE_UPSELL_FLAG, active=True)
    def test_course(self):
        course_run = {
            'status': 'published', 
            'seats': [
                {
                    'type': 'verified', 
                    'price': '86.00', 
                    'sku': 'B9B6D0B'
                }
            ]
        }

        course = CourseFactory.create(run='test', display_name='test')
        CourseModeFactory.create(course_id=course.id, mode_slug='verified')
        import pdb;pdb.set_trace()  # BJH: DELETEME    

        response = self.client.get(self.url, {'course_id': course.id})
        self.assertEqual(response.status_code, 200)
        expected = {
            'show_upsell': True,
            'price': u'Free',
            'basket_url': None,
        }
        self.assertEqual(response.data, expected)
