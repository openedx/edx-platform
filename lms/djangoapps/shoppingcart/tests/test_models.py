"""
Tests for the Shopping Cart Models
"""
from decimal import Decimal
import datetime
import sys
import json
import copy

import smtplib
from boto.exception import BotoServerError  # this is a super-class of SESError and catches connection errors

from mock import patch, MagicMock
import pytz
import ddt
from django.core import mail
from django.core.mail.message import EmailMessage
from django.conf import settings
from django.db import DatabaseError
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from shoppingcart.models import (
    Order, OrderItem, CertificateItem,
    InvalidCartItem, CourseRegistrationCode, PaidCourseRegistration, CourseRegCodeItem,
    Donation, OrderItemSubclassPK,
    Invoice, CourseRegistrationCodeInvoiceItem, InvoiceTransaction, InvoiceHistory,
    RegistrationCodeRedemption,
    Coupon, CouponRedemption)
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from shoppingcart.exceptions import (
    PurchasedCallbackException,
    CourseDoesNotExistException,
    ItemAlreadyInCartException,
    AlreadyEnrolledInCourseException,
    InvalidStatusToRetire,
    UnexpectedOrderItemStatus,
)

from opaque_keys.edx.locator import CourseLocator


@ddt.ddt
class OrderTest(ModuleStoreTestCase):
    def setUp(self):
        super(OrderTest, self).setUp()

        self.user = UserFactory.create()
        course = CourseFactory.create()
        self.course_key = course.id
        self.other_course_keys = []
        for __ in xrange(1, 5):
            self.other_course_keys.append(CourseFactory.create().id)
        self.cost = 40

        # Add mock tracker for event testing.
        patcher = patch('shoppingcart.models.analytics')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def test_get_cart_for_user(self):
        # create a cart
        cart = Order.get_cart_for_user(user=self.user)
        # add something to it
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # should return the same cart
        cart2 = Order.get_cart_for_user(user=self.user)
        self.assertEquals(cart2.orderitem_set.count(), 1)

    def test_user_cart_has_items(self):
        anon = AnonymousUser()
        self.assertFalse(Order.user_cart_has_items(anon))
        self.assertFalse(Order.user_cart_has_items(self.user))
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(order=cart, user=self.user)
        item.save()
        self.assertTrue(Order.user_cart_has_items(self.user))
        self.assertFalse(Order.user_cart_has_items(self.user, [CertificateItem]))
        self.assertFalse(Order.user_cart_has_items(self.user, [PaidCourseRegistration]))

    def test_user_cart_has_paid_course_registration_items(self):
        cart = Order.get_cart_for_user(self.user)
        item = PaidCourseRegistration(order=cart, user=self.user)
        item.save()
        self.assertTrue(Order.user_cart_has_items(self.user, [PaidCourseRegistration]))
        self.assertFalse(Order.user_cart_has_items(self.user, [CertificateItem]))

    def test_user_cart_has_certificate_items(self):
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        self.assertTrue(Order.user_cart_has_items(self.user, [CertificateItem]))
        self.assertFalse(Order.user_cart_has_items(self.user, [PaidCourseRegistration]))

    def test_cart_clear(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        CertificateItem.add_to_order(cart, self.other_course_keys[0], self.cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), 2)
        self.assertTrue(cart.has_items())
        cart.clear()
        self.assertEquals(cart.orderitem_set.count(), 0)
        self.assertFalse(cart.has_items())

    def test_add_item_to_cart_currency_match(self):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='eur')
        # verify that a new item has been added
        self.assertEquals(cart.orderitem_set.count(), 1)
        # verify that the cart's currency was updated
        self.assertEquals(cart.currency, 'eur')
        with self.assertRaises(InvalidCartItem):
            CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
        # assert that this item did not get added to the cart
        self.assertEquals(cart.orderitem_set.count(), 1)

    def test_total_cost(self):
        cart = Order.get_cart_for_user(user=self.user)
        # add items to the order
        course_costs = [(self.other_course_keys[0], 30),
                        (self.other_course_keys[1], 40),
                        (self.other_course_keys[2], 10),
                        (self.other_course_keys[3], 20)]
        for course, cost in course_costs:
            CertificateItem.add_to_order(cart, course, cost, 'honor')
        self.assertEquals(cart.orderitem_set.count(), len(course_costs))
        self.assertEquals(cart.total_cost, sum(cost for _course, cost in course_costs))

    def test_start_purchase(self):
        # Start the purchase, which will mark the cart as "paying"
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
        cart.start_purchase()
        self.assertEqual(cart.status, 'paying')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'paying')

        # Starting the purchase should be idempotent
        cart.start_purchase()
        self.assertEqual(cart.status, 'paying')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'paying')

        # If we retrieve the cart for the user, we should get a different order
        next_cart = Order.get_cart_for_user(user=self.user)
        self.assertNotEqual(cart, next_cart)
        self.assertEqual(next_cart.status, 'cart')

        # Complete the first purchase
        cart.purchase()
        self.assertEqual(cart.status, 'purchased')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'purchased')

        # Starting the purchase again should be a no-op
        cart.start_purchase()
        self.assertEqual(cart.status, 'purchased')
        for item in cart.orderitem_set.all():
            self.assertEqual(item.status, 'purchased')

    def test_retire_order_cart(self):
        """Test that an order in cart can successfully be retired"""
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')

        cart.retire()
        self.assertEqual(cart.status, 'defunct-cart')
        self.assertEqual(cart.orderitem_set.get().status, 'defunct-cart')

    def test_retire_order_paying(self):
        """Test that an order in "paying" can successfully be retired"""
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
        cart.start_purchase()

        cart.retire()
        self.assertEqual(cart.status, 'defunct-paying')
        self.assertEqual(cart.orderitem_set.get().status, 'defunct-paying')

    @ddt.data(
        ("cart", "paying", UnexpectedOrderItemStatus),
        ("purchased", "purchased", InvalidStatusToRetire),
    )
    @ddt.unpack
    def test_retire_order_error(self, order_status, item_status, exception):
        """
        Test error cases for retiring an order:
        1) Order item has a different status than the order
        2) The order's status isn't in "cart" or "paying"
        """
        cart = Order.get_cart_for_user(user=self.user)
        item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')

        cart.status = order_status
        cart.save()
        item.status = item_status
        item.save()

        with self.assertRaises(exception):
            cart.retire()

    @ddt.data('defunct-paying', 'defunct-cart')
    def test_retire_order_already_retired(self, status):
        """
        Check that orders that have already been retired noop when the method
        is called on them again.
        """
        cart = Order.get_cart_for_user(user=self.user)
        item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor', currency='usd')
        cart.status = item.status = status
        cart.save()
        item.save()
        cart.retire()
        self.assertEqual(cart.status, status)
        self.assertEqual(item.status, status)

    @override_settings(
        SEGMENT_IO_LMS_KEY="foobar",
        FEATURES={
            'SEGMENT_IO_LMS': True,
            'STORE_BILLING_INFO': True,
        }
    )
    def test_purchase(self):
        # This test is for testing the subclassing functionality of OrderItem, but in
        # order to do this, we end up testing the specific functionality of
        # CertificateItem, which is not quite good unit test form. Sorry.
        cart = Order.get_cart_for_user(user=self.user)
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
        item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # Course enrollment object should be created but still inactive
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
        # Analytics client pipes output to stderr when using the default client
        with patch('sys.stderr', sys.stdout.write):
            cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))

        # Test email sending
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals('Order Payment Confirmation', mail.outbox[0].subject)
        self.assertIn(settings.PAYMENT_SUPPORT_EMAIL, mail.outbox[0].body)
        self.assertIn(unicode(cart.total_cost), mail.outbox[0].body)
        self.assertIn(item.additional_instruction_text(), mail.outbox[0].body)

        # Verify Google Analytics event fired for purchase
        self.mock_tracker.track.assert_called_once_with(  # pylint: disable=maybe-no-member
            self.user.id,
            'Completed Order',
            {
                'orderId': 1,
                'currency': 'usd',
                'total': '40',
                'products': [
                    {
                        'sku': u'CertificateItem.honor',
                        'name': unicode(self.course_key),
                        'category': unicode(self.course_key.org),
                        'price': '40',
                        'id': 1,
                        'quantity': 1
                    }
                ]
            },
            context={'Google Analytics': {'clientId': None}}
        )

    def test_purchase_item_failure(self):
        # once again, we're testing against the specific implementation of
        # CertificateItem
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch('shoppingcart.models.CertificateItem.save', side_effect=DatabaseError):
            with self.assertRaises(DatabaseError):
                cart.purchase()
                # verify that we rolled back the entire transaction
                self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
                # verify that e-mail wasn't sent
                self.assertEquals(len(mail.outbox), 0)

    def test_purchase_twice(self):
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        # purchase the cart more than once
        cart.purchase()
        cart.purchase()
        self.assertEquals(len(mail.outbox), 1)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_smtp_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch('shoppingcart.models.EmailMessage.send', side_effect=smtplib.SMTPException):
            cart.purchase()
            self.assertTrue(error_logger.called)

    @patch('shoppingcart.models.log.error')
    def test_purchase_item_email_boto_failure(self, error_logger):
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        with patch.object(EmailMessage, 'send') as mock_send:
            mock_send.side_effect = BotoServerError("status", "reason")
            cart.purchase()
            self.assertTrue(error_logger.called)

    def purchase_with_data(self, cart):
        """ purchase a cart with billing information """
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        cart.purchase(
            first='John',
            last='Smith',
            street1='11 Cambridge Center',
            street2='Suite 101',
            city='Cambridge',
            state='MA',
            postalcode='02412',
            country='US',
            ccnum='1111',
            cardtype='001',
        )

    @patch('shoppingcart.models.render_to_string')
    @patch.dict(settings.FEATURES, {'STORE_BILLING_INFO': True})
    def test_billing_info_storage_on(self, render):
        cart = Order.get_cart_for_user(self.user)
        self.purchase_with_data(cart)
        self.assertNotEqual(cart.bill_to_first, '')
        self.assertNotEqual(cart.bill_to_last, '')
        self.assertNotEqual(cart.bill_to_street1, '')
        self.assertNotEqual(cart.bill_to_street2, '')
        self.assertNotEqual(cart.bill_to_postalcode, '')
        self.assertNotEqual(cart.bill_to_ccnum, '')
        self.assertNotEqual(cart.bill_to_cardtype, '')
        self.assertNotEqual(cart.bill_to_city, '')
        self.assertNotEqual(cart.bill_to_state, '')
        self.assertNotEqual(cart.bill_to_country, '')
        ((_, context), _) = render.call_args
        self.assertTrue(context['has_billing_info'])

    @patch('shoppingcart.models.render_to_string')
    @patch.dict(settings.FEATURES, {'STORE_BILLING_INFO': False})
    def test_billing_info_storage_off(self, render):
        cart = Order.get_cart_for_user(self.user)
        self.purchase_with_data(cart)
        self.assertNotEqual(cart.bill_to_first, '')
        self.assertNotEqual(cart.bill_to_last, '')
        self.assertNotEqual(cart.bill_to_city, '')
        self.assertNotEqual(cart.bill_to_state, '')
        self.assertNotEqual(cart.bill_to_country, '')
        self.assertNotEqual(cart.bill_to_postalcode, '')
        # things we expect to be missing when the feature is off
        self.assertEqual(cart.bill_to_street1, '')
        self.assertEqual(cart.bill_to_street2, '')
        self.assertEqual(cart.bill_to_ccnum, '')
        self.assertEqual(cart.bill_to_cardtype, '')
        ((_, context), _) = render.call_args
        self.assertFalse(context['has_billing_info'])

    def test_generate_receipt_instructions_callchain(self):
        """
        This tests the generate_receipt_instructions call chain (ie calling the function on the
        cart also calls it on items in the cart
        """
        mock_gen_inst = MagicMock(return_value=(OrderItemSubclassPK(OrderItem, 1), set([])))

        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)
        item.save()
        self.assertTrue(cart.has_items())
        with patch.object(OrderItem, 'generate_receipt_instructions', mock_gen_inst):
            cart.generate_receipt_instructions()
            mock_gen_inst.assert_called_with()

    def test_confirmation_email_error(self):
        CourseMode.objects.create(
            course_id=self.course_key,
            mode_slug="verified",
            mode_display_name="Verified",
            min_price=self.cost
        )

        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')

        # Simulate an error when sending the confirmation
        # email.  This should NOT raise an exception.
        # If it does, then the implicit view-level
        # transaction could cause a roll-back, effectively
        # reversing order fulfillment.
        with patch.object(mail.message.EmailMessage, 'send') as mock_send:
            mock_send.side_effect = Exception("Kaboom!")
            cart.purchase()

        # Verify that the purchase completed successfully
        self.assertEqual(cart.status, 'purchased')

        # Verify that the user is enrolled as "verified"
        mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_key)
        self.assertTrue(is_active)
        self.assertEqual(mode, 'verified')


class OrderItemTest(TestCase):
    def setUp(self):
        super(OrderItemTest, self).setUp()

        self.user = UserFactory.create()

    def test_order_item_purchased_callback(self):
        """
        This tests that calling purchased_callback on the base OrderItem class raises NotImplementedError
        """
        item = OrderItem(user=self.user, order=Order.get_cart_for_user(self.user))
        with self.assertRaises(NotImplementedError):
            item.purchased_callback()

    def test_order_item_generate_receipt_instructions(self):
        """
        This tests that the generate_receipt_instructions call chain and also
        that calling it on the base OrderItem class returns an empty list
        """
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)
        item.save()
        self.assertTrue(cart.has_items())
        (inst_dict, inst_set) = cart.generate_receipt_instructions()
        self.assertDictEqual({item.pk_with_subclass: set([])}, inst_dict)
        self.assertEquals(set([]), inst_set)

    def test_is_discounted(self):
        """
        This tests the is_discounted property of the OrderItem
        """
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)

        item.list_price = None
        item.unit_cost = 100
        self.assertFalse(item.is_discounted)

        item.list_price = 100
        item.unit_cost = 100
        self.assertFalse(item.is_discounted)

        item.list_price = 100
        item.unit_cost = 90
        self.assertTrue(item.is_discounted)

    def test_get_list_price(self):
        """
        This tests the get_list_price() method of the OrderItem
        """
        cart = Order.get_cart_for_user(self.user)
        item = OrderItem(user=self.user, order=cart)

        item.list_price = None
        item.unit_cost = 100
        self.assertEqual(item.get_list_price(), item.unit_cost)

        item.list_price = 200
        item.unit_cost = 100
        self.assertEqual(item.get_list_price(), item.list_price)


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class PaidCourseRegistrationTest(ModuleStoreTestCase):
    """
    Paid Course Registration Tests.
    """
    def setUp(self):
        super(PaidCourseRegistrationTest, self).setUp()

        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.cost = 40
        self.course = CourseFactory.create()
        self.course_key = self.course.id
        self.course_mode = CourseMode(course_id=self.course_key,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.percentage_discount = 20.0
        self.cart = Order.get_cart_for_user(self.user)

    def test_get_total_amount_of_purchased_items(self):
        """
        Test to check the total amount of the
        purchased items.
        """
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()

        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(course_key=self.course_key)
        self.assertEqual(total_amount, 40.00)

    def test_get_total_amount_empty(self):
        """
        Test to check the total amount of the
        purchased items.
        """
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(course_key=self.course_key)
        self.assertEqual(total_amount, 0.00)

    def test_add_to_order(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)

        self.assertEqual(reg1.unit_cost, self.cost)
        self.assertEqual(reg1.line_cost, self.cost)
        self.assertEqual(reg1.unit_cost, self.course_mode.min_price)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_key))
        self.assertFalse(PaidCourseRegistration.contained_in_order(
            self.cart, CourseLocator(org="MITx", course="999", run="Robot_Super_Course_abcd"))
        )

        self.assertEqual(self.cart.total_cost, self.cost)

    def test_order_generated_registration_codes(self):
        """
        Test to check for the order generated registration
        codes.
        """
        self.cart.order_type = 'business'
        self.cart.save()
        item = CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        self.cart.purchase()
        registration_codes = CourseRegistrationCode.order_generated_registration_codes(self.course_key)
        self.assertEqual(registration_codes.count(), item.qty)

    def test_order_generated_totals(self):
        """
        Test to check for the order generated registration
        codes.
        """

        total_amount = CourseRegCodeItem.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 0)

        self.cart.order_type = 'business'
        self.cart.save()
        item = CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        self.cart.purchase()
        registration_codes = CourseRegistrationCode.order_generated_registration_codes(self.course_key)
        self.assertEqual(registration_codes.count(), item.qty)

        total_amount = CourseRegCodeItem.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 80.00)

    def add_coupon(self, course_key, is_active, code):
        """
        add dummy coupon into models
        """
        Coupon.objects.create(
            code=code,
            description='testing code',
            course_id=course_key,
            percentage_discount=self.percentage_discount,
            created_by=self.user,
            is_active=is_active
        )

    def login_user(self, username):
        """
        login the user to the platform.
        """
        self.client.login(username=username, password="password")

    def test_get_top_discount_codes_used(self):
        """
        Test to check for the top coupon codes used.
        """
        self.login_user(self.user.username)
        self.add_coupon(self.course_key, True, 'Ad123asd')
        self.add_coupon(self.course_key, True, '32213asd')
        self.purchases_using_coupon_codes()
        top_discounted_codes = CouponRedemption.get_top_discount_codes_used(self.course_key)
        self.assertTrue(top_discounted_codes[0]['coupon__code'], 'Ad123asd')
        self.assertTrue(top_discounted_codes[0]['coupon__used_count'], 1)
        self.assertTrue(top_discounted_codes[1]['coupon__code'], '32213asd')
        self.assertTrue(top_discounted_codes[1]['coupon__used_count'], 2)

    def test_get_total_coupon_code_purchases(self):
        """
        Test to assert the number of coupon code purchases.
        """
        self.login_user(self.user.username)
        self.add_coupon(self.course_key, True, 'Ad123asd')
        self.add_coupon(self.course_key, True, '32213asd')
        self.purchases_using_coupon_codes()

        total_coupon_code_purchases = CouponRedemption.get_total_coupon_code_purchases(self.course_key)
        self.assertTrue(total_coupon_code_purchases['coupon__count'], 3)

    def test_get_self_purchased_seat_count(self):
        """
        Test to assert the number of seats
        purchased using individual purchases.
        """
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()

        test_student = UserFactory.create()
        test_student.set_password('password')
        test_student.save()

        self.cart = Order.get_cart_for_user(test_student)
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()

        total_seats_count = PaidCourseRegistration.get_self_purchased_seat_count(course_key=self.course_key)
        self.assertTrue(total_seats_count, 2)

    def purchases_using_coupon_codes(self):
        """
        helper method that uses coupon codes when purchasing courses.
        """
        self.cart.order_type = 'business'
        self.cart.save()
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': 'Ad123asd'})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase()

        self.cart.clear()
        self.cart = Order.get_cart_for_user(self.user)
        self.cart.order_type = 'business'
        self.cart.save()
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': 'Ad123asd'})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase()

        self.cart.clear()
        self.cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': '32213asd'})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase()

    def test_cart_type_business(self):
        self.cart.order_type = 'business'
        self.cart.save()
        item = CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        self.cart.purchase()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))
        # check that the registration codes are generated against the order
        registration_codes = CourseRegistrationCode.order_generated_registration_codes(self.course_key)
        self.assertEqual(registration_codes.count(), item.qty)

    def test_regcode_redemptions(self):
        """
        Asserts the data model around RegistrationCodeRedemption
        """
        self.cart.order_type = 'business'
        self.cart.save()
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        self.cart.purchase()

        reg_code = CourseRegistrationCode.order_generated_registration_codes(self.course_key)[0]

        enrollment = CourseEnrollment.enroll(self.user, self.course_key)

        redemption = RegistrationCodeRedemption(
            registration_code=reg_code,
            redeemed_by=self.user,
            course_enrollment=enrollment
        )
        redemption.save()

        test_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(enrollment)

        self.assertEqual(test_redemption.id, redemption.id)  # pylint: disable=no-member

    def test_regcode_multi_redemptions(self):
        """
        Asserts the data model around RegistrationCodeRedemption and
        what happens when we do multiple redemptions by same user
        """
        self.cart.order_type = 'business'
        self.cart.save()
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        self.cart.purchase()

        reg_codes = CourseRegistrationCode.order_generated_registration_codes(self.course_key)

        self.assertEqual(len(reg_codes), 2)

        enrollment = CourseEnrollment.enroll(self.user, self.course_key)

        ids = []
        for reg_code in reg_codes:
            redemption = RegistrationCodeRedemption(
                registration_code=reg_code,
                redeemed_by=self.user,
                course_enrollment=enrollment
            )
            redemption.save()
            ids.append(redemption.id)  # pylint: disable=no-member

        test_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(enrollment)

        self.assertIn(test_redemption.id, ids)  # pylint: disable=no-member

    def test_add_with_default_mode(self):
        """
        Tests add_to_cart where the mode specified in the argument is NOT in the database
        and NOT the default "honor".  In this case it just adds the user in the CourseMode.DEFAULT_MODE, 0 price
        """
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key, mode_slug="DNE")

        self.assertEqual(reg1.unit_cost, 0)
        self.assertEqual(reg1.line_cost, 0)
        self.assertEqual(reg1.mode, "honor")
        self.assertEqual(reg1.user, self.user)
        self.assertEqual(reg1.status, "cart")
        self.assertEqual(self.cart.total_cost, 0)
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_key))

        course_reg_code_item = CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2, mode_slug="DNE")

        self.assertEqual(course_reg_code_item.unit_cost, 0)
        self.assertEqual(course_reg_code_item.line_cost, 0)
        self.assertEqual(course_reg_code_item.mode, "honor")
        self.assertEqual(course_reg_code_item.user, self.user)
        self.assertEqual(course_reg_code_item.status, "cart")
        self.assertEqual(self.cart.total_cost, 0)
        self.assertTrue(CourseRegCodeItem.contained_in_order(self.cart, self.course_key))

    def test_add_course_reg_item_with_no_course_item(self):
        fake_course_id = CourseLocator(org="edx", course="fake", run="course")
        with self.assertRaises(CourseDoesNotExistException):
            CourseRegCodeItem.add_to_order(self.cart, fake_course_id, 2)

    def test_course_reg_item_already_in_cart(self):
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        with self.assertRaises(ItemAlreadyInCartException):
            CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)

    def test_course_reg_item_already_enrolled_in_course(self):
        CourseEnrollment.enroll(self.user, self.course_key)
        with self.assertRaises(AlreadyEnrolledInCourseException):
            CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)

    def test_purchased_callback(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))
        reg1 = PaidCourseRegistration.objects.get(id=reg1.id)  # reload from DB to get side-effect
        self.assertEqual(reg1.status, "purchased")
        self.assertIsNotNone(reg1.course_enrollment)
        self.assertEqual(reg1.course_enrollment.id, CourseEnrollment.objects.get(user=self.user, course_id=self.course_key).id)

    def test_generate_receipt_instructions(self):
        """
        Add 2 courses to the order and make sure the instruction_set only contains 1 element (no dups)
        """
        course2 = CourseFactory.create()
        course_mode2 = CourseMode(course_id=course2.id,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=self.cost)
        course_mode2.save()
        pr1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        pr2 = PaidCourseRegistration.add_to_order(self.cart, course2.id)
        self.cart.purchase()
        inst_dict, inst_set = self.cart.generate_receipt_instructions()
        self.assertEqual(2, len(inst_dict))
        self.assertEqual(1, len(inst_set))
        self.assertIn("dashboard", inst_set.pop())
        self.assertIn(pr1.pk_with_subclass, inst_dict)
        self.assertIn(pr2.pk_with_subclass, inst_dict)

    def test_purchased_callback_exception(self):
        reg1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        reg1.course_id = CourseLocator(org="changed", course="forsome", run="reason")
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))

        reg1.course_id = CourseLocator(org="abc", course="efg", run="hij")
        reg1.save()
        with self.assertRaises(PurchasedCallbackException):
            reg1.purchased_callback()
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course_key))

        course_reg_code_item = CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2)
        course_reg_code_item.course_id = CourseLocator(org="changed1", course="forsome1", run="reason1")
        course_reg_code_item.save()
        with self.assertRaises(PurchasedCallbackException):
            course_reg_code_item.purchased_callback()

    def test_user_cart_has_both_items(self):
        """
        This test exists b/c having both CertificateItem and PaidCourseRegistration in an order used to break
        PaidCourseRegistration.contained_in_order
        """
        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.assertTrue(PaidCourseRegistration.contained_in_order(cart, self.course_key))


class CertificateItemTest(ModuleStoreTestCase):
    """
    Tests for verifying specific CertificateItem functionality
    """
    def setUp(self):
        super(CertificateItemTest, self).setUp()

        self.user = UserFactory.create()
        self.cost = 40
        course = CourseFactory.create()
        self.course_key = course.id
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="honor",
                                 mode_display_name="honor cert",
                                 min_price=self.cost)
        course_mode.save()
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost)
        course_mode.save()

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

        analytics_patcher = patch('shoppingcart.models.analytics')
        self.mock_analytics_tracker = analytics_patcher.start()
        self.addCleanup(analytics_patcher.stop)

    def _assert_refund_tracked(self):
        """
        Assert that we fired a refund event.
        """
        self.mock_analytics_tracker.track.assert_called_with(  # pylint: disable=maybe-no-member
            self.user.id,
            'Refunded Order',
            {
                'orderId': 1,
                'currency': 'usd',
                'total': '40',
                'products': [
                    {
                        'sku': u'CertificateItem.verified',
                        'name': unicode(self.course_key),
                        'category': unicode(self.course_key.org),
                        'price': '40',
                        'id': 1,
                        'quantity': 1
                    }
                ]
            },
            context={'Google Analytics': {'clientId': None}}
        )

    def test_existing_enrollment(self):
        CourseEnrollment.enroll(self.user, self.course_key)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))
        self.mock_tracker.reset_mock()
        cart.purchase()
        enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEquals(enrollment.mode, u'verified')

    def test_single_item_template(self):
        cart = Order.get_cart_for_user(user=self.user)
        cert_item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
        self.assertEquals(cert_item.single_item_receipt_template, 'shoppingcart/receipt.html')

        cert_item = CertificateItem.add_to_order(cart, self.course_key, self.cost, 'honor')
        self.assertEquals(cert_item.single_item_receipt_template, 'shoppingcart/receipt.html')

    @override_settings(
        SEGMENT_IO_LMS_KEY="foobar",
        FEATURES={
            'SEGMENT_IO_LMS': True,
            'STORE_BILLING_INFO': True,
        }
    )
    def test_refund_cert_callback_no_expiration(self):
        # When there is no expiration date on a verified mode, the user can always get a refund

        # need to prevent analytics errors from appearing in stderr
        with patch('sys.stderr', sys.stdout.write):
            CourseEnrollment.enroll(self.user, self.course_key, 'verified')
            cart = Order.get_cart_for_user(user=self.user)
            CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
            cart.purchase()
            CourseEnrollment.unenroll(self.user, self.course_key)

        target_certs = CertificateItem.objects.filter(course_id=self.course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')
        self._assert_refund_tracked()

    def test_no_refund_on_cert_callback(self):
        # If we explicitly skip refunds, the unenroll action should not modify the purchase.
        CourseEnrollment.enroll(self.user, self.course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
        cart.purchase()

        CourseEnrollment.unenroll(self.user, self.course_key, skip_refund=True)
        target_certs = CertificateItem.objects.filter(
            course_id=self.course_key,
            user_id=self.user,
            status='purchased',
            mode='verified'
        )
        self.assertTrue(target_certs[0])
        self.assertFalse(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'purchased')

    @override_settings(
        SEGMENT_IO_LMS_KEY="foobar",
        FEATURES={
            'SEGMENT_IO_LMS': True,
            'STORE_BILLING_INFO': True,
        }
    )
    def test_refund_cert_callback_before_expiration(self):
        # If the expiration date has not yet passed on a verified mode, the user can be refunded
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create()
        self.course_key = course.id
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=(datetime.datetime.now(pytz.utc) + many_days))
        course_mode.save()

        # need to prevent analytics errors from appearing in stderr
        with patch('sys.stderr', sys.stdout.write):
            CourseEnrollment.enroll(self.user, self.course_key, 'verified')
            cart = Order.get_cart_for_user(user=self.user)
            CertificateItem.add_to_order(cart, self.course_key, self.cost, 'verified')
            cart.purchase()
            CourseEnrollment.unenroll(self.user, self.course_key)

        target_certs = CertificateItem.objects.filter(course_id=self.course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertTrue(target_certs[0])
        self.assertTrue(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'refunded')
        self._assert_refund_tracked()

    def test_refund_cert_callback_before_expiration_email(self):
        """ Test that refund emails are being sent correctly. """
        course = CourseFactory.create()
        course_key = course.id
        many_days = datetime.timedelta(days=60)

        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=datetime.datetime.now(pytz.utc) + many_days)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        mail.outbox = []
        with patch('shoppingcart.models.log.error') as mock_error_logger:
            CourseEnrollment.unenroll(self.user, course_key)
            self.assertFalse(mock_error_logger.called)
            self.assertEquals(len(mail.outbox), 1)
            self.assertEquals('[Refund] User-Requested Refund', mail.outbox[0].subject)
            self.assertEquals(settings.PAYMENT_SUPPORT_EMAIL, mail.outbox[0].from_email)
            self.assertIn('has requested a refund on Order', mail.outbox[0].body)

    @patch('shoppingcart.models.log.error')
    def test_refund_cert_callback_before_expiration_email_error(self, error_logger):
        # If there's an error sending an email to billing, we need to log this error
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create()
        course_key = course.id

        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,
                                 expiration_datetime=datetime.datetime.now(pytz.utc) + many_days)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        with patch('shoppingcart.models.send_mail', side_effect=smtplib.SMTPException):
            CourseEnrollment.unenroll(self.user, course_key)
            self.assertTrue(error_logger.call_args[0][0].startswith('Failed sending email'))

    def test_refund_cert_callback_after_expiration(self):
        # If the expiration date has passed, the user cannot get a refund
        many_days = datetime.timedelta(days=60)

        course = CourseFactory.create()
        course_key = course.id
        course_mode = CourseMode(course_id=course_key,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=self.cost,)
        course_mode.save()

        CourseEnrollment.enroll(self.user, course_key, 'verified')
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, course_key, self.cost, 'verified')
        cart.purchase()

        course_mode.expiration_datetime = (datetime.datetime.now(pytz.utc) - many_days)
        course_mode.save()

        CourseEnrollment.unenroll(self.user, course_key)
        target_certs = CertificateItem.objects.filter(course_id=course_key, user_id=self.user, status='refunded', mode='verified')
        self.assertEqual(len(target_certs), 0)

    def test_refund_cert_no_cert_exists(self):
        # If there is no paid certificate, the refund callback should return nothing
        CourseEnrollment.enroll(self.user, self.course_key, 'verified')
        ret_val = CourseEnrollment.unenroll(self.user, self.course_key)
        self.assertFalse(ret_val)

    def test_no_id_prof_confirm_email(self):
        # Pay for a no-id-professional course
        course_mode = CourseMode(course_id=self.course_key,
                                 mode_slug="no-id-professional",
                                 mode_display_name="No Id Professional Cert",
                                 min_price=self.cost)
        course_mode.save()
        CourseEnrollment.enroll(self.user, self.course_key)
        cart = Order.get_cart_for_user(user=self.user)
        CertificateItem.add_to_order(cart, self.course_key, self.cost, 'no-id-professional')
        # verify that we are still enrolled
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course_key))
        self.mock_tracker.reset_mock()
        cart.purchase()
        enrollment = CourseEnrollment.objects.get(user=self.user, course_id=self.course_key)
        self.assertEquals(enrollment.mode, u'no-id-professional')

        # Check that the tax-deduction information appears in the confirmation email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEquals('Order Payment Confirmation', email.subject)
        self.assertNotIn("If you haven't verified your identity yet, please start the verification process", email.body)


class DonationTest(ModuleStoreTestCase):
    """Tests for the donation order item type. """

    COST = Decimal('23.45')

    def setUp(self):
        """Create a test user and order. """
        super(DonationTest, self).setUp()
        self.user = UserFactory.create()
        self.cart = Order.get_cart_for_user(self.user)

    def test_donate_to_org(self):
        # No course ID provided, so this is a donation to the entire organization
        donation = Donation.add_to_order(self.cart, self.COST)
        self._assert_donation(
            donation,
            donation_type="general",
            unit_cost=self.COST,
            line_desc="Donation for edX"
        )

    def test_donate_to_course(self):
        # Create a test course
        course = CourseFactory.create(display_name="Test Course")

        # Donate to the course
        donation = Donation.add_to_order(self.cart, self.COST, course_id=course.id)
        self._assert_donation(
            donation,
            donation_type="course",
            course_id=course.id,
            unit_cost=self.COST,
            line_desc=u"Donation for Test Course"
        )

    def test_confirmation_email(self):
        # Pay for a donation
        Donation.add_to_order(self.cart, self.COST)
        self.cart.start_purchase()
        self.cart.purchase()

        # Check that the tax-deduction information appears in the confirmation email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEquals('Order Payment Confirmation', email.subject)
        self.assertIn("tax purposes", email.body)

    def test_donate_no_such_course(self):
        fake_course_id = CourseLocator(org="edx", course="fake", run="course")
        with self.assertRaises(CourseDoesNotExistException):
            Donation.add_to_order(self.cart, self.COST, course_id=fake_course_id)

    def _assert_donation(self, donation, donation_type=None, course_id=None, unit_cost=None, line_desc=None):
        """Verify the donation fields and that the donation can be purchased. """
        self.assertEqual(donation.order, self.cart)
        self.assertEqual(donation.user, self.user)
        self.assertEqual(donation.donation_type, donation_type)
        self.assertEqual(donation.course_id, course_id)
        self.assertEqual(donation.qty, 1)
        self.assertEqual(donation.unit_cost, unit_cost)
        self.assertEqual(donation.currency, "usd")
        self.assertEqual(donation.line_desc, line_desc)

        # Verify that the donation is in the cart
        self.assertTrue(self.cart.has_items(item_type=Donation))
        self.assertEqual(self.cart.total_cost, unit_cost)

        # Purchase the item
        self.cart.start_purchase()
        self.cart.purchase()

        # Verify that the donation is marked as purchased
        donation = Donation.objects.get(pk=donation.id)
        self.assertEqual(donation.status, "purchased")


class InvoiceHistoryTest(TestCase):
    """Tests for the InvoiceHistory model. """

    INVOICE_INFO = {
        'is_valid': True,
        'internal_reference': 'Test Internal Ref Num',
        'customer_reference_number': 'Test Customer Ref Num',
    }

    CONTACT_INFO = {
        'company_name': 'Test Company',
        'company_contact_name': 'Test Company Contact Name',
        'company_contact_email': 'test-contact@example.com',
        'recipient_name': 'Test Recipient Name',
        'recipient_email': 'test-recipient@example.com',
        'address_line_1': 'Test Address 1',
        'address_line_2': 'Test Address 2',
        'address_line_3': 'Test Address 3',
        'city': 'Test City',
        'state': 'Test State',
        'zip': '12345',
        'country': 'US',
    }

    def setUp(self):
        super(InvoiceHistoryTest, self).setUp()
        invoice_data = copy.copy(self.INVOICE_INFO)
        invoice_data.update(self.CONTACT_INFO)
        self.course_key = CourseLocator('edX', 'DemoX', 'Demo_Course')
        self.invoice = Invoice.objects.create(total_amount="123.45", course_id=self.course_key, **invoice_data)
        self.user = UserFactory.create()

    def test_get_invoice_total_amount(self):
        """
        test to check the total amount
        of the invoices for the course.
        """
        total_amount = Invoice.get_invoice_total_amount_for_course(self.course_key)
        self.assertEqual(total_amount, 123.45)

    def test_get_total_amount_of_paid_invoices(self):
        """
        Test to check the Invoice Transactions amount.
        """
        InvoiceTransaction.objects.create(
            invoice=self.invoice,
            amount='123.45',
            currency='usd',
            comments='test comments',
            status='completed',
            created_by=self.user,
            last_modified_by=self.user
        )
        total_amount_paid = InvoiceTransaction.get_total_amount_of_paid_course_invoices(self.course_key)
        self.assertEqual(float(total_amount_paid), 123.45)

    def test_get_total_amount_of_no_invoices(self):
        """
        Test to check the Invoice Transactions amount.
        """
        total_amount_paid = InvoiceTransaction.get_total_amount_of_paid_course_invoices(self.course_key)
        self.assertEqual(float(total_amount_paid), 0)

    def test_invoice_contact_info_history(self):
        self._assert_history_invoice_info(
            is_valid=True,
            internal_ref=self.INVOICE_INFO['internal_reference'],
            customer_ref=self.INVOICE_INFO['customer_reference_number']
        )
        self._assert_history_contact_info(**self.CONTACT_INFO)
        self._assert_history_items([])
        self._assert_history_transactions([])

    def test_invoice_generated_registration_codes(self):
        """
        test filter out the registration codes
        that were generated via Invoice.
        """
        invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.invoice,
            qty=5,
            unit_price='123.45',
            course_id=self.course_key
        )
        for i in range(5):
            CourseRegistrationCode.objects.create(
                code='testcode{counter}'.format(counter=i),
                course_id=self.course_key,
                created_by=self.user,
                invoice=self.invoice,
                invoice_item=invoice_item,
                mode_slug='honor'
            )

        registration_codes = CourseRegistrationCode.invoice_generated_registration_codes(self.course_key)
        self.assertEqual(registration_codes.count(), 5)

    def test_invoice_history_items(self):
        # Create an invoice item
        CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.invoice,
            qty=1,
            unit_price='123.45',
            course_id=self.course_key
        )
        self._assert_history_items([{
            'qty': 1,
            'unit_price': '123.45',
            'currency': 'usd',
            'course_id': unicode(self.course_key)
        }])

        # Create a second invoice item
        CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.invoice,
            qty=2,
            unit_price='456.78',
            course_id=self.course_key
        )
        self._assert_history_items([
            {
                'qty': 1,
                'unit_price': '123.45',
                'currency': 'usd',
                'course_id': unicode(self.course_key)
            },
            {
                'qty': 2,
                'unit_price': '456.78',
                'currency': 'usd',
                'course_id': unicode(self.course_key)
            }
        ])

    def test_invoice_history_transactions(self):
        # Create an invoice transaction
        first_transaction = InvoiceTransaction.objects.create(
            invoice=self.invoice,
            amount='123.45',
            currency='usd',
            comments='test comments',
            status='completed',
            created_by=self.user,
            last_modified_by=self.user
        )
        self._assert_history_transactions([{
            'amount': '123.45',
            'currency': 'usd',
            'comments': 'test comments',
            'status': 'completed',
            'created_by': self.user.username,
            'last_modified_by': self.user.username,
        }])

        # Create a second invoice transaction
        second_transaction = InvoiceTransaction.objects.create(
            invoice=self.invoice,
            amount='456.78',
            currency='usd',
            comments='test more comments',
            status='started',
            created_by=self.user,
            last_modified_by=self.user
        )
        self._assert_history_transactions([
            {
                'amount': '123.45',
                'currency': 'usd',
                'comments': 'test comments',
                'status': 'completed',
                'created_by': self.user.username,
                'last_modified_by': self.user.username,
            },
            {
                'amount': '456.78',
                'currency': 'usd',
                'comments': 'test more comments',
                'status': 'started',
                'created_by': self.user.username,
                'last_modified_by': self.user.username,
            }
        ])

        # Delete the transactions
        first_transaction.delete()
        second_transaction.delete()
        self._assert_history_transactions([])

    def _assert_history_invoice_info(self, is_valid=True, customer_ref=None, internal_ref=None):
        """Check top-level invoice information in the latest history record. """
        latest = self._latest_history()
        self.assertEqual(latest['is_valid'], is_valid)
        self.assertEqual(latest['customer_reference'], customer_ref)
        self.assertEqual(latest['internal_reference'], internal_ref)

    def _assert_history_contact_info(self, **kwargs):
        """Check contact info in the latest history record. """
        contact_info = self._latest_history()['contact_info']
        for key, value in kwargs.iteritems():
            self.assertEqual(contact_info[key], value)

    def _assert_history_items(self, expected_items):
        """Check line item info in the latest history record. """
        items = self._latest_history()['items']
        self.assertItemsEqual(items, expected_items)

    def _assert_history_transactions(self, expected_transactions):
        """Check transactions (payments/refunds) in the latest history record. """
        transactions = self._latest_history()['transactions']
        self.assertItemsEqual(transactions, expected_transactions)

    def _latest_history(self):
        """Retrieve the snapshot from the latest history record. """
        latest = InvoiceHistory.objects.latest()
        return json.loads(latest.snapshot)
