"""
Tests for Shopping Cart views
"""
from urlparse import urlparse

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.models import Group

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from shoppingcart.views import _can_download_report, _get_date_from_str
from shoppingcart.models import Order, CertificateItem, PaidCourseRegistration, Coupon
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from edxmako.shortcuts import render_to_response
from shoppingcart.processors import render_purchase_form_html
from mock import patch, Mock
from shoppingcart.views import initialize_report
from decimal import Decimal
from student.tests.factories import AdminFactory

def mock_render_purchase_form_html(*args, **kwargs):
    return render_purchase_form_html(*args, **kwargs)

form_mock = Mock(side_effect=mock_render_purchase_form_html)

def mock_render_to_response(*args, **kwargs):
    return render_to_response(*args, **kwargs)

render_mock = Mock(side_effect=mock_render_to_response)

postpay_mock = Mock()


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ShoppingCartViewsTests(ModuleStoreTestCase):
    def setUp(self):
        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.instructor = AdminFactory.create()
        self.cost = 40
        self.coupon_code = 'abcde'
        self.percentage_discount = 10
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id
        self.course_mode = CourseMode(course_id=self.course_key,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=self.cost)
        self.course_mode.save()
        verified_course = CourseFactory.create(org='org', number='test', display_name='Test Course')
        self.verified_course_key = verified_course.id
        self.cart = Order.get_cart_for_user(self.user)
        self.addCleanup(patcher.stop)

    def get_discount(self):
        """
        This method simple return the discounted amount
        """
        val = Decimal("{0:.2f}".format(Decimal(self.percentage_discount / 100.00) * self.cost))
        return self.cost - val

    def add_coupon(self, course_key, is_active):
        """
        add dummy coupon into models
        """
        coupon = Coupon(code=self.coupon_code, description='testing code', course_id=course_key,
                        percentage_discount=self.percentage_discount, created_by=self.user, is_active=is_active)
        coupon.save()

    def add_course_to_user_cart(self):
        """
        adding course to user cart
        """
        self.login_user()
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        return reg_item

    def login_user(self):
        self.client.login(username=self.user.username, password="password")

    def test_add_course_to_cart_anon(self):
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 403)

    def test_add_course_to_cart_already_in_cart(self):
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.login_user()
        resp = self.client.post(reverse('shoppingcart.views.add_course_to_cart', args=[self.course_key.to_deprecated_string()]))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('The course {0} is already in your cart.'.format(self.course_key.to_deprecated_string()), resp.content)

    def test_course_discount_invalid_coupon(self):
        self.add_coupon(self.course_key, True)
        self.add_course_to_user_cart()
        non_existing_code = "non_existing_code"
        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': non_existing_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Discount does not exist against coupon '{0}'.".format(non_existing_code), resp.content)

    def test_course_discount_inactive_coupon(self):
        self.add_coupon(self.course_key, False)
        self.add_course_to_user_cart()
        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Coupon '{0}' is inactive.".format(self.coupon_code), resp.content)

    def test_course_does_not_exist_in_cart_against_valid_coupon(self):
        course_key = self.course_key.to_deprecated_string() + 'testing'
        self.add_coupon(course_key, True)
        self.add_course_to_user_cart()

        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 404)
        self.assertIn("Coupon '{0}' is not valid for any course in the shopping cart.".format(self.coupon_code), resp.content)

    def test_course_discount_for_valid_active_coupon_code(self):

        self.add_coupon(self.course_key, True)
        self.add_course_to_user_cart()

        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit price should be updated for that course
        item = self.cart.orderitem_set.all().select_subclasses()[0]
        self.assertEquals(item.unit_cost, self.get_discount())

        # after getting 10 percent discount
        self.assertEqual(self.cart.total_cost, self.get_discount())

        # now testing coupon code already used scenario, reusing the same coupon code
        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Coupon '{0}' already used.".format(self.coupon_code), resp.content)

    @patch('shoppingcart.views.log.debug')
    def test_non_existing_coupon_redemption_on_removing_item(self, debug_log):

        reg_item = self.add_course_to_user_cart()
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})
        debug_log.assert_called_with(
            'Coupon redemption does not exist for order item id={0}.'.format(reg_item.id))

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)

    @patch('shoppingcart.views.log.info')
    def test_existing_coupon_redemption_on_removing_item(self, info_log):

        self.add_coupon(self.course_key, True)
        reg_item = self.add_course_to_user_cart()

        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)
        info_log.assert_called_with(
            'Coupon "{0}" redemption entry removed for user "{1}" for order item "{2}"'.format(self.coupon_code, self.user, reg_item.id))

    @patch('shoppingcart.views.log.info')
    def test_coupon_discount_for_multiple_courses_in_cart(self, info_log):

        reg_item = self.add_course_to_user_cart()
        self.add_coupon(self.course_key, True)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        # unit_cost should be updated for that particular course for which coupon code is registered
        items = self.cart.orderitem_set.all().select_subclasses()
        for item in items:
            if item.id == reg_item.id:
                self.assertEquals(item.unit_cost, self.get_discount())
            elif item.id == cert_item.id:
                self.assertEquals(item.list_price, None)

        # Delete the discounted item, corresponding coupon redemption should be removed for that particular discounted item
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': reg_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        info_log.assert_called_with(
            'Coupon "{0}" redemption entry removed for user "{1}" for order item "{2}"'.format(self.coupon_code, self.user, reg_item.id))

    @patch('shoppingcart.views.log.info')
    def test_delete_certificate_item(self, info_log):

        reg_item = self.add_course_to_user_cart()
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        # Delete the discounted item, corresponding coupon redemption should be removed for that particular discounted item
        resp = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                {'id': cert_item.id})

        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        info_log.assert_called_with(
            'order item {0} removed for user {1}'.format(cert_item.id, self.user))

    @patch('shoppingcart.views.log.info')
    def test_remove_coupon_redemption_on_clear_cart(self, info_log):

        reg_item = self.add_course_to_user_cart()
        CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.assertEquals(self.cart.orderitem_set.count(), 2)

        self.add_coupon(self.course_key, True)
        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(reverse('shoppingcart.views.clear_cart', args=[]))
        self.assertEqual(resp.status_code, 200)
        self.assertEquals(self.cart.orderitem_set.count(), 0)

        info_log.assert_called_with(
            'Coupon redemption entry removed for user {0} for order {1}'.format(self.user, reg_item.id))

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
        self.assertIn(_("The course you requested does not exist."), resp.content)

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
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        resp = self.client.get(reverse('shoppingcart.views.show_cart', args=[]))
        self.assertEqual(resp.status_code, 200)

        ((purchase_form_arg_cart,), _) = form_mock.call_args
        purchase_form_arg_cart_items = purchase_form_arg_cart.orderitem_set.all().select_subclasses()
        self.assertIn(reg_item, purchase_form_arg_cart_items)
        self.assertIn(cert_item, purchase_form_arg_cart_items)
        self.assertEqual(len(purchase_form_arg_cart_items), 2)

        ((template, context), _) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/list.html')
        self.assertEqual(len(context['shoppingcart_items']), 2)
        self.assertEqual(context['amount'], 80)
        self.assertIn("80.00", context['form_html'])

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
            'Cannot remove cart OrderItem id={0}. DoesNotExist or item is already purchased'.format(cert_item.id))

        resp3 = self.client.post(reverse('shoppingcart.views.remove_item', args=[]),
                                 {'id': -1})
        self.assertEqual(resp3.status_code, 200)
        exception_log.assert_called_with(
            'Cannot remove cart OrderItem id={0}. DoesNotExist or item is already purchased'.format(-1))

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
        self.add_course_to_user_cart()
        self.assertEquals(self.cart.orderitem_set.count(), 1)
        self.add_coupon(self.course_key, True)
        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)

        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        # Total amount of a particular course that is purchased by different users
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 36)

        self.client.login(username=self.instructor.username, password="test")
        cart = Order.get_cart_for_user(self.instructor)
        PaidCourseRegistration.add_to_order(cart, self.course_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course_key)
        self.assertEqual(total_amount, 76)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_valid_coupon_code(self):
        self.add_course_to_user_cart()
        self.add_coupon(self.course_key, True)

        resp = self.client.post(reverse('shoppingcart.views.use_coupon'), {'coupon_code': self.coupon_code})
        self.assertEqual(resp.status_code, 200)
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn(str(self.get_discount()), resp.content)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success(self):
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        self.login_user()
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn('80.00', resp.content)

        ((template, context), _) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['order_items'])
        self.assertIn(cert_item, context['order_items'])
        self.assertFalse(context['any_refunds'])

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_with_upgrade(self):

        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        cert_item = CertificateItem.add_to_order(self.cart, self.verified_course_key, self.cost, 'honor')
        self.cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')

        self.login_user()

        # When we come from the upgrade flow, we'll have a session variable showing that
        s = self.client.session
        s['attempting_upgrade'] = True
        s.save()

        self.mock_tracker.emit.reset_mock()  # pylint: disable=maybe-no-member
        resp = self.client.get(reverse('shoppingcart.views.show_receipt', args=[self.cart.id]))

        # Once they've upgraded, they're no longer *attempting* to upgrade
        attempting_upgrade = self.client.session.get('attempting_upgrade', False)
        self.assertFalse(attempting_upgrade)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('FirstNameTesting123', resp.content)
        self.assertIn('80.00', resp.content)


        ((template, context), _) = render_mock.call_args

        # When we come from the upgrade flow, we get these context variables


        self.assertEqual(template, 'shoppingcart/receipt.html')
        self.assertEqual(context['order'], self.cart)
        self.assertIn(reg_item, context['order_items'])
        self.assertIn(cert_item, context['order_items'])
        self.assertFalse(context['any_refunds'])

        course_enrollment = CourseEnrollment.get_or_create_enrollment(self.user, self.course_key)
        course_enrollment.emit_event('edx.course.enrollment.upgrade.succeeded')
        self.mock_tracker.emit.assert_any_call(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.upgrade.succeeded',
            {
                'user_id': course_enrollment.user.id,
                'course_id': course_enrollment.course_id.to_deprecated_string(),
                'mode': course_enrollment.mode
            }
        )

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_show_receipt_success_refund(self):
        reg_item = PaidCourseRegistration.add_to_order(self.cart, self.course_key)
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
        self.assertIn(reg_item, context['order_items'])
        self.assertIn(cert_item, context['order_items'])
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


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class CSVReportViewsTest(ModuleStoreTestCase):
    """
    Test suite for CSV Purchase Reporting
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.cost = 40
        self.course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        self.course_key = self.course.id
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
        verified_course = CourseFactory.create(org='org', number='test', display_name='Test Course')

        self.verified_course_key = verified_course.id
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
        self.assertIn(_("Download CSV Reports"), response.content)

    @patch('shoppingcart.views.render_to_response', render_mock)
    def test_report_csv_bad_date(self):
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.post(reverse('payment_csv_report'), {'start_date': 'BAD', 'end_date': 'BAD', 'requested_report': 'itemized_purchase_report'})

        ((template, context), unused_kwargs) = render_mock.call_args
        self.assertEqual(template, 'shoppingcart/download_report.html')
        self.assertFalse(context['total_count_error'])
        self.assertTrue(context['date_fmt_error'])
        self.assertIn(_("There was an error in your date input.  It should be formatted as YYYY-MM-DD"),
                      response.content)

    CORRECT_CSV_NO_DATE_ITEMIZED_PURCHASE = ",1,purchased,1,40,40,usd,Registration for Course: Robot Super Course,"

    def test_report_csv_itemized(self):
        report_type = 'itemized_purchase_report'
        start_date = '1970-01-01'
        end_date = '2100-01-01'
        PaidCourseRegistration.add_to_order(self.cart, self.course_key)
        self.cart.purchase()
        self.login_user()
        self.add_to_download_group(self.user)
        response = self.client.post(reverse('payment_csv_report'), {'start_date': start_date,
                                                                    'end_date': end_date,
                                                                    'requested_report': report_type})
        self.assertEqual(response['Content-Type'], 'text/csv')
        report = initialize_report(report_type, start_date, end_date)
        self.assertIn(",".join(report.header()), response.content)
        self.assertIn(self.CORRECT_CSV_NO_DATE_ITEMIZED_PURCHASE, response.content)

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
