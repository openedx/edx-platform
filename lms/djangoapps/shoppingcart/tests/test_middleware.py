"""
Unit tests for shoppingcart middleware
"""
from mock import patch, Mock
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory
from course_modes.models import CourseMode
from shoppingcart.models import Order, PaidCourseRegistration
from shoppingcart.middleware import UserHasCartMiddleware

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class UserCartMiddlewareUnitTest(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.request = Mock()
        self.mw = UserHasCartMiddleware()

    def add_to_cart(self):
        course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        course_mode = CourseMode(course_id=course.id,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=40)
        course_mode.save()
        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course.id)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_SHOPPING_CART': False, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_no_enable_shoppingcart(self):
        """
        Tests when MITX_FEATURES['ENABLE_SHOPPING_CART'] is not set
        """
        self.add_to_cart()
        self.request.user = self.user
        self.mw.process_request(self.request)
        self.assertFalse(self.request.display_shopping_cart)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': False})
    def test_no_enable_paid_course_registration(self):
        """
        Tests when MITX_FEATURES['ENABLE_PAID_COURSE_REGISTRATION'] is not set
        """
        self.add_to_cart()
        self.request.user = self.user
        self.mw.process_request(self.request)
        self.assertFalse(self.request.display_shopping_cart)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_anonymous_user(self):
        """
        Tests when request.user is anonymous
        """
        self.request.user = AnonymousUser()
        self.mw.process_request(self.request)
        self.assertFalse(self.request.display_shopping_cart)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_no_items_in_cart(self):
        """
        Tests when request.user doesn't have a cart with items
        """
        self.request.user = self.user
        self.mw.process_request(self.request)
        self.assertFalse(self.request.display_shopping_cart)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_items_in_cart(self):
        """
        Tests when request.user has a cart with items
        """
        self.add_to_cart()
        self.request.user = self.user
        self.mw.process_request(self.request)
        self.assertTrue(self.request.display_shopping_cart)
