"""
Tests for PaymentTransaction related models and logic
"""
import datetime
import uuid

import pytz
from django.conf import settings
from django.test.utils import override_settings
from django.db import IntegrityError

from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory

from shoppingcart.models import (
    Order, PaidCourseRegistration, PaymentTransaction,
    TRANSACTION_TYPE_PURCHASE, TRANSACTION_TYPE_REFUND,
    PaymentTransactionCourseMap
)
from student.tests.factories import UserFactory
from course_modes.models import CourseMode
from shoppingcart.exceptions import (
    OrderDoesNotExistException
)

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class PaymentTransactionModelTests(ModuleStoreTestCase):
    """
    This test class will perform unit tests on the models regarding
    the PaymentTransaction
    """
    def setUp(self):
        """
        Set up testing environment
        """
        self.user = UserFactory.create()
        self.user2 = UserFactory.create()

        self.cost = 40
        self.course = CourseFactory.create()
        self.course_key = self.course.id
        self.course_mode = CourseMode(
            course_id=self.course_key,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=self.cost
        )
        self.course_mode.save()

        self.course2 = CourseFactory.create()
        self.course_key2 = self.course2.id
        self.cost2 = 100
        self.course_mode2 = CourseMode(
            course_id=self.course_key2,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=self.cost2
        )
        self.course_mode2.save()

        self.order1 = Order.get_cart_for_user(self.user)
        self.order_item1 = PaidCourseRegistration.add_to_order(self.order1, self.course_key)
        self.order1.purchase()

    def test_create_new_transaction(self):
        """
        Happy path testing of a new transaction
        """
        transaction = PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            self.order1.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        # look up directly in database and assert that they are the same
        saved_transaction = PaymentTransaction.objects.get(
            remote_transaction_id=transaction.remote_transaction_id
        )
        self.assertEqual(transaction, saved_transaction)

        # then make sure there we can query against the mappings to the course
        queryset = PaymentTransaction.get_transactions_for_course(self.course_key)
        self.assertEqual(len(queryset), 1)
        self.assertEqual(queryset[0].transaction, transaction)

        queryset = PaymentTransaction.get_transactions_for_course(
            self.course_key, transaction_type=TRANSACTION_TYPE_PURCHASE,
        )
        self.assertEqual(len(queryset), 1)
        self.assertEqual(queryset[0].transaction, transaction)

        queryset = PaymentTransaction.get_transactions_for_course(
            self.course_key, transaction_type=TRANSACTION_TYPE_REFUND,
        )
        self.assertEqual(len(queryset), 0)

        # check some of the totals
        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key)
        self.assertEqual(amounts['purchased'], self.cost)
        self.assertEqual(amounts['refunded'], 0.0)

    def test_multiple_transactions(self):
        """
        Similar happy path, but with multiple purchases, let's make sure the aggregate queries are correct.
        Interleave transactions between courses to make sure the GROUP BY is working as expected
        """
        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            self.order1.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        order2 = Order.get_cart_for_user(self.user2)
        PaidCourseRegistration.add_to_order(order2, self.course_key2)
        order2.purchase()

        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            order2.id,
            'USD',
            self.cost2,
            TRANSACTION_TYPE_PURCHASE
        )

        order3 = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(order3, self.course_key2)
        order3.purchase()

        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            order3.id,
            'USD',
            self.cost2,
            TRANSACTION_TYPE_PURCHASE
        )

        order4 = Order.get_cart_for_user(self.user2)
        PaidCourseRegistration.add_to_order(order4, self.course_key)
        order4.purchase()

        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            order4.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        # add one refund transaction
        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            order4.id,
            'USD',
            -self.cost,
            TRANSACTION_TYPE_REFUND
        )

        # check some of the totals
        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key)
        self.assertEqual(amounts['purchased'], 2.0 * self.cost)
        self.assertEqual(amounts['refunded'], -self.cost)

        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key2)
        self.assertEqual(amounts['purchased'], 2.0 * self.cost2)
        self.assertEqual(amounts['refunded'], 0.0)

        # check some various time slices
        yesterday = datetime.datetime.now(pytz.UTC) - datetime.timedelta(1)
        day_before = datetime.datetime.now(pytz.UTC) - datetime.timedelta(2)
        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key, day_before, yesterday)
        self.assertEqual(amounts['purchased'], 0.0)
        self.assertEqual(amounts['refunded'], 0.0)

        tomorrow = datetime.datetime.now(pytz.UTC) + datetime.timedelta(1)
        day_after = datetime.datetime.now(pytz.UTC) + datetime.timedelta(2)
        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key, tomorrow, day_after)
        self.assertEqual(amounts['purchased'], 0.0)
        self.assertEqual(amounts['refunded'], 0.0)

        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key, yesterday, day_after)
        self.assertEqual(amounts['purchased'], 2.0 * self.cost)
        self.assertEqual(amounts['refunded'], -self.cost)

    def test_multiple_courses(self):
        """
        Verify the aggregates when Orders contain more than one OrderItem for multiple courses
        """
        order = Order.get_cart_for_user(self.user2)
        PaidCourseRegistration.add_to_order(order, self.course_key)
        PaidCourseRegistration.add_to_order(order, self.course_key2)
        order.purchase()

        PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            order.id,
            'USD',
            self.cost + self.cost2,
            TRANSACTION_TYPE_PURCHASE
        )

        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key)
        self.assertEqual(amounts['purchased'], self.cost)
        self.assertEqual(amounts['refunded'], 0.0)

        amounts = PaymentTransaction.get_transaction_totals_for_course(self.course_key2)
        self.assertEqual(amounts['purchased'], self.cost2)
        self.assertEqual(amounts['refunded'], 0.0)

    def test_non_purchased(self):
        """
        Verifies that we cannot save a new Transaction for an Order that has not been 'purchased'
        """
        order = Order.get_cart_for_user(self.user2)
        PaidCourseRegistration.add_to_order(order, self.course_key)

        transaction_id = uuid.uuid4()
        with self.assertRaises(Exception):
            PaymentTransaction.create(
                transaction_id,
                uuid.uuid4(),
                datetime.datetime.now(pytz.UTC),
                order.id,
                'USD',
                self.cost,
                TRANSACTION_TYPE_PURCHASE
            )

        # make sure that the transaction did not save
        self.assertFalse(PaymentTransaction.objects.filter(remote_transaction_id=transaction_id).exists())

    def test_bad_amount(self):
        """
        Verifies that we cannot save a new Transaction for an Order which does not match the total on the Order
        """
        transaction_id = uuid.uuid4()
        with self.assertRaises(Exception):
            PaymentTransaction.create(
                transaction_id,
                uuid.uuid4(),
                datetime.datetime.now(pytz.UTC),
                self.order1.id,
                'USD',
                self.cost + 1.0,
                TRANSACTION_TYPE_PURCHASE
            )

        # make sure that the transaction did not save
        self.assertFalse(PaymentTransaction.objects.filter(remote_transaction_id=transaction_id).exists())

    def test_bad_order_id(self):
        """
        Verifies that we cannot create a transaction for an order that does not exist
        """
        transaction_id = uuid.uuid4()
        with self.assertRaises(OrderDoesNotExistException):
            PaymentTransaction.create(
                transaction_id,
                uuid.uuid4(),
                datetime.datetime.now(pytz.UTC),
                0,
                'USD',
                self.cost,
                TRANSACTION_TYPE_PURCHASE
            )

        # make sure that the transaction did not save
        self.assertFalse(PaymentTransaction.objects.filter(remote_transaction_id=transaction_id).exists())

    def test_duplicate_same_transactions(self):
        """
        Test that we can create two transactions with the same primary key *AND* the same data
        """
        transaction = PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            self.order1.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        # look up directly in database and assert that they are the same
        saved_transaction = PaymentTransaction.objects.get(
            remote_transaction_id=transaction.remote_transaction_id
        )
        self.assertEqual(transaction, saved_transaction)

        saved_transaction2 = PaymentTransaction.create(
            transaction.remote_transaction_id,
            transaction.account_id,
            transaction.processed_at,
            transaction.order.id,  # pylint: disable=no-member
            transaction.currency,
            transaction.amount,
            transaction.transaction_type
        )

        # these should be the same
        self.assertEqual(saved_transaction, saved_transaction2)

    def test_duplicate_different_transactions(self):
        """
        Test that we cannot create two transactions with the same primary key
        """
        transaction = PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            self.order1.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        # look up directly in database and assert that they are the same
        saved_transaction = PaymentTransaction.objects.get(
            remote_transaction_id=transaction.remote_transaction_id
        )
        self.assertEqual(transaction, saved_transaction)

        with self.assertRaises(IntegrityError):
            PaymentTransaction.create(
                transaction.remote_transaction_id,
                uuid.uuid4(),
                datetime.datetime.now(pytz.UTC),
                self.order1.id,
                'USD',
                self.cost,
                TRANSACTION_TYPE_PURCHASE
            )

    def test_course_mapping_uniqueness(self):
        """
        Make sure we can't have multiple mappings of a transaction to the same course
        """

        transaction = PaymentTransaction.create(
            uuid.uuid4(),
            uuid.uuid4(),
            datetime.datetime.now(pytz.UTC),
            self.order1.id,
            'USD',
            self.cost,
            TRANSACTION_TYPE_PURCHASE
        )

        mapping = PaymentTransactionCourseMap(
            transaction=transaction,
            course_id=self.course_key,
            order_item=self.order_item1
        )

        # we should not be able to do this
        with self.assertRaises(IntegrityError):
            mapping.save()
