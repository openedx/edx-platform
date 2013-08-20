"""
Tests for the Shopping Cart
"""

from factory import DjangoModelFactory
from django.test import TestCase
from shoppingcart.models import Order, CertificateItem, InvalidCartItem
from student.tests.factories import UserFactory
from student.models import CourseEnrollment


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
