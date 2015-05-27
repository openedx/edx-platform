"""Tests for the retire_order command"""

from tempfile import NamedTemporaryFile
from django.core.management import call_command

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from shoppingcart.models import Order, CertificateItem
from student.tests.factories import UserFactory


class TestRetireOrder(ModuleStoreTestCase):
    """Test the retire_order command"""
    def setUp(self):
        super(TestRetireOrder, self).setUp()

        course = CourseFactory.create()
        self.course_key = course.id

        # set up test carts
        self.cart, __ = self._create_cart()

        self.paying, __ = self._create_cart()
        self.paying.start_purchase()

        self.already_defunct_cart, __ = self._create_cart()
        self.already_defunct_cart.retire()

        self.purchased, self.purchased_item = self._create_cart()
        self.purchased.status = "purchased"
        self.purchased.save()
        self.purchased_item.status = "purchased"
        self.purchased.save()

    def test_retire_order(self):
        """Test the retire_order command"""
        nonexistent_id = max(order.id for order in Order.objects.all()) + 1
        order_ids = [
            self.cart.id,
            self.paying.id,
            self.already_defunct_cart.id,
            self.purchased.id,
            nonexistent_id
        ]

        self._create_tempfile_and_call_command(order_ids)

        self.assertEqual(
            Order.objects.get(id=self.cart.id).status, "defunct-cart"
        )
        self.assertEqual(
            Order.objects.get(id=self.paying.id).status, "defunct-paying"
        )
        self.assertEqual(
            Order.objects.get(id=self.already_defunct_cart.id).status,
            "defunct-cart"
        )
        self.assertEqual(
            Order.objects.get(id=self.purchased.id).status, "purchased"
        )

    def _create_tempfile_and_call_command(self, order_ids):
        """
        Takes a list of order_ids, writes them to a tempfile, and then runs the
        "retire_order" command on the tempfile
        """
        with NamedTemporaryFile() as temp:
            temp.write("\n".join(str(order_id) for order_id in order_ids))
            temp.seek(0)
            call_command('retire_order', temp.name)

    def _create_cart(self):
        """Creates a cart and adds a CertificateItem to it"""
        cart = Order.get_cart_for_user(UserFactory.create())
        item = CertificateItem.add_to_order(
            cart, self.course_key, 10, 'honor', currency='usd'
        )
        return cart, item
