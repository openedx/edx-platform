"""
Unit tests for Ecommerce feature flag in new instructor dashboard.
"""

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from course_modes.models import CourseMode
from shoppingcart.models import Coupons
from mock import patch


# pylint: disable=E1101
@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestECommerceDashboardViews(ModuleStoreTestCase):
    """
    Check for email view on the new instructor dashboard
    for Mongo-backed courses
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")
        mode = CourseMode(
            course_id=self.course.id, mode_slug='honor',
            mode_display_name='honor', min_price=10, currency='usd'
        )
        mode.save()
        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.e_commerce_link = '<a href="" data-section="e-commerce">E-Commerce</a>'

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    def test_pass_e_commerce_tab_in_instructor_dashboard(self):
        """
        Test Pass E-commerce Tab is in the Instructor Dashboard
        """
        response = self.client.get(self.url)
        self.assertTrue(self.e_commerce_link in response.content)

    def test_add_coupon(self):
        """
        Test Add Coupon Scenarios. Handle all the HttpResponses return by add_coupon view
        """
        # URL for add_coupon
        add_coupon_url = reverse('add_coupon')
        data = {
            'code': 'A2314', 'course_id': self.course.id.to_deprecated_string(),
            'description': 'ADSADASDSAD', 'created_by': self.instructor, 'discount': 5
        }
        response = self.client.post(add_coupon_url, data)
        data = {
            'code': 'A2314', 'course_id': self.course.id.to_deprecated_string(),
            'description': 'asdsasda', 'created_by': self.instructor, 'discount': 111
        }
        response = self.client.post(add_coupon_url, data)
        self.assertTrue("Coupon Already Exist" in response.content)

        response = self.client.post(self.url, data)
        self.assertTrue('<td>ADSADASDSAD</td>' in response.content)
        self.assertTrue('<td>A2314</td>' in response.content)
        self.assertFalse('<td>111</td>' in response.content)

    def test_delete_coupon(self):
        """
        Test Delete Coupon Scenarios. Handle all the HttpResponses return by remove_coupon view
        """
        coupon = Coupons(
            code='AS452', description='asdsadsa', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=10, created_by=self.instructor
        )

        coupon.save()

        response = self.client.post(self.url)
        self.assertTrue('<td>AS452</td>' in response.content)

        # URL for remove_coupon
        delete_coupon_url = reverse('remove_coupon')
        response = self.client.post(delete_coupon_url, {'id': coupon.id})
        self.assertTrue('coupon id={0} updated successfully'.format(coupon.id) in response.content)

        coupon.is_active = False
        coupon.save()

        response = self.client.post(delete_coupon_url, {'id': coupon.id})
        self.assertTrue('coupon id={0} is already inactive or request made by Anonymous User'.format(coupon.id) in response.content)

        response = self.client.post(delete_coupon_url, {'id': 24454})
        self.assertTrue('Cannot remove coupon Coupon id={0}. DoesNotExist or coupon is already deleted'.format(24454) in response.content)

    def test_edit_coupon_info(self):
        """
        Test Edit Coupon Info Scenarios. Handle all the HttpResponses return by edit_coupon_info view
        """
        coupon = Coupons(
            code='AS452', description='asdsadsa', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=10, created_by=self.instructor
        )
        coupon.save()
        # URL for edit_coupon_info
        edit_url = reverse('edit_coupon_info')
        response = self.client.post(edit_url, {'id': coupon.id})
        self.assertTrue('coupon id={0} fields updated successfully'.format(coupon.id) in response.content)

        response = self.client.post(edit_url, {'id': 444444})
        self.assertTrue('Coupon {0} not found'.format(444444) in response.content)

        coupon.is_active = False
        coupon.save()
        response = self.client.post(edit_url, {'id': coupon.id})
        self.assertTrue('"success": false' in response.content)

    def test_update_coupon(self):
        """
        Test Update Coupon Info Scenarios. Handle all the HttpResponses return by update_coupon view
        """
        coupon = Coupons(
            code='AS452', description='asdsadsa', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=10, created_by=self.instructor
        )
        coupon.save()
        response = self.client.post(self.url)
        self.assertTrue('<td>AS452</td>' in response.content)
        data = {
            'coupon_id': coupon.id, 'code': 'update_code', 'discount': '12',
            'course_id': coupon.course_id.to_deprecated_string()
        }
        # URL for update_coupon
        update_coupon_url = reverse('update_coupon')
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('Coupon {0} updated Successfully'.format(coupon.id)in response.content)

        response = self.client.post(self.url)
        self.assertTrue('<td>update_code</td>' in response.content)
        self.assertTrue('<td>12</td>' in response.content)

        data['coupon_id'] = 1000  # Coupon Not Exist with this ID
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('Coupon {0} not found'.format(1000)in response.content)

        coupon1 = Coupons(
            code='11111', description='coupon', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=20, created_by=self.instructor
        )
        coupon1.save()
        data = {'coupon_id': coupon.id, 'code': '11111', 'discount': '12'}
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('Coupon {0} Already Exist'.format(coupon.id) in response.content)
