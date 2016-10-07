"""
Tests for Shopping Cart views
"""
from collections import OrderedDict
import pytz
from urlparse import urlparse
from decimal import Decimal
import json

from django.http import HttpRequest
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail

from django.core.cache import cache
from pytz import UTC
from freezegun import freeze_time
from datetime import datetime, timedelta
from mock import patch, Mock
from nose.plugins.attrib import attr
import ddt

from common.test.utils import XssTestMixin
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.roles import CourseSalesAdminRole
from util.date_utils import get_default_time_display
from util.testing import UrlResetMixin

from shoppingcart.views import _can_download_report, _get_date_from_str
from shoppingcart.models import (
    Order, CertificateItem, PaidCourseRegistration, CourseRegCodeItem,
    Coupon, CourseRegistrationCode, RegistrationCodeRedemption,
    DonationConfiguration,
    CouponRedemption)
from student.tests.factories import UserFactory, AdminFactory, CourseModeFactory
from courseware.tests.factories import InstructorFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from openedx.core.djangoapps.edxmako.shortcuts import render_to_response
from embargo.test_utils import restrict_course
from shoppingcart.processors import render_purchase_form_html
from shoppingcart.admin import SoftDeleteCouponAdmin
from shoppingcart.views import initialize_report
from shoppingcart.tests.payment_fake import PaymentFakeView
from shoppingcart.processors.CyberSource2 import sign


def mock_render_purchase_form_html(*args, **kwargs):
    return render_purchase_form_html(*args, **kwargs)

form_mock = Mock(side_effect=mock_render_purchase_form_html)


def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)

postpay_mock = Mock()


@attr(shard=3)
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
@ddt.ddt
class ShoppingCartViewsTests(SharedModuleStoreTestCase, XssTestMixin):
    """
    Test shopping cart view under various states
    """

    @classmethod
    def setUpClass(cls):
        super(ShoppingCartViewsTests, cls).setUpClass()
        cls.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        cls.course_key = cls.course.id

        verified_course = CourseFactory.create(org='org', number='test', display_name='Test Course')
        cls.verified_course_key = verified_course.id

        xss_course = CourseFactory.create(org='xssorg', number='test', display_name='<script>alert("XSS")</script>')
        cls.xss_course_key = xss_course.id

        cls.testing_course = CourseFactory.create(org='edX', number='888', display_name='Testing Super Course')

    def setUp(self):
        super(ShoppingCartViewsTests, self).setUp()

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.instructor = AdminFactory.create()
        self.cost = 40
        self.coupon_code = 'abcde'
        self.reg_code = 'qwerty'
        self.percentage_discount = 10
        self.course_mode = CourseMode(
            course_id=self.course_key,
            mode_slug=CourseMode.HONOR,
            mode_display_name="honor cert",
            min_price=self.cost
        )
        self.course_mode.save()

        # Saving another testing course mode
        self.testing_cost = 20
        self.testing_course_mode = CourseMode(
            course_id=self.testing_course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name="testing honor cert",
            min_price=self.testing_cost
        )
        self.testing_course_mode.save()

        # And for the XSS course
        CourseMode(
            course_id=self.xss_course_key,
            mode_slug=CourseMode.HONOR,
            mode_display_name="honor cert",
            min_price=self.cost
        ).save()

        # And the verified course
        self.verified_course_mode = CourseMode(
            course_id=self.verified_course_key,
            mode_slug=CourseMode.HONOR,
            mode_display_name="honor cert",
            min_price=self.cost
        )
        self.verified_course_mode.save()

        self.cart = Order.get_cart_for_user(self.user)

        self.addCleanup(patcher.stop)

        self.now = datetime.now(pytz.UTC)
        self.yesterday = self.now - timedelta(days=1)
        self.tomorrow = self.now + timedelta(days=1)

    def get_discount(self, cost):
        """
        This method simple return the discounted amount
        """
        val = Decimal("{0:.2f}".format(Decimal(self.percentage_discount / 100.00) * cost))
        return cost - val

    def add_coupon(self, course_key, is_active, code):
        """
        add dummy coupon into models
        """
        coupon = Coupon(code=code, description='testing code', course_id=course_key,
                        percentage_discount=self.percentage_discount, created_by=self.user, is_active=is_active)
        coupon.save()

    def add_reg_code(self, course_key, mode_slug=None, is_valid=True):
        """
        add dummy registration code into models
        """
        if mode_slug is None:
            mode_slug = self.course_mode.mode_slug
        course_reg_code = CourseRegistrationCode(
            code=self.reg_code, course_id=course_key,
            created_by=self.user, mode_slug=mode_slug,
            is_valid=is_valid
        )
        course_reg_code.save()

    def _add_course_mode(self, min_price=50, mode_slug='honor', expiration_date=None):
        """
        Adds a course mode to the test course.
        """
        mode = CourseModeFactory.create()
        mode.course_id = self.course.id
        mode.min_price = min_price
        mode.mode_slug = mode_slug
        mode.expiration_date = expiration_date
        mode.save()
        return mode

    def add_course_to_user_cart(self, course_key):
        """
        adding course to user cart
        """
        self.login_user()
        reg_item = PaidCourseRegistration.add_to_order(self.cart, course_key, mode_slug=self.course_mode.mode_slug)
        return reg_item

    def login_user(self):
        self.client.login(username=self.user.username, password="password")

    def test_add_course_to_cart_anon(self):
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 403)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_billing_details(self):
        billing_url = reverse('billing_details')
        self.login_user()

        # page not found error because order_type is not business
        resp = self.client.get(billing_url)
        self.assertEqual(resp.status_code, 404)

        #chagne the order_type to business
        self.cart.order_type = 'business'
        self.cart.save()
        resp = self.client.get(billing_url)
        self.assertEqual(resp.status_code, 200)

        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/billing_details.html')
        # check for the default currency in the context
        self.assertEqual(context['currency'], 'usd')
        self.assertEqual(context['currency_symbol'], '$')

        data = {'company_name': 'Test Company', 'company_contact_name': 'JohnDoe',
                'company_contact_email': 'john@est.com', 'recipient_name': 'Mocker',
                'recipient_email': 'mock@germ.com', 'company_address_line_1': 'DC Street # 1',
                'company_address_line_2': '',
                'company_city': 'DC', 'company_state': 'NY', 'company_zip': '22003', 'company_country': 'US',
                'customer_reference_number': 'PO#23'}

        resp = self.client.post(billing_url, data)
        self.assertEqual(resp.status_code, 200)

    @patch('shoppingcart.views.render_to_response', render_mock)
    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=['PKR', 'Rs'])
    def test_billing_details_with_override_currency_settings(self):
        billing_url = reverse('billing_details')
        self.login_user()

        #chagne the order_type to business
        self.cart.order_type = 'business'
        self.cart.save()
        resp = self.client.get(billing_url)
        self.assertEqual(resp.status_code, 200)

        ((template, context), __) = render_mock.call_args  # pylint: disable=redefined-outer-name

        self.assertEqual(template, 'shoppingcart/billing_details.html')
        # check for the override currency settings in the context
        self.assertEqual(context['currency'], 'PKR')
        self.assertEqual(context['currency_symbol'], 'Rs')

    def test_same_coupon_code_applied_on_multiple_items_in_the_cart(self):
        """
        test to check that that the same coupon code applied on multiple
        items in the cart.
        """

        self.login_user()
        # add first course to user cart
        resp = self.client.post(
            reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()])
        )
        self.assertEqual(resp.status_code, 200)
        # add and apply the coupon code to course in the cart
        self.add_coupon(self.course_key, True, self.coupon_code)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # now add the same coupon code to the second course(testing_course)
        self.add_coupon(self.testing_course.id, True, self.coupon_code)
        #now add the second course to cart, the coupon code should be
        # applied when adding the second course to the cart
        resp = self.client.post(
            reverse('shoppingcart.views.add_course_to_cart', args=[self.testing_course.id.to_deprecated_string()])
        )
        self.assertEqual(resp.status_code, 200)
        #now check the user cart and see that the discount has been applied on both the courses
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        #first course price is 40$ and the second course price is 20$
        # after 10% discount on both the courses the total price will be 18+36 = 54
        self.assertIn('54.00', resp.content)

    def test_add_course_to_cart_already_in_cart(self):
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('The course {0} is already in your cart.'.format(self.course_key.to_deprecated_string()), resp.content)

    def test_course_discount_invalid_coupon(self):
        self.add_coupon(self.course_key, True, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)
        non_existing_code = "non_existing_code"
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': non_existing_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Discount does not exist against code '{0}'.".format(non_existing_code), resp.content)

    def test_valid_qty_greater_then_one_and_purchase_type_should_business(self):
        qty = 2
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['total_cost'], item.unit_cost * qty)
        cart = Order.get_cart_for_user(self.user)
        self.assertEqual(cart.order_type, 'business')

    def test_in_valid_qty_case(self):
        # invalid quantity, Quantity must be between 1 and 1000.
        qty = 0
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Quantity must be between 1 and 1000.", resp.content)

        # invalid quantity, Quantity must be an integer.
        qty = 'abcde'
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Quantity must be an integer.", resp.content)

        # invalid quantity, Quantity is not present in request
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Quantity must be between 1 and 1000.", resp.content)

    def test_valid_qty_but_item_not_found(self):
        qty = 2
        item_id = '-1'
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item_id, 'qty': qty})
        self.assertEqual(resp.status_code, 404)
        self.assertEqual('Order item does not exist.', resp.content)

        # now testing the case if item id not found in request,
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'qty': qty})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual('Order item not found in request.', resp.content)

    def test_purchase_type_should_be_personal_when_qty_is_one(self):
        qty = 1
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['total_cost'], item.unit_cost * 1)
        cart = Order.get_cart_for_user(self.user)
        self.assertEqual(cart.order_type, 'personal')

    def test_purchase_type_on_removing_item_and_cart_has_item_with_qty_one(self):
        qty = 5
        self.add_course_to_user_cart(self.course_key)
        item2 = self.add_course_to_user_cart(self.testing_course.id)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item2.id, 'qty': qty})
        self.assertEqual(resp.status_code, 200)
        cart = Order.get_cart_for_user(self.user)
        cart_items = cart.orderitem_set.all()
        test_flag = False
        for cartitem in cart_items:
            if cartitem.qty == 5:
                test_flag = True
                resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]), {'id': cartitem.id})
                self.assertEqual(resp.status_code, 200)
        self.assertTrue(test_flag)

        cart = Order.get_cart_for_user(self.user)
        self.assertEqual(cart.order_type, 'personal')

    def test_billing_details_btn_in_cart_when_qty_is_greater_than_one(self):
        qty = 5
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertIn("Billing Details", resp.content)

    def test_purchase_type_should_be_personal_when_remove_all_items_from_cart(self):
        item1 = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item1.id, 'qty': 2})
        self.assertEqual(resp.status_code, 200)

        item2 = self.add_course_to_user_cart(self.testing_course.id)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item2.id, 'qty': 5})
        self.assertEqual(resp.status_code, 200)

        cart = Order.get_cart_for_user(self.user)
        cart_items = cart.orderitem_set.all()
        test_flag = False
        for cartitem in cart_items:
            test_flag = True
            resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]), {'id': cartitem.id})
            self.assertEqual(resp.status_code, 200)
        self.assertTrue(test_flag)

        cart = Order.get_cart_for_user(self.user)
        self.assertEqual(cart.order_type, 'personal')

    def test_use_valid_coupon_code_and_qty_is_greater_than_one(self):
        qty = 5
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': qty})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['total_cost'], item.unit_cost * qty)

        # use coupon code
        self.add_coupon(self.course_key, True, self.coupon_code)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        self.assertEquals(item.unit_cost * qty, 180)

    def test_course_discount_invalid_reg_code(self):
        self.add_reg_code(self.course_key)
        self.add_course_to_user_cart(self.course_key)
        non_existing_code = "non_existing_code"
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': non_existing_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Discount does not exist against code '{0}'.".format(non_existing_code), resp.content)

    def test_course_discount_inactive_coupon(self):
        self.add_coupon(self.course_key, False, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Discount does not exist against code '{0}'.".format(self.coupon_code), resp.content)

    def test_course_does_not_exist_in_cart_against_valid_coupon(self):
        course_key = self.course_key.to_deprecated_string() + 'testing'
        self.add_coupon(course_key, True, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Discount does not exist against code '{0}'.".format(self.coupon_code), resp.content)

    def test_inactive_registration_code_returns_error(self):
        """
        test to redeem inactive registration code and
        it returns an error.
        """
        course_key = self.course_key.to_deprecated_string()
        self.add_reg_code(course_key, is_valid=False)
        self.add_course_to_user_cart(self.course_key)

        # now apply the inactive registration code
        # it will raise an exception
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn(
            "This enrollment code ({enrollment_code}) is no longer valid.".format(
                enrollment_code=self.reg_code), resp.content)

    def test_course_does_not_exist_in_cart_against_valid_reg_code(self):
        course_key = self.course_key.to_deprecated_string() + 'testing'
        self.add_reg_code(course_key)
        self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Code '{0}' is not valid for any course in the shopping cart.".format(self.reg_code), resp.content)

    def test_cart_item_qty_greater_than_1_against_valid_reg_code(self):
        course_key = self.course_key.to_deprecated_string()
        self.add_reg_code(course_key)
        item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': 4})
        self.assertEqual(resp.status_code, 200)
        # now update the cart item quantity and then apply the registration code
        # it will raise an exception
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Cart item quantity should not be greater than 1 when applying activation code", resp.content)

    @ddt.data(True, False)
    def test_reg_code_uses_associated_mode(self, expired_mode):
        """Tests the use of reg codes on verified courses, expired or active. """
        course_key = self.course_key.to_deprecated_string()
        expiration_date = self.yesterday if expired_mode else self.tomorrow
        self._add_course_mode(mode_slug='verified', expiration_date=expiration_date)
        self.add_reg_code(course_key, mode_slug='verified')
        self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('register_code_redemption', args=[self.reg_code]), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.course.display_name, resp.content)

    @ddt.data(True, False)
    def test_reg_code_uses_unknown_mode(self, expired_mode):
        """Tests the use of reg codes on verified courses, expired or active. """
        course_key = self.course_key.to_deprecated_string()
        expiration_date = self.yesterday if expired_mode else self.tomorrow
        self._add_course_mode(mode_slug='verified', expiration_date=expiration_date)
        self.add_reg_code(course_key, mode_slug='bananas')
        self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('register_code_redemption', args=[self.reg_code]), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.course.display_name, resp.content)
        self.assertIn("error processing your redeem code", resp.content)

    def test_course_discount_for_valid_active_coupon_code(self):

        self.add_coupon(self.course_key, True, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit price should be updated for that course
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        self.assertEquals(item.unit_cost, self.get_discount(self.cost))

        # after getting 10 percent discount
        self.assertEqual(self.cart.total_cost, self.get_discount(self.cost))

        # now using the same coupon code against the same order.
        # Only one coupon redemption should be allowed per order.
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Only one coupon redemption is allowed against an order", resp.content)

    def test_course_discount_against_two_distinct_coupon_codes(self):

        self.add_coupon(self.course_key, True, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit price should be updated for that course
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        self.assertEquals(item.unit_cost, self.get_discount(self.cost))

        # now using another valid active coupon code.
        # Only one coupon redemption should be allowed per order.
        self.add_coupon(self.course_key, True, 'abxyz')
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': 'abxyz'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Only one coupon redemption is allowed against an order", resp.content)

    def test_same_coupons_code_on_multiple_courses(self):

        # add two same coupon codes on two different courses
        self.add_coupon(self.course_key, True, self.coupon_code)
        self.add_coupon(self.testing_course.id, True, self.coupon_code)
        self.add_course_to_user_cart(self.course_key)
        self.add_course_to_user_cart(self.testing_course.id)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit price should be updated for that course
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        self.assertEquals(item.unit_cost, self.get_discount(self.cost))

        item = self.cart.orderitem_set.all().select_subclasses()[1]
        self.assertEquals(item.unit_cost, self.get_discount(self.testing_cost))

    def test_soft_delete_coupon(self):
        self.add_coupon(self.course_key, True, self.coupon_code)
        coupon = Coupon(code='TestCode', description='testing', course_id=self.course_key,
                        percentage_discount=12, created_by=self.user, is_active=True)
        coupon.save()
        self.assertEquals(coupon.__unicode__(), '[Coupon] code: TestCode course: MITx/999/Robot_Super_Course')
        admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        admin.is_staff = True
        get_coupon = Coupon.objects.get(id=1)
        request = HttpRequest()
        request.user = admin
        request.session = 'session'
        messages = FallbackStorage(request)
        request._messages = messages        # pylint: disable=protected-access
        coupon_admin = SoftDeleteCouponAdmin(Coupon, AdminSite())
        test_query_set = coupon_admin.queryset(request)
        test_actions = coupon_admin.get_actions(request)
        self.assertIn('really_delete_selected', test_actions['really_delete_selected'])
        self.assertEqual(get_coupon.is_active, True)
        coupon_admin.really_delete_selected(request, test_query_set)
        for coupon in test_query_set:
            self.assertEqual(coupon.is_active, False)
        coupon_admin.delete_model(request, get_coupon)
        self.assertEqual(get_coupon.is_active, False)

        coupon = Coupon(code='TestCode123', description='testing123', course_id=self.course_key,
                        percentage_discount=22, created_by=self.user, is_active=True)
        coupon.save()
        test_query_set = coupon_admin.queryset(request)
        coupon_admin.really_delete_selected(request, test_query_set)
        for coupon in test_query_set:
            self.assertEqual(coupon.is_active, False)

    def test_course_free_discount_for_valid_active_reg_code(self):
        self.add_reg_code(self.course_key)
        self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 200)

        redeem_url = reverse('register_code_redemption', args=[self.reg_code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        # now testing registration code already used scenario, reusing the same code
        # the item has been removed when using the registration code for the first time
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("This enrollment code ({enrollment_code}) is not valid.".format(
            enrollment_code=self.reg_code
        ), resp.content)

    def test_upgrade_from_valid_reg_code(self):
        """Use a valid registration code to upgrade from honor to verified mode. """
        # Ensure the course has a verified mode
        course_key = self.course_key.to_deprecated_string()
        self._add_course_mode(mode_slug='verified')
        self.add_reg_code(course_key, mode_slug='verified')

        # Enroll as honor in the course with the current user.
        CourseEnrollment.enroll(self.user, self.course_key, mode=CourseMode.HONOR)
        self.login_user()
        current_enrollment, __ = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_key)
        self.assertEquals('honor', current_enrollment)

        redeem_url = reverse('register_code_redemption', args=[self.reg_code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

        # Once upgraded, should be "verified"
        current_enrollment, __ = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_key)
        self.assertEquals('verified', current_enrollment)

    @patch('shoppingcart.views.log.debug')
    def test_non_existing_coupon_redemption_on_removing_item(self, debug_log):

        reg_item = self.add_course_to_user_cart(self.course_key)
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})
        debug_log.assert_called_with(
            'Code redemption does not exist for order item id=%s.',
            str(reg_item.id)
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)

    @patch('shoppingcart.views.log.info')
    def test_existing_coupon_redemption_on_removing_item(self, info_log):

        self.add_coupon(self.course_key, True, self.coupon_code)
        reg_item = self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)
        info_log.assert_called_with(
            'Coupon "%s" redemption entry removed for user "%s" for order item "%s"',
            self.coupon_code,
            self.user,
            str(reg_item.id)
        )

    @patch('shoppingcart.views.log.info')
    def test_reset_redemption_for_coupon(self, info_log):

        self.add_coupon(self.course_key, True, self.coupon_code)
        reg_item = self.add_course_to_user_cart(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse('shoppingcart.views.reset_code_redemption', args=[]))

        self.assertEqual(resp.status_code, 200)
        info_log.assert_called_with(
            'Coupon redemption entry removed for user %s for order %s',
            self.user,
            reg_item.id
        )

    @patch('shoppingcart.views.log.info')
    def test_coupon_discount_for_multiple_courses_in_cart(self, info_log):

        reg_item = self.add_course_to_user_cart(self.course_key)
        self.add_coupon(self.course_key, True, self.coupon_code)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit_cost should be updated for that particular course for which coupon code is registered
        items = self.cart.orderitem_set.all().select_subclasses()
        for item in items:
            if item.id == reg_item.id:
                self.assertEquals(item.unit_cost, self.get_discount(self.cost))
                self.assertEquals(item.list_price, self.cost)
            elif item.id == cert_item.id:
                self.assertEquals(item.list_price, self.cost)
                self.assertEquals(item.unit_cost, self.cost)

        # Delete the discounted item, corresponding coupon redemption should
        # be removed for that particular discounted item
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        info_log.assert_called_with(
            'Coupon "%s" redemption entry removed for user "%s" for order item "%s"',
            self.coupon_code,
            self.user,
            str(reg_item.id)
        )

    @patch('shoppingcart.views.log.info')
    def test_delete_certificate_item(self, info_log):

        self.add_course_to_user_cart(self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        # Delete the discounted item, corresponding coupon redemption should be removed for that particular discounted item
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': cert_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        info_log.assert_called_with("order item %s removed for user %s", str(cert_item.id), self.user)

    @patch('shoppingcart.views.log.info')
    def test_remove_coupon_redemption_on_clear_cart(self, info_log):

        reg_item = self.add_course_to_user_cart(self.course_key)
        CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        self.add_coupon(self.course_key, True, self.coupon_code)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse('shoppingcart.views.clear_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)

        info_log.assert_called_with(
            'Coupon redemption entry removed for user %s for order %s',
            self.user,
            reg_item.id
        )

    def test_add_course_to_cart_already_registered(self):
        CourseEnrollment.enroll(self.user, self.course_key)
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('You are already registered in course {0}.'.format(self.course_key.to_deprecated_string()), resp.content)

    def test_add_nonexistent_course_to_cart(self):
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=['non/existent/course']))
        self.assertEqual(resp.status_code, 404)
        self.assertIn("The course you requested does not exist.", resp.content)

    def test_add_course_to_cart_success(self):
        self.login_user()
        reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()])
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(PaidCourseRegistration.contained_in_order(self.cart, self.course_key))

    @patch('shoppingcart.views.render_purchase_form_html', form_mock)
    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_cart(self):
        self.login_user()
        reg_item = PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        cert_item = CertificateItem.add_to_order(
            self.cart,
            self.verified_course_key,
            self.cost,
            self.course_mode.mode_slug
        )
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)

        ((purchase_form_arg_cart,), _) = form_mock.call_args  # pylint: disable=redefined-outer-name
        purchase_form_arg_cart_items = purchase_form_arg_cart.orderitem_set.all().select_subclasses()
        self.assertIn(reg_item, purchase_form_arg_cart_items)
        self.assertIn(cert_item, purchase_form_arg_cart_items)
        self.assertEqual(len(purchase_form_arg_cart_items), 2)

        ((template, context), _) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/shopping_cart.html')
        self.assertEqual(len(context['shoppingcart_items']), 2)
        self.assertEqual(context['amount'], 80)
        self.assertIn("80.00", context['form_html'])
        # check for the default currency in the context
        self.assertEqual(context['currency'], 'usd')
        self.assertEqual(context['currency_symbol'], '$')

    @patch('shoppingcart.views.render_purchase_form_html', form_mock)
    @patch('shoppingcart.views.render_to_response', render_mock)
    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=['PKR', 'Rs'])
    def test_show_cart_with_override_currency_settings(self):
        self.login_user()
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)

        ((purchase_form_arg_cart,), _) = form_mock.call_args  # pylint: disable=redefined-outer-name
        purchase_form_arg_cart_items = purchase_form_arg_cart.orderitem_set.all().select_subclasses()
        self.assertIn(reg_item, purchase_form_arg_cart_items)

        ((template, context), _) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/shopping_cart.html')
        # check for the override currency settings in the context
        self.assertEqual(context['currency'], 'PKR')
        self.assertEqual(context['currency_symbol'], 'Rs')

    def test_clear_cart(self):
        self.login_user()
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)
        resp = self.client.post(reverse('shoppingcart.views.clear_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)

    @patch('shoppingcart.views.log.exception')
    def test_remove_item(self, exception_log):
        self.login_user()
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        self.assertNotIn(reg_item, self.cart.orderitem_set.all().select_subclasses())

        self.cart.purchase()
        resp2 = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                 {'id': cert_item.id})
        self.assertEqual(resp2.status_code, 200)
        exception_log.assert_called_with(
            'Cannot remove cart OrderItem id=%s. DoesNotExist or item is already purchased', str(cert_item.id)
        )

        resp3 = self.client.post(
            reverse('shoppingcart.views.remove_item', args=[]),
            {'id': -1}
        )
        self.assertEqual(resp3.status_code, 200)
        exception_log.assert_called_with(
            'Cannot remove cart OrderItem id=%s. DoesNotExist or item is already purchased',
            '-1'
        )

    @patch('shoppingcart.views.process_postpay_callback', postpay_mock)
    def test_postpay_callback_success(self):
        postpay_mock.return_value = {'success': True, 'order': self.cart}
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.postpay_callback', args=[]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(urlparse(resp.__getitem__('location')).path,
                         reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))

    @patch('shoppingcart.views.process_postpay_callback', postpay_mock)
    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_postpay_callback_failure(self):
        postpay_mock.return_value = {'success': False, 'order': self.cart, 'error_html': 'ERROR_TEST!!!'}
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.postpay_callback', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('ERROR_TEST!!!', resp.content)

        ((template, context), _) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/error.html')
        self.assertEqual(context['order'], self.cart)
        self.assertEqual(context['error_html'], 'ERROR_TEST!!!')

    @ddt.data(0, 1)
    def test_show_receipt_json(self, num_items):
        # Create the correct number of items in the order
        for __ in range(num_items):
            CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase()
        self.login_user()
        url = reverse('shoppingcart.views.show_receipt', args=[self.cart.id])
        resp = self.client.get(url, HTTP_ACCEPT="application/json")

        # Should have gotten a successful response
        self.assertEqual(resp.status_code, 200)

        # Parse the response as JSON and check the contents
        json_resp = json.loads(resp.content)
        self.assertEqual(json_resp.get('currency'), self.cart.currency)
        self.assertEqual(json_resp.get('purchase_datetime'), get_default_time_display(self.cart.purchase_time))
        self.assertEqual(json_resp.get('total_cost'), self.cart.total_cost)
        self.assertEqual(json_resp.get('status'), "purchased")
        self.assertEqual(json_resp.get('billed_to'), {
            'first_name': self.cart.bill_to_first,
            'last_name': self.cart.bill_to_last,
            'street1': self.cart.bill_to_street1,
            'street2': self.cart.bill_to_street2,
            'city': self.cart.bill_to_city,
            'state': self.cart.bill_to_state,
            'postal_code': self.cart.bill_to_postalcode,
            'country': self.cart.bill_to_country
        })

        self.assertEqual(len(json_resp.get('items')), num_items)
        for item in json_resp.get('items'):
            self.assertEqual(item, {
                'unit_cost': 40,
                'quantity': 1,
                'line_cost': 40,
                'line_desc': '{} for course Test Course'.format(self.verified_course_mode.mode_display_name),
                'course_key': unicode(self.verified_course_key)
            })

    def test_show_receipt_xss(self):
        CertificateItem.add_to_order(self.cart, self.xss_course_key, self.cost, 'honor')
        self.cart.purchase()

        self.login_user()
        url = reverse('shoppingcart.views.show_receipt', args=[self.cart.id])
        resp = self.client.get(url)
        self.assert_no_xss(resp, '<script>alert("XSS")</script>')

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_reg_code_xss(self):
        self.add_reg_code(self.xss_course_key)

        # One courses in user shopping cart
        self.add_course_to_user_cart(self.xss_course_key)
        self.assertEquals(self.cart.orderitem_set.count(), 1)

        post_response = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(post_response.status_code, 200)

        redeem_url = reverse('register_code_redemption', args=[self.reg_code])
        redeem_response = self.client.get(redeem_url)

        self.assert_no_xss(redeem_response, '<script>alert("XSS")</script>')

    def test_show_receipt_json_multiple_items(self):
        # Two different item types
        PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        CertificateItem.add_to_order(
            self.cart,
            self.verified_course_key,
            self.cost,
            self.verified_course_mode.mode_slug
        )
        self.cart.purchase()

        self.login_user()
        url = reverse('shoppingcart.views.show_receipt', args=[self.cart.id])
        resp = self.client.get(url, HTTP_ACCEPT="application/json")

        # Should have gotten a successful response
        self.assertEqual(resp.status_code, 200)

        # Parse the response as JSON and check the contents
        json_resp = json.loads(resp.content)
        self.assertEqual(json_resp.get('total_cost'), self.cart.total_cost)

        items = json_resp.get('items')
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], {
            'unit_cost': 40,
            'quantity': 1,
            'line_cost': 40,
            'line_desc': 'Registration for Course: Robot Super Course',
            'course_key': unicode(self.course_key)
        })
        self.assertEqual(items[1], {
            'unit_cost': 40,
            'quantity': 1,
            'line_cost': 40,
            'line_desc': '{} for course Test Course'.format(self.verified_course_mode.mode_display_name),
            'course_key': unicode(self.verified_course_key)
        })

    def test_receipt_json_refunded(self):
        mock_enrollment = Mock()
        mock_enrollment.refundable.side_effect = lambda: True
        mock_enrollment.course_id = self.verified_course_key
        mock_enrollment.user = self.user

        CourseMode.objects.create(
            course_id=self.verified_course_key,
            mode_slug="verified",
            mode_display_name="verified cert",
            min_price=self.cost
        )

        cert = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'verified')
        self.cart.purchase()
        cert.refund_cert_callback(course_enrollment=mock_enrollment)

        self.login_user()
        url = reverse('shoppingcart.views.show_receipt', args=[self.cart.id])
        resp = self.client.get(url, HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 200)

        json_resp = json.loads(resp.content)
        self.assertEqual(json_resp.get('status'), 'refunded')

    def test_show_receipt_404s(self):
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase()

        user2 = UserFactory.create()
        cart2 = Order.get_cart_for_user(user2)
        PaidCourseRegistration.add_to_order(cart2, self.course_key)
        cart2.purchase()

        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[cart2.id]))
        self.assertEqual(resp.status_code, 404)

        resp2 = self.client.get(reverse('shoppingcart.views.show_receipt', args=[1000]))
        self.assertEqual(resp2.status_code, 404)

    def test_total_amount_of_purchased_course(self):
        self.add_course_to_user_cart(self.course_key)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        self.add_coupon(self.course_key, True, self.coupon_code)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        # Total amount of a particular course that is purchased by different users
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 36)

        self.client.login(username=self.instructor.username, password="test")
        cart = Order.get_cart_for_user(self.instructor)
        PaidCourseRegistration.add_to_order(cart, self.course_key, mode_slug=self.course_mode.mode_slug)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 76)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_valid_coupon_code(self):
        self.add_course_to_user_cart(self.course_key)
        self.add_coupon(self.course_key, True, self.coupon_code)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn(str(self.get_discount(self.cost)), resp.content)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_reg_code_and_course_registration_scenario(self):
        self.add_reg_code(self.course_key)

        # One courses in user shopping cart
        self.add_course_to_user_cart(self.course_key)
        self.assertEquals(self.cart.orderitem_set.count(), 1)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 200)

        redeem_url = reverse('register_code_redemption', args=[self.reg_code])
        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_reg_code_with_multiple_courses_and_checkout_scenario(self):
        self.add_reg_code(self.course_key)

        # Two courses in user shopping cart
        self.login_user()
        PaidCourseRegistration.add_to_order(self.cart, self.course_key, mode_slug=self.course_mode.mode_slug)
        item2 = PaidCourseRegistration.add_to_order(
            self.cart,
            self.testing_course.id,
            mode_slug=self.course_mode.mode_slug
        )
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 200)

        redeem_url = reverse('register_code_redemption', args=[self.reg_code])
        resp = self.client.get(redeem_url)
        self.assertEquals(resp.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', resp.content)

        #now activate the user by enrolling him/her to the course
        resp = self.client.post(redeem_url)
        self.assertEquals(resp.status_code, 200)

        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertIn('Payment', resp.content)
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)

        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertEqual(context['order'].total_cost, self.testing_cost)

        course_enrollment = CourseEnrollment.objects.filter(user=self.user)
        self.assertEqual(course_enrollment.count(), 2)

        # make sure the enrollment_ids were stored in the PaidCourseRegistration items
        # refetch them first since they are updated
        # item1 has been deleted from the the cart.
        #  User has been enrolled for the item1
        item2 = PaidCourseRegistration.objects.get(id=item2.id)
        self.assertIsNotNone(item2.course_enrollment)
        self.assertEqual(item2.course_enrollment.course_id, self.testing_course.id)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_valid_reg_code(self):
        self.add_course_to_user_cart(self.course_key)
        self.add_reg_code(self.course_key)

        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.reg_code})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('0.00', resp.content)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success(self):
        reg_item = PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn('80.00', resp.content)

        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['shoppingcart_items'][0])
        self.assertIn(cert_item, context['shoppingcart_items'][1])
        self.assertFalse(context['any_refunds'])
        # check for the default currency settings in the context
        self.assertEqual(context['currency_symbol'], '$')
        self.assertEqual(context['currency'], 'usd')

    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=['PKR', 'Rs'])
    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_override_currency_settings(self):
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)

        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertIn(reg_item, context['shoppingcart_items'][0])
        self.assertIn(cert_item, context['shoppingcart_items'][1])

        # check for the override currency settings in the context
        self.assertEqual(context['currency_symbol'], 'Rs')
        self.assertEqual(context['currency'], 'PKR')

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_courseregcode_item_total_price(self):
        self.cart.order_type = 'business'
        self.cart.save()
        CourseRegCodeItem.add_to_order(self.cart, self.course_key, 2, mode_slug=self.course_mode.mode_slug)
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.assertEquals(CourseRegCodeItem.get_total_amount_of_purchased_item(self.course_key), 80)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_order_type_business(self):
        self.cart.order_type = 'business'
        self.cart.save()
        reg_item = CourseRegCodeItem.add_to_order(
            self.cart,
            self.course_key,
            2,
            mode_slug=self.course_mode.mode_slug
        )
        self.cart.add_billing_details(company_name='T1Omega', company_contact_name='C1',
                                      company_contact_email='test@t1.com', recipient_email='test@t2.com')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        # mail is sent to these emails recipient_email, company_contact_email, order.user.email
        self.assertEquals(len(mail.outbox), 3)

        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)

        # when order_type = 'business' the user is not enrolled in the
        # course but presented with the enrollment links
        self.assertFalse(CourseEnrollment.is_enrolled(self.cart.user, self.course_key))
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn('80.00', resp.content)
        # check for the enrollment codes content
        self.assertIn('Please send each professional one of these unique registration codes to enroll into the course.', resp.content)

        # fetch the newly generated registration codes
        course_registration_codes = CourseRegistrationCode.objects.filter(order=self.cart)

        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['shoppingcart_items'][0])
        # now check for all the registration codes in the receipt
        # and all the codes should be unused at this point
        self.assertIn(course_registration_codes[0].code, context['reg_code_info_list'][0]['code'])
        self.assertIn(course_registration_codes[1].code, context['reg_code_info_list'][1]['code'])
        self.assertFalse(context['reg_code_info_list'][0]['is_redeemed'])
        self.assertFalse(context['reg_code_info_list'][1]['is_redeemed'])

        self.assertIn(self.cart.purchase_time.strftime("%B %d, %Y"), resp.content)
        self.assertIn(self.cart.company_name, resp.content)
        self.assertIn(self.cart.company_contact_name, resp.content)
        self.assertIn(self.cart.company_contact_email, resp.content)
        self.assertIn(self.cart.recipient_email, resp.content)
        self.assertIn("Invoice #{order_id}".format(order_id=self.cart.id), resp.content)
        self.assertIn('You have successfully purchased <b>{total_registration_codes} course registration codes'
                      .format(total_registration_codes=context['total_registration_codes']), resp.content)

        # now redeem one of registration code from the previous order
        redeem_url = reverse('register_code_redemption', args=[context['reg_code_info_list'][0]['code']])

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)
        self.assertIn('View Dashboard', response.content)

        # now view the receipt page again to see if any registration codes
        # has been expired or not
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        ((template, context), _) = render_mock.call_args  # pylint: disable=redefined-outer-name
        self.assertEqual(template, 'shoppingcart/receipt.html')
        # now check for all the registration codes in the receipt
        # and one of code should be used at this point
        self.assertTrue(context['reg_code_info_list'][0]['is_redeemed'])
        self.assertFalse(context['reg_code_info_list'][1]['is_redeemed'])

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_upgrade(self):

        reg_item = PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        self.login_user()

        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn('80.00', resp.content)

        ((template, context), _) = render_mock.call_args

        # When we come from the upgrade flow, we get these context variables

        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['shoppingcart_items'][0])
        self.assertIn(cert_item, context['shoppingcart_items'][1])
        self.assertFalse(context['any_refunds'])

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_refund(self):
        reg_item = PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        cert_item.status = "refunded"
        cert_item.save()
        self.assertEqual(self.cart.total_cost, 40)
        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('40.00', resp.content)

        ((template, context), _tmp) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['shoppingcart_items'][0])
        self.assertIn(cert_item, context['shoppingcart_items'][1])
        self.assertTrue(context['any_refunds'])

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_custom_receipt_page(self):
        cert_item = CertificateItem.add_to_order(self.cart, self.course_key, self.cost, 'honor')
        self.cart.purchase()
        self.login_user()
        receipt_url = reverse('shoppingcart.views.show_receipt', args=[self.cart.id])
        resp = self.client.get(receipt_url)
        self.assertEqual(resp.status_code, 200)
        ((template, _context), _tmp) = render_mock.call_args
        self.assertEqual(template, cert_item.single_item_receipt_template)

    def _assert_404(self, url, use_post=False):
        """
        Helper method to assert that a given url will return a 404 status code
        """
        if use_post:
            response = self.client.post(url)
        else:
            response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': False})
    def test_disabled_paid_courses(self):
        """
        Assert that the pages that require ENABLE_PAID_COURSE_REGISTRATION=True return a
        HTTP 404 status code when we have this flag turned off
        """
        self.login_user()
        self._assert_404(reverse('shoppingcart.views.show_cart', args=[]))
        self._assert_404(reverse('shoppingcart.views.clear_cart', args=[]))
        self._assert_404(reverse('shoppingcart.views.remove_item', args=[]), use_post=True)
        self._assert_404(reverse('shoppingcart.views.register_code_redemption', args=["testing"]))
        self._assert_404(reverse('shoppingcart.views.use_code', args=[]), use_post=True)
        self._assert_404(reverse('shoppingcart.views.update_user_cart', args=[]))
        self._assert_404(reverse('shoppingcart.views.reset_code_redemption', args=[]), use_post=True)
        self._assert_404(reverse('shoppingcart.views.billing_details', args=[]))

    def test_upgrade_postpay_callback_emits_ga_event(self):
        # Enroll as honor in the course with the current user.

        CourseEnrollment.enroll(self.user, self.course_key)

        # add verified mode
        CourseMode.objects.create(
            course_id=self.verified_course_key,
            mode_slug="verified",
            mode_display_name="verified cert",
            min_price=self.cost
        )

        # Purchase a verified certificate
        self.cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'verified')
        self.cart.start_purchase()

        self.login_user()
        # setting the attempting upgrade session value.
        session = self.client.session
        session['attempting_upgrade'] = True
        session.save()

        ordered_params = OrderedDict([
            ('amount', self.cost),
            ('currency', 'usd'),
            ('transaction_type', 'sale'),
            ('orderNumber', str(self.cart.id)),
            ('access_key', '123456789'),
            ('merchantID', 'edx'),
            ('djch', '012345678912'),
            ('orderPage_version', 2),
            ('orderPage_serialNumber', '1234567890'),
            ('profile_id', "00000001"),
            ('reference_number', str(self.cart.id)),
            ('locale', 'en'),
            ('signed_date_time', '2014-08-18T13:59:31Z'),
        ])

        resp_params = PaymentFakeView.response_post_params(sign(ordered_params))
        self.assertTrue(self.client.session.get('attempting_upgrade'))
        url = reverse('shoppingcart.views.postpay_callback')
        self.client.post(url, resp_params, follow=True)
        self.assertFalse(self.client.session.get('attempting_upgrade'))

        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.upgrade.succeeded',
            {
                'user_id': self.user.id,
                'course_id': self.verified_course_key.to_deprecated_string(),
                'mode': 'verified'
            }
        )

    def test_shopping_cart_navigation_link_not_in_microsite(self):
        """
        Tests shopping cart link is available in navigation header if request is not from a microsite.
        """
        CourseEnrollment.enroll(self.user, self.course_key)
        self.add_course_to_user_cart(self.testing_course.id)
        resp = self.client.get(reverse('courseware', kwargs={'course_id': unicode(self.course.id)}))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a class="shopping-cart"', resp.content)

    def test_shopping_cart_navigation_link_not_in_microsite_and_not_on_courseware(self):
        """
        Tests shopping cart link is available in navigation header if request is not from a microsite
        and requested page is not courseware too.
        """
        CourseEnrollment.enroll(self.user, self.course_key)
        self.add_course_to_user_cart(self.testing_course.id)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a class="shopping-cart"', resp.content)

    def test_shopping_cart_navigation_link_in_microsite_not_on_courseware(self):
        """
        Tests shopping cart link is available in navigation header if request is from a microsite but requested
        page is not from courseware.
        """
        CourseEnrollment.enroll(self.user, self.course_key)
        self.add_course_to_user_cart(self.testing_course.id)
        with patch('microsite_configuration.microsite.is_request_in_microsite',
                   Mock(return_value=True)):
            resp = self.client.get(reverse('dashboard'))
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<a class="shopping-cart"', resp.content)

    def test_shopping_cart_navigation_link_in_microsite_courseware_page(self):
        """
        Tests shopping cart link is not available in navigation header if request is from a microsite
        and requested page is from courseware.
        """
        CourseEnrollment.enroll(self.user, self.course_key)
        self.add_course_to_user_cart(self.testing_course.id)
        with patch('microsite_configuration.microsite.is_request_in_microsite',
                   Mock(return_value=True)):
            resp = self.client.get(reverse('courseware', kwargs={'course_id': unicode(self.course.id)}))
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('<a class="shopping-cart"', resp.content)


class ReceiptRedirectTest(SharedModuleStoreTestCase):
    """Test special-case redirect from the receipt page. """

    COST = 40
    PASSWORD = 'password'

    @classmethod
    def setUpClass(cls):
        super(ReceiptRedirectTest, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id

    def setUp(self):
        super(ReceiptRedirectTest, self).setUp()
        self.user = UserFactory.create()
        self.user.set_password(self.PASSWORD)
        self.user.save()
        self.course_mode = CourseMode(
            course_id=self.course_key,
            mode_slug="verified",
            mode_display_name="verified cert",
            min_price=self.COST
        )
        self.course_mode.save()
        self.cart = Order.get_cart_for_user(self.user)
        self.client.login(
            username=self.user.username,
            password=self.PASSWORD
        )

    def test_postpay_callback_redirect_to_verify_student(self):
        # Create other carts first
        # This ensures that the order ID and order item IDs do not match
        Order.get_cart_for_user(self.user).start_purchase()
        Order.get_cart_for_user(self.user).start_purchase()
        Order.get_cart_for_user(self.user).start_purchase()

        # Purchase a verified certificate
        self.cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(
            self.cart,
            self.course_key,
            self.COST,
            'verified'
        )
        self.cart.start_purchase()

        # Simulate hitting the post-pay callback
        with patch('shoppingcart.views.process_postpay_callback') as mock_process:
            mock_process.return_value = {'success': True, 'order': self.cart}
            url = reverse('shoppingcart.views.postpay_callback')
            resp = self.client.post(url, follow=True)

        # Expect to be redirected to the payment confirmation
        # page in the verify_student app
        redirect_url = reverse(
            'verify_student_payment_confirmation',
            kwargs={'course_id': unicode(self.course_key)}
        )
        redirect_url += '?payment-order-num={order_num}'.format(
            order_num=self.cart.id
        )
        self.assertIn(redirect_url, resp.redirect_chain[0][0])


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class ShoppingcartViewsClosedEnrollment(ModuleStoreTestCase):
    """
    Test suite for ShoppingcartViews Course Enrollments Closed or not
    """
    def setUp(self):
        super(ShoppingcartViewsClosedEnrollment, self).setUp()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.instructor = AdminFactory.create()
        self.cost = 40

        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id
        self.course_mode = CourseMode(
            course_id=self.course_key,
            mode_slug=CourseMode.HONOR,
            mode_display_name="honor cert",
            min_price=self.cost
        )
        self.course_mode.save()
        self.testing_course = CourseFactory.create(
            org='Edx',
            number='999',
            display_name='Testing Super Course',
            metadata={"invitation_only": False}
        )
        self.testing_course_mode = CourseMode(
            course_id=self.testing_course.id,
            mode_slug=CourseMode.HONOR,
            mode_display_name="honor cert",
            min_price=self.cost
        )
        self.course_mode.save()
        self.percentage_discount = 20.0
        self.coupon_code = 'asdsad'
        self.course_mode = CourseMode(course_id=self.testing_course.id,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.cart = Order.get_cart_for_user(self.user)
        self.now = datetime.now(pytz.UTC)
        self.tomorrow = self.now + timedelta(days=1)
        self.nextday = self.tomorrow + timedelta(days=1)

    def add_coupon(self, course_key, is_active, code):
        """
        add dummy coupon into models
        """
        coupon = Coupon(code=code, description='testing code', course_id=course_key,
                        percentage_discount=self.percentage_discount, created_by=self.user, is_active=is_active)
        coupon.save()

    def login_user(self):
        """
        Helper fn to login self.user
        """
        self.client.login(username=self.user.username, password="password")

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_to_check_that_cart_item_enrollment_is_closed(self):
        self.login_user()
        reg_item1 = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        expired_course_item = PaidCourseRegistration.add_to_order(self.cart, self.testing_course.id)

        # update the testing_course enrollment dates
        self.testing_course.enrollment_start = self.tomorrow
        self.testing_course.enrollment_end = self.nextday
        self.testing_course = self.update_course(self.testing_course, self.user.id)

        # now add the same coupon code to the second course(testing_course)
        self.add_coupon(self.testing_course.id, True, self.coupon_code)
        resp = self.client.post(reverse('shoppingcart.views.use_code'), {'code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        coupon_redemption = CouponRedemption.objects.filter(coupon__course_id=expired_course_item.course_id,
                                                            order=expired_course_item.order_id)
        self.assertEqual(coupon_redemption.count(), 1)
        # testing_course enrollment is closed but the course is in the cart
        # so we delete that item from the cart and display the message in the cart
        # coupon redemption entry should also be deleted when the item is expired.
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("{course_name} has been removed because the enrollment period has closed.".format(course_name=self.testing_course.display_name), resp.content)

        # now the redemption entry should be deleted from the table.
        coupon_redemption = CouponRedemption.objects.filter(coupon__course_id=expired_course_item.course_id,
                                                            order=expired_course_item.order_id)
        self.assertEqual(coupon_redemption.count(), 0)
        ((template, context), _tmp) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/shopping_cart.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item1, context['shoppingcart_items'][0])
        self.assertEqual(1, len(context['shoppingcart_items']))
        self.assertEqual(True, context['is_course_enrollment_closed'])
        self.assertIn(self.testing_course.display_name, context['expired_course_names'])

    def test_to_check_that_cart_item_enrollment_is_closed_when_clicking_the_payment_button(self):
        self.login_user()
        PaidCourseRegistration.add_to_order(
            self.cart,
            self.course_key,
            mode_slug=self.course_mode.mode_slug
        )
        PaidCourseRegistration.add_to_order(
            self.cart,
            self.testing_course.id,
            mode_slug=self.testing_course_mode.mode_slug
        )

        # update the testing_course enrollment dates
        self.testing_course.enrollment_start = self.tomorrow
        self.testing_course.enrollment_end = self.nextday
        self.testing_course = self.update_course(self.testing_course, self.user.id)

        # testing_course enrollment is closed but the course is in the cart
        # so we delete that item from the cart and display the message in the cart
        resp = self.client.get(reverse('shoppingcart.views.verify_cart'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['is_course_enrollment_closed'])

        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("{course_name} has been removed because the enrollment period has closed.".format(course_name=self.testing_course.display_name), resp.content)
        self.assertIn('40.00', resp.content)

    def test_is_enrollment_closed_when_order_type_is_business(self):
        self.login_user()
        self.cart.order_type = 'business'
        self.cart.save()
        PaidCourseRegistration.add_to_order(self.cart, self.course_key, mode_slug=self.course_mode.mode_slug)
        CourseRegCodeItem.add_to_order(self.cart, self.testing_course.id, 2, mode_slug=self.course_mode.mode_slug)

        # update the testing_course enrollment dates
        self.testing_course.enrollment_start = self.tomorrow
        self.testing_course.enrollment_end = self.nextday
        self.testing_course = self.update_course(self.testing_course, self.user.id)

        resp = self.client.post(reverse('shoppingcart.views.billing_details'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(json.loads(resp.content)['is_course_enrollment_closed'])

        # testing_course enrollment is closed but the course is in the cart
        # so we delete that item from the cart and display the message in the cart
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("{course_name} has been removed because the enrollment period has closed.".format(course_name=self.testing_course.display_name), resp.content)
        self.assertIn('40.00', resp.content)


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class RegistrationCodeRedemptionCourseEnrollment(SharedModuleStoreTestCase):
    """
    Test suite for RegistrationCodeRedemption Course Enrollments
    """

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    @classmethod
    def setUpClass(cls):
        super(RegistrationCodeRedemptionCourseEnrollment, cls).setUpClass()
        cls.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        cls.course_key = cls.course.id

    def setUp(self, **kwargs):
        super(RegistrationCodeRedemptionCourseEnrollment, self).setUp()

        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.cost = 40
        self.course_mode = CourseMode(course_id=self.course_key,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()

    def login_user(self):
        """
        Helper fn to login self.user
        """
        self.client.login(username=self.user.username, password="password")

    def test_registration_redemption_post_request_ratelimited(self):
        """
        Try (and fail) registration code redemption 30 times
        in a row on an non-existing registration code post request
        """
        cache.clear()
        url = reverse('register_code_redemption', args=['asdasd'])
        self.login_user()
        for i in xrange(30):  # pylint: disable=unused-variable
            response = self.client.post(url)
            self.assertEquals(response.status_code, 404)

        # then the rate limiter should kick in and give a HttpForbidden response
        response = self.client.post(url)
        self.assertEquals(response.status_code, 403)

        # now reset the time to 5 mins from now in future in order to unblock
        reset_time = datetime.now(UTC) + timedelta(seconds=300)
        with freeze_time(reset_time):
            response = self.client.post(url)
            self.assertEquals(response.status_code, 404)

        cache.clear()

    def test_registration_redemption_get_request_ratelimited(self):
        """
        Try (and fail) registration code redemption 30 times
        in a row on an non-existing registration code get request
        """
        cache.clear()
        url = reverse('register_code_redemption', args=['asdasd'])
        self.login_user()
        for i in xrange(30):  # pylint: disable=unused-variable
            response = self.client.get(url)
            self.assertEquals(response.status_code, 404)

        # then the rate limiter should kick in and give a HttpForbidden response
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)

        # now reset the time to 5 mins from now in future in order to unblock
        reset_time = datetime.now(UTC) + timedelta(seconds=300)
        with freeze_time(reset_time):
            response = self.client.get(url)
            self.assertEquals(response.status_code, 404)

        cache.clear()

    def test_course_enrollment_active_registration_code_redemption(self):
        """
        Test for active registration code course enrollment
        """
        cache.clear()
        instructor = InstructorFactory(course_key=self.course_key)
        self.client.login(username=instructor.username, password='test')

        # Registration Code Generation only available to Sales Admins.
        CourseSalesAdminRole(self.course.id).add_users(instructor)

        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 12, 'company_name': 'Test Group', 'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com', 'unit_price': 122.45, 'recipient_name': 'Test123',
            'recipient_email': 'test@123.com', 'address_line_1': 'Portland Street',
            'address_line_2': '', 'address_line_3': '', 'city': '', 'state': '', 'zip': '', 'country': '',
            'customer_reference_number': '123A23F', 'internal_reference': '', 'invoice': ''
        }

        response = self.client.post(url, data)
        self.assertEquals(response.status_code, 200)
        # get the first registration from the newly created registration codes
        registration_code = CourseRegistrationCode.objects.all()[0].code
        redeem_url = reverse('register_code_redemption', args=[registration_code])
        self.login_user()

        response = self.client.get(redeem_url)
        self.assertEquals(response.status_code, 200)
        # check button text
        self.assertIn('Activate Course Enrollment', response.content)

        #now activate the user by enrolling him/her to the course
        response = self.client.post(redeem_url)
        self.assertEquals(response.status_code, 200)
        self.assertIn('View Dashboard', response.content)

        #now check that the registration code has already been redeemed and user is already registered in the course
        RegistrationCodeRedemption.objects.filter(registration_code__code=registration_code)
        response = self.client.get(redeem_url)
        self.assertEquals(len(RegistrationCodeRedemption.objects.filter(registration_code__code=registration_code)), 1)
        self.assertIn("You've clicked a link for an enrollment code that has already been used.", response.content)

        #now check that the registration code has already been redeemed
        response = self.client.post(redeem_url)
        self.assertIn("You've clicked a link for an enrollment code that has already been used.", response.content)

        #now check the response of the dashboard page
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        self.assertEquals(response.status_code, 200)
        self.assertIn(self.course.display_name, response.content)


@ddt.ddt
class RedeemCodeEmbargoTests(UrlResetMixin, ModuleStoreTestCase):
    """Test blocking redeem code redemption based on country access rules. """

    USERNAME = 'bob'
    PASSWORD = 'test'

    URLCONF_MODULES = ['embargo']

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(RedeemCodeEmbargoTests, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.user.username, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

    @ddt.data('get', 'post')
    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_registration_code_redemption_embargo(self, method):
        # Create a valid registration code
        reg_code = CourseRegistrationCode.objects.create(
            code="abcd1234",
            course_id=self.course.id,
            created_by=self.user
        )

        # Try to redeem the code from a restricted country
        with restrict_course(self.course.id) as redirect_url:
            url = reverse(
                'register_code_redemption',
                kwargs={'registration_code': 'abcd1234'}
            )
            response = getattr(self.client, method)(url)
            self.assertRedirects(response, redirect_url)

        # The registration code should NOT be redeemed
        is_redeemed = RegistrationCodeRedemption.objects.filter(
            registration_code=reg_code
        ).exists()
        self.assertFalse(is_redeemed)

        # The user should NOT be enrolled
        is_enrolled = CourseEnrollment.is_enrolled(self.user, self.course.id)
        self.assertFalse(is_enrolled)


@ddt.ddt
class DonationViewTest(SharedModuleStoreTestCase):
    """Tests for making a donation.

    These tests cover both the single-item purchase flow,
    as well as the receipt page for donation items.
    """

    DONATION_AMOUNT = "23.45"
    PASSWORD = "password"

    @classmethod
    def setUpClass(cls):
        super(DonationViewTest, cls).setUpClass()
        cls.course = CourseFactory.create(display_name="Test Course")

    def setUp(self):
        """Create a test user and order. """
        super(DonationViewTest, self).setUp()

        # Create and login a user
        self.user = UserFactory.create()
        self.user.set_password(self.PASSWORD)
        self.user.save()
        result = self.client.login(username=self.user.username, password=self.PASSWORD)
        self.assertTrue(result)

        # Enable donations
        config = DonationConfiguration.current()
        config.enabled = True
        config.save()

    def test_donation_for_org(self):
        self._donate(self.DONATION_AMOUNT)
        self._assert_receipt_contains("tax purposes")

    def test_donation_for_course_receipt(self):
        # Donate to our course
        self._donate(self.DONATION_AMOUNT, course_id=self.course.id)

        # Verify the receipt page
        self._assert_receipt_contains("tax purposes")
        self._assert_receipt_contains(self.course.display_name)

    def test_smallest_possible_donation(self):
        self._donate("0.01")
        self._assert_receipt_contains("0.01")

    @ddt.data(
        {},
        {"amount": "abcd"},
        {"amount": "-1.00"},
        {"amount": "0.00"},
        {"amount": "0.001"},
        {"amount": "0"},
        {"amount": "23.45", "course_id": "invalid"}
    )
    def test_donation_bad_request(self, bad_params):
        response = self.client.post(reverse('donation'), bad_params)
        self.assertEqual(response.status_code, 400)

    def test_donation_requires_login(self):
        self.client.logout()
        response = self.client.post(reverse('donation'), {'amount': self.DONATION_AMOUNT})
        self.assertEqual(response.status_code, 302)

    def test_no_such_course(self):
        response = self.client.post(
            reverse("donation"),
            {"amount": self.DONATION_AMOUNT, "course_id": "edx/DemoX/Demo"}
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data("get", "put", "head", "options", "delete")
    def test_donation_requires_post(self, invalid_method):
        response = getattr(self.client, invalid_method)(
            reverse("donation"), {"amount": self.DONATION_AMOUNT}
        )
        self.assertEqual(response.status_code, 405)

    def test_donations_disabled(self):
        config = DonationConfiguration.current()
        config.enabled = False
        config.save()

        # Logged in -- should be a 404
        response = self.client.post(reverse('donation'))
        self.assertEqual(response.status_code, 404)

        # Logged out -- should still be a 404
        self.client.logout()
        response = self.client.post(reverse('donation'))
        self.assertEqual(response.status_code, 404)

    def _donate(self, donation_amount, course_id=None):
        """Simulate a donation to a course.

        This covers the entire payment flow, except for the external
        payment processor, which is simulated.

        Arguments:
            donation_amount (unicode): The amount the user is donating.

        Keyword Arguments:
            course_id (CourseKey): If provided, make a donation to the specific course.

        Raises:
            AssertionError

        """
        # Purchase a single donation item
        # Optionally specify a particular course for the donation
        params = {'amount': donation_amount}
        if course_id is not None:
            params['course_id'] = course_id

        url = reverse('donation')
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, 200)

        # Use the fake payment implementation to simulate the parameters
        # we would receive from the payment processor.
        payment_info = json.loads(response.content)
        self.assertEqual(payment_info["payment_url"], "/shoppingcart/payment_fake")

        # If this is a per-course donation, verify that we're sending
        # the course ID to the payment processor.
        if course_id is not None:
            self.assertEqual(
                payment_info["payment_params"]["merchant_defined_data1"],
                unicode(course_id)
            )
            self.assertEqual(
                payment_info["payment_params"]["merchant_defined_data2"],
                "donation_course"
            )
        else:
            self.assertEqual(payment_info["payment_params"]["merchant_defined_data1"], "")
            self.assertEqual(
                payment_info["payment_params"]["merchant_defined_data2"],
                "donation_general"
            )

        processor_response_params = PaymentFakeView.response_post_params(payment_info["payment_params"])

        # Use the response parameters to simulate a successful payment
        url = reverse('shoppingcart.views.postpay_callback')
        response = self.client.post(url, processor_response_params)
        self.assertRedirects(response, self._receipt_url)

    def _assert_receipt_contains(self, expected_text):
        """Load the receipt page and verify that it contains the expected text."""
        resp = self.client.get(self._receipt_url)
        self.assertContains(resp, expected_text)

    @property
    def _receipt_url(self):
        order_id = Order.objects.get(user=self.user, status="purchased").id
        return reverse("shoppingcart.views.show_receipt", kwargs={"ordernum": order_id})


class CSVReportViewsTest(SharedModuleStoreTestCase):
    """
    Test suite for CSV Purchase Reporting
    """
    @classmethod
    def setUpClass(cls):
        super(CSVReportViewsTest, cls).setUpClass()
        cls.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        cls.course_key = cls.course.id
        verified_course = CourseFactory.create(org='org', number='test', display_name='Test Course')
        cls.verified_course_key = verified_course.id

    def setUp(self):
        super(CSVReportViewsTest, self).setUp()

        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.cost = 40
        self.course_mode = CourseMode(course_id=self.course_key,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        self.course_mode2 = CourseMode(course_id=self.course_key,
                                       mode_slug="verified",
                                       mode_display_name="verified cert",
                                       min_price=self.cost)
        self.course_mode2.save()

        self.cart = Order.get_cart_for_user(self.user)
        self.dl_grp = Group(name=settings.PAYMENT_REPORT_GENERATOR_GROUP)
        self.dl_grp.save()

    def login_user(self):
        """
        Helper fn to login self.user
        """
        self.client.login(username=self.user.username, password="password")

    def add_to_download_group(self, user):
        """
        Helper fn to add self.user to group that's allowed to download report CSV
        """
        user.groups.add(self.dl_grp)

    def test_report_csv_no_access(self):
        self.login_user()
        response = self.client.get(reverse('payment_csv_report'))
        self.assertEqual(response.status_code, 403)

    def test_report_csv_bad_method(self):
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.put(reverse('payment_csv_report'))
        self.assertEqual(response.status_code, 400)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_report_csv_get(self):
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.get(reverse('payment_csv_report'))

        ((template, context), unused_kwargs) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/download_report.html')
        self.assertFalse(context['total_count_error'])
        self.assertFalse(context['date_fmt_error'])
        self.assertIn("Download CSV Reports", response.content.decode('UTF-8'))

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_report_csv_bad_date(self):
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.post(reverse('payment_csv_report'), {'start_date': 'BAD', 'end_date': 'BAD', 'requested_report': 'itemized_purchase_report'})

        ((template, context), unused_kwargs) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/download_report.html')
        self.assertFalse(context['total_count_error'])
        self.assertTrue(context['date_fmt_error'])
        self.assertIn("There was an error in your date input.  It should be formatted as YYYY-MM-DD",
                      response.content.decode('UTF-8'))

    def test_report_csv_itemized(self):
        report_type = 'itemized_purchase_report'
        start_date = '1970-01-01'
        end_date = '2100-01-01'
        PaidCourseRegistration.add_to_order(self.cart, self.course_key, mode_slug=self.course_mode.mode_slug)
        self.cart.purchase()
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.post(reverse('payment_csv_report'), {'start_date': start_date,
                                                                    'end_date': end_date,
                                                                    'requested_report': report_type})
        self.assertEqual(response['Content-Type'], 'text/csv')
        report = initialize_report(report_type, start_date, end_date)
        self.assertIn(",".join(report.header()), response.content)
        self.assertIn(
            ",1,purchased,1,40.00,40.00,usd,Registration for Course: Robot Super Course,",
            response.content
        )

    def test_report_csv_university_revenue_share(self):
        report_type = 'university_revenue_share'
        start_date = '1970-01-01'
        end_date = '2100-01-01'
        start_letter = 'A'
        end_letter = 'Z'
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.post(reverse('payment_csv_report'), {'start_date': start_date,
                                                                    'end_date': end_date,
                                                                    'start_letter': start_letter,
                                                                    'end_letter': end_letter,
                                                                    'requested_report': report_type})
        self.assertEqual(response['Content-Type'], 'text/csv')
        report = initialize_report(report_type, start_date, end_date, start_letter, end_letter)
        self.assertIn(",".join(report.header()), response.content)


class UtilFnsTest(TestCase):
    """
    Tests for utility functions in views.py
    """
    def setUp(self):
        super(UtilFnsTest, self).setUp()

        self.user = UserFactory.create()

    def test_can_download_report_no_group(self):
        """
        Group controlling perms is not present
        """
        self.assertFalse(_can_download_report(self.user))

    def test_can_download_report_not_member(self):
        """
        User is not part of group controlling perms
        """
        Group(name=settings.PAYMENT_REPORT_GENERATOR_GROUP).save()
        self.assertFalse(_can_download_report(self.user))

    def test_can_download_report(self):
        """
        User is part of group controlling perms
        """
        grp = Group(name=settings.PAYMENT_REPORT_GENERATOR_GROUP)
        grp.save()
        self.user.groups.add(grp)
        self.assertTrue(_can_download_report(self.user))

    def test_get_date_from_str(self):
        test_str = "2013-10-01"
        date = _get_date_from_str(test_str)
        self.assertEqual(2013, date.year)
        self.assertEqual(10, date.month)
        self.assertEqual(1, date.day)
