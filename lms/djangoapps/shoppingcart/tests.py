"""
Tests for the Shopping Cart
"""

from factory import DjangoModelFactory
from django.test import TestCase
from shoppingcart import models
from student.tests.factories import UserFactory


class OrderFactory(DjangoModelFactory):
    FACTORY_FOR = models.Order


class OrderItem(DjangoModelFactory):
    FACTORY_FOR = models.OrderItem


class OrderTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.cart = OrderFactory.create(user=self.user, status='cart')

    def test_total_cost(self):
        # add items to the order
        for _ in xrange(5):
            pass
