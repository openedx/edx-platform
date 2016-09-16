# -*- coding: utf-8 -*-
"""
Tests for Microsite Dashboard with Shopping Cart History
"""
import mock

from django.core.urlresolvers import reverse

from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from shoppingcart.models import (
    Order, PaidCourseRegistration, CertificateItem, Donation
)
from student.tests.factories import UserFactory
from course_modes.models import CourseMode


def fake_all_orgs(default=None):  # pylint: disable=unused-argument
    """
    create a fake list of all microsites
    """
    return set(['fakeX', 'fooX'])


def fakex_microsite(name, default=None):  # pylint: disable=unused-argument
    """
    create a fake microsite site name
    """
    return 'fakeX'


def non_microsite(name, default=None):  # pylint: disable=unused-argument
    """
    create a fake microsite site name
    """
    return None


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class TestOrderHistoryOnMicrositeDashboard(ModuleStoreTestCase):
    """
    Test for microsite dashboard order history
    """
    def setUp(self):
        super(TestOrderHistoryOnMicrositeDashboard, self).setUp()

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()

        self.addCleanup(patcher.stop)

        # First Order with our (fakeX) microsite's course.
        course1 = CourseFactory.create(org='fakeX', number='999', display_name='fakeX Course')
        course1_key = course1.id
        course1_mode = CourseMode(course_id=course1_key,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=20)
        course1_mode.save()

        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course1_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_microsite = cart.id

        # Second Order with another(fooX) microsite's course
        course2 = CourseFactory.create(org='fooX', number='888', display_name='fooX Course')
        course2_key = course2.id
        course2_mode = CourseMode(course_id=course2.id,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=20)
        course2_mode.save()

        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course2_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_other_microsite = cart.id

        # Third Order with course not attributed to any microsite.
        course3 = CourseFactory.create(org='otherorg', number='777', display_name='otherorg Course')
        course3_key = course3.id
        course3_mode = CourseMode(course_id=course3.id,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=20)
        course3_mode.save()

        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course3_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_non_microsite = cart.id

        # Fourth Order with course not attributed to any microsite but with a CertificateItem
        course4 = CourseFactory.create(org='otherorg', number='888')
        course4_key = course4.id
        course4_mode = CourseMode(course_id=course4.id,
                                  mode_slug="verified",
                                  mode_display_name="verified cert",
                                  min_price=20)
        course4_mode.save()

        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, course4_key, 20.0, 'verified')
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_cert_non_microsite = cart.id

        # Fifth Order with course not attributed to any microsite but with a Donation
        course5 = CourseFactory.create(org='otherorg', number='999')
        course5_key = course5.id

        cart = Order.get_cart_for_user(self.user)
        Donation.add_to_order(cart, 20.0, course5_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_donation = cart.id

        # also add a donation not associated with a course to make sure the None case works OK
        Donation.add_to_order(cart, 10.0, None)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.orderid_courseless_donation = cart.id

    @mock.patch("microsite_configuration.microsite.get_value", fakex_microsite)
    @mock.patch("microsite_configuration.microsite.get_all_orgs", fake_all_orgs)
    def test_when_in_microsite_shows_orders_with_microsite_courses_only(self):
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("dashboard"))
        receipt_url_microsite_course = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_microsite})
        receipt_url_microsite_course2 = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_other_microsite})
        receipt_url_non_microsite = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_non_microsite})
        receipt_url_cert_non_microsite = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_cert_non_microsite})
        receipt_url_donation = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_donation})

        # We need to decode because of these chars: © & ▸
        content = response.content.decode('utf-8')
        self.assertIn(receipt_url_microsite_course, content)
        self.assertNotIn(receipt_url_microsite_course2, content)
        self.assertNotIn(receipt_url_non_microsite, content)
        self.assertNotIn(receipt_url_cert_non_microsite, content)
        self.assertNotIn(receipt_url_donation, content)

    @mock.patch("microsite_configuration.microsite.get_value", non_microsite)
    @mock.patch("microsite_configuration.microsite.get_all_orgs", fake_all_orgs)
    def test_when_not_in_microsite_shows_orders_with_non_microsite_courses_only(self):
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("dashboard"))
        receipt_url_microsite_course = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_microsite})
        receipt_url_microsite_course2 = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_other_microsite})
        receipt_url_non_microsite = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_non_microsite})
        receipt_url_cert_non_microsite = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_cert_non_microsite})
        receipt_url_donation = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_donation})
        receipt_url_courseless_donation = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.orderid_courseless_donation})

        # We need to decode because of these chars: © & ▸
        content = response.content.decode('utf-8')
        self.assertNotIn(receipt_url_microsite_course, content)
        self.assertNotIn(receipt_url_microsite_course2, content)
        self.assertIn(receipt_url_non_microsite, content)
        self.assertIn(receipt_url_cert_non_microsite, content)
        self.assertIn(receipt_url_donation, content)
        self.assertIn(receipt_url_courseless_donation, content)
