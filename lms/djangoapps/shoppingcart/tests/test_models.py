"""
Tests for the Shopping Cart Models
"""

from factory import DjangoModelFactory
from mock import patch
from django.test import TestCase
from django.test.utils import override_settings
from django.db import DatabaseError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.models import Order, OrderItem, CertificateItem, InvalidCartItem, PaidCourseRegistration
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.exceptions import PurchasedCallbackException


class OrderTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "test/course"
        self.cost = 40

    def test_get_cart_for_user(self):
        # create a cart
        cart = Order.get_cart_for_user(user=self.user)
        # add something to it
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        # should return the same cart
        cart2 = Order.get_cart_for_user(user=self.user)
        self.assertEquals(cart2.orderitem_set.count(), 1)

    def test_cart_clear(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        CertificateItem.add_to_order(cart, 'test/course1', self.cost, 'verified')
        self.assertEquals(cart.orderitem_set.count(), 2)
        cart.clear()
        self.assertEquals(cart.orderitem_set.count(), 0)

    def test_add_item_to_cart_currency_match(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified', currency='eur')
        # verify that a new item has been added
        self.assertEquals(cart.orderitem_set.count(), 1)
        # verify that the cart's currency was updated
        self.assertEquals(cart.currency, 'eur')
        with self.assertRaises(InvalidCartItem):
            CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified', currency='usd')
        # assert that this item did not get added to the cart
        self.assertEquals(cart.orderitem_set.count(), 1)

    def test_total_cost(self):
        cart = Order.get_cart_for_user(user=self.user)
        # add items to the order
        course_costs = [('test/course1', 30),
                        ('test/course2', 40),
                        ('test/course3', 10),
                        ('test/course4', 20)]
        for course, cost in course_costs:
            CertificateItem.add_to_order(cart, course, cost, 'verified')
        self.assertEquals(cart.orderitem_set.count(), len(course_costs))
        self.assertEquals(cart.total_cost, sum(cost for _course, cost in course_costs))

    def test_purchase(self):
        # This test is for testing the subclassing functionality of OrderItem, but in
        # order to do this, we end up testing the specific functionality of
        # CertificateItem, which is not quite good unit test form. Sorry.
        cart = Order.get_cart_for_user(user=self.user)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        # course enrollment object should be created but still inactive
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))
        cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))

    def test_purchase_item_failure(self):
        # once again, we're testing against the specific implementation of
        # CertificateItem
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        with patch('shoppingcart.models.CertificateItem.save', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                cart.purchase()
                # verify that we rolled back the entire transaction
                self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))


class OrderItemTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()

    def test_orderItem_purchased_callback(self):
        """
        This tests that calling purchased_callback on the base OrderItem class raises NotImplementedError
        """
        item = OrderItem(user=self.user, order=Order.get_cart_for_user(self.user))
        with self.assertRaises(NotImplementedError):
            item.purchased_callback()


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class PaidCourseRegistrationTest(ModuleStoreTestCase):
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

    def test_add_to_order(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)

        self.assertEqual(reg1.unit_cost, self.cost)
        self.assertEqual(reg1.line_cost, self.cost)
        self.assertEqual(reg1.unit_cost, self.course_mode.min_price)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertTrue(PaidCourseRegistration.part_of_order(self.cart, self.course_id))
        self.assertFalse(PaidCourseRegistration.part_of_order(self.cart, self.course_id + "abcd"))
        self.assertEqual(self.cart.total_cost, self.cost)

    def test_add_with_default_mode(self):
        """
        Tests add_to_cart where the mode specified in the argument is NOT in the database
        and NOT the default "honor".  In this case it just adds the user in the CourseMode.DEFAULT_MODE, 0 price
        """
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id, mode_slug="DNE")

        self.assertEqual(reg1.unit_cost, 0)
        self.assertEqual(reg1.line_cost, 0)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertEqual(self.cart.total_cost, 0)
        self.assertTrue(PaidCourseRegistration.part_of_order(self.cart, self.course_id))

    def test_purchased_callback(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        self.cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
        reg1 = PaidCourseRegistration.objects.get(id=reg1.id)  # reload from DB to get side-effect
        self.assertEqual(reg1.status, "purchased")

    def test_purchased_callback_exception(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_id)
        reg1.course_id = "changedforsomereason"
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))

        reg1.course_id = "abc/efg/hij"
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_id))


class CertificateItemTest(TestCase):
    """
    Tests for verifying specific CertificateItem functionality
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.course_id = "test/course"
        self.cost = 40

    def test_existing_enrollment(self):
        CourseEnrollment.enroll(self.user, self.course_id)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_id, self.cost, 'verified')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_id))
        cart.purchase()
        enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_id)
        self.assertEquals(enrollment.mode, u'verified')
