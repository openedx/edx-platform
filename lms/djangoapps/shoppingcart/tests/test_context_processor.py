"""
Unit tests for shoppingcart context_processor
"""
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from mock import patch, Mock

from course_modes.tests.factories import CourseModeFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from shoppingcart.models import Order, PaidCourseRegistration
from shoppingcart.context_processor import user_has_cart_context_processor


class UserCartContextProcessorUnitTest(ModuleStoreTestCase):
    """
    Unit test for shoppingcart context_processor
    """
    def setUp(self):
        super(UserCartContextProcessorUnitTest, self).setUp()

        self.user = UserFactory.create()
        self.request = Mock()

    def add_to_cart(self):
        """
        Adds content to self.user's cart
        """
        course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        CourseModeFactory.create(course_id=course.id)
        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course.id)

    @patch.dict(settings.FEATURES, {'ENABLE_SHOPPING_CART': False, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_no_enable_shoppingcart(self):
        """
        Tests when FEATURES['ENABLE_SHOPPING_CART'] is not set
        """
        self.add_to_cart()
        self.request.user = self.user
        context = user_has_cart_context_processor(self.request)
        self.assertFalse(context['should_display_shopping_cart_func']())

    @patch.dict(settings.FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': False})
    def test_no_enable_paid_course_registration(self):
        """
        Tests when FEATURES['ENABLE_PAID_COURSE_REGISTRATION'] is not set
        """
        self.add_to_cart()
        self.request.user = self.user
        context = user_has_cart_context_processor(self.request)
        self.assertFalse(context['should_display_shopping_cart_func']())

    @patch.dict(settings.FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_anonymous_user(self):
        """
        Tests when request.user is anonymous
        """
        self.request.user = AnonymousUser()
        context = user_has_cart_context_processor(self.request)
        self.assertFalse(context['should_display_shopping_cart_func']())

    @patch.dict(settings.FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_no_items_in_cart(self):
        """
        Tests when request.user doesn't have a cart with items
        """
        self.request.user = self.user
        context = user_has_cart_context_processor(self.request)
        self.assertFalse(context['should_display_shopping_cart_func']())

    @patch.dict(settings.FEATURES, {'ENABLE_SHOPPING_CART': True, 'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_items_in_cart(self):
        """
        Tests when request.user has a cart with items
        """
        self.add_to_cart()
        self.request.user = self.user
        context = user_has_cart_context_processor(self.request)
        self.assertTrue(context['should_display_shopping_cart_func']())
