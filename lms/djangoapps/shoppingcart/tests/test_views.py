"""
Tests for Shopping Cart views
"""
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.views import add_course_to_cart
from shoppingcart.models import Order, OrderItem, CertificateItem, InvalidCartItem, PaidCourseRegistration
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from ..exceptions import PurchasedCallbackException

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE, DEBUG=True)
class ShoppingCartViewsTests(ModuleStoreTestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "MITx/999/Robot_Super_Course"
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_mode = CourseMode(course_id=self.course_id,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.cart = Order.get_cart_for_user(self.user)

    def test_add_course_to_cart_anon(self):
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_id]))
        self.assertEqual(resp.status_code, 403)
