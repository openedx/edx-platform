# -*- coding: utf-8 -*-
"""
Dashboard with Shopping Cart History tests with configuration overrides.
"""
from django.core.urlresolvers import reverse

from mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from shoppingcart.models import (
    Order, PaidCourseRegistration, CertificateItem, Donation
)
from student.tests.factories import UserFactory
from course_modes.models import CourseMode
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin


@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
class TestOrderHistoryOnSiteDashboard(SiteMixin, ModuleStoreTestCase):
    """
    Test for dashboard order history site configuration overrides.
    """
    def setUp(self):
        super(TestOrderHistoryOnSiteDashboard, self).setUp()

        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()

        self.addCleanup(patcher.stop)

        # First Order with our (fakeX) site's course.
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
        self.fakex_site_order_id = cart.id

        # Second Order with another(fooX) site's course
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
        self.foox_site_order_id = cart.id

        # Third Order with course not attributed to any site.
        course3 = CourseFactory.create(org='fakeOtherX', number='777', display_name='fakeOtherX Course')
        course3_key = course3.id
        course3_mode = CourseMode(course_id=course3.id,
                                  mode_slug="honor",
                                  mode_display_name="honor cert",
                                  min_price=20)
        course3_mode.save()

        cart = Order.get_cart_for_user(self.user)
        PaidCourseRegistration.add_to_order(cart, course3_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.order_id = cart.id

        # Fourth Order with course not attributed to any site but with a CertificateItem
        course4 = CourseFactory.create(org='fakeOtherX', number='888')
        course4_key = course4.id
        course4_mode = CourseMode(course_id=course4.id,
                                  mode_slug="verified",
                                  mode_display_name="verified cert",
                                  min_price=20)
        course4_mode.save()

        cart = Order.get_cart_for_user(self.user)
        CertificateItem.add_to_order(cart, course4_key, 20.0, 'verified')
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.certificate_order_id = cart.id

        # Fifth Order with course not attributed to any site but with a Donation
        course5 = CourseFactory.create(org='fakeOtherX', number='999')
        course5_key = course5.id

        cart = Order.get_cart_for_user(self.user)
        Donation.add_to_order(cart, 20.0, course5_key)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.donation_order_id = cart.id

        # also add a donation not associated with a course to make sure the None case works OK
        Donation.add_to_order(cart, 10.0, None)
        cart.purchase(first='FirstNameTesting123', street1='StreetTesting123')
        self.courseless_donation_order_id = cart.id

    def test_shows_orders_with_current_site_courses_only(self):
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("dashboard"))
        receipt_url_course = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.fakex_site_order_id})
        receipt_url_course2 = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.foox_site_order_id})
        receipt_url = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.order_id})
        receipt_url_cert = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.certificate_order_id})
        receipt_url_donation = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.donation_order_id})

        # We need to decode because of these chars: © & ▸
        content = response.content.decode('utf-8')
        self.assertIn(receipt_url_course, content)
        self.assertNotIn(receipt_url_course2, content)
        self.assertNotIn(receipt_url, content)
        self.assertNotIn(receipt_url_cert, content)
        self.assertNotIn(receipt_url_donation, content)

    def test_shows_orders_with_non_site_courses_only_when_no_configuration_override_exists(self):
        self.use_site(self.site_other)
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("dashboard"))
        receipt_url_course = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.fakex_site_order_id})
        receipt_url_course2 = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.foox_site_order_id})
        receipt_url = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.order_id})
        receipt_url_cert = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.certificate_order_id})
        receipt_url_donation = reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': self.donation_order_id})
        receipt_url_courseless_donation = reverse(
            'shoppingcart.views.show_receipt',
            kwargs={'ordernum': self.courseless_donation_order_id},
        )

        # We need to decode because of these chars: © & ▸
        content = response.content.decode('utf-8')
        self.assertNotIn(receipt_url_course, content)
        self.assertNotIn(receipt_url_course2, content)
        self.assertIn(receipt_url, content)
        self.assertIn(receipt_url_cert, content)
        self.assertIn(receipt_url_donation, content)
        self.assertIn(receipt_url_courseless_donation, content)
