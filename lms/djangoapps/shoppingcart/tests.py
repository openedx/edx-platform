"""
Tests for the Shopping Cart
"""

from factory import DjangoModelFactory
from django.test import TestCase
from shoppingcart.models import Order, VerifiedCertificate
from student.tests.factories import UserFactory


class OrderFactory(DjangoModelFactory):
    FACTORY_FOR = Order


class VerifiedCertificateFactory(DjangoModelFactory):
    FACTORY_FOR = VerifiedCertificate


class OrderTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.cart = OrderFactory.create(user=self.user, status='cart')
        self.course_id = "test/course"

    def test_add_item_to_cart(self):
        pass

    def test_total_cost(self):
        # add items to the order
        cost = 30
        iterations = 5
        for _ in xrange(iterations):
            VerifiedCertificate.add_to_order(self.cart, self.user, self.course_id, cost)
        self.assertEquals(self.cart.total_cost, cost * iterations)

