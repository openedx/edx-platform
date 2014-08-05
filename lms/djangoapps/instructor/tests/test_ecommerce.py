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
from shoppingcart.models import Coupon, PaidCourseRegistration, CourseRegistrationCode
from mock import patch
from student.roles import CourseFinanceAdminRole


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestECommerceDashboardViews(ModuleStoreTestCase):
    """
    Check for E-commerce view on the new instructor dashboard
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")
        mode = CourseMode(
            course_id=self.course.id.to_deprecated_string(), mode_slug='honor',
            mode_display_name='honor', min_price=10, currency='usd'
        )
        mode.save()
        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.e_commerce_link = '<a href="" data-section="e-commerce">E-Commerce</a>'
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)

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

    def test_user_has_finance_admin_rights_in_e_commerce_tab(self):
        response = self.client.get(self.url)
        self.assertTrue(self.e_commerce_link in response.content)

        # Total amount html should render in e-commerce page, total amount will be 0
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        self.assertTrue('<span>Total Amount: <span>$' + str(total_amount) + '</span></span>' in response.content)
        self.assertTrue('Download All e-Commerce Purchase' in response.content)

        # removing the course finance_admin role of login user
        CourseFinanceAdminRole(self.course.id).remove_users(self.instructor)

        # total amount should not be visible in e-commerce page if the user is not finance admin
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url)
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        self.assertFalse('Download All e-Commerce Purchase' in response.content)
        self.assertFalse('<span>Total Amount: <span>$' + str(total_amount) + '</span></span>' in response.content)

    def test_user_view_course_price(self):
        """
        test to check if the user views the set price button and price in
        the instructor dashboard
        """
        response = self.client.get(self.url)
        self.assertTrue(self.e_commerce_link in response.content)

        # Total amount html should render in e-commerce page, total amount will be 0
        course_honor_mode = CourseMode.mode_for_course(self.course.id, 'honor')

        price = course_honor_mode.min_price
        self.assertTrue('Course Price: <span>$' + str(price) + '</span>' in response.content)
        self.assertFalse('+ Set Price</a></span>' in response.content)

        # removing the course finance_admin role of login user
        CourseFinanceAdminRole(self.course.id).remove_users(self.instructor)

        # total amount should not be visible in e-commerce page if the user is not finance admin
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        self.assertFalse('+ Set Price</a></span>' in response.content)

    def test_update_course_price_check(self):
        price = 200
        # course B
        course2 = CourseFactory.create(org='EDX', display_name='test_course', number='100')
        mode = CourseMode(
            course_id=course2.id.to_deprecated_string(), mode_slug='honor',
            mode_display_name='honor', min_price=30, currency='usd'
        )
        mode.save()
        # course A update
        CourseMode.objects.filter(course_id=self.course.id).update(min_price=price)

        set_course_price_url = reverse('set_course_mode_price', kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {'course_price': price, 'currency': 'usd'}
        response = self.client.post(set_course_price_url, data)
        self.assertTrue('CourseMode price updated successfully' in response.content)

        # Course A updated total amount should be visible in e-commerce page if the user is finance admin
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)

        self.assertTrue('Course Price: <span>$' + str(price) + '</span>' in response.content)

    def test_user_admin_set_course_price(self):
        """
        test to set the course price related functionality.
        test al the scenarios for setting a new course price
        """
        set_course_price_url = reverse('set_course_mode_price', kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {'course_price': '12%', 'currency': 'usd'}

        # Value Error course price should be a numeric value
        response = self.client.post(set_course_price_url, data)
        self.assertTrue("Please Enter the numeric value for the course price" in response.content)

        # validation check passes and course price is successfully added
        data['course_price'] = 100
        response = self.client.post(set_course_price_url, data)
        self.assertTrue("CourseMode price updated successfully" in response.content)

        course_honor_mode = CourseMode.objects.get(mode_slug='honor')
        course_honor_mode.delete()
        # Course Mode not exist with mode slug honor
        response = self.client.post(set_course_price_url, data)
        self.assertTrue("CourseMode with the mode slug({mode_slug}) DoesNotExist".format(mode_slug='honor') in response.content)

    def test_add_coupon(self):
        """
        Test Add Coupon Scenarios. Handle all the HttpResponses return by add_coupon view
        """
        # URL for add_coupon
        add_coupon_url = reverse('add_coupon', kwargs={'course_id': self.course.id.to_deprecated_string()})
        data = {
            'code': 'A2314', 'course_id': self.course.id.to_deprecated_string(),
            'description': 'ADSADASDSAD', 'created_by': self.instructor, 'discount': 5
        }
        response = self.client.post(add_coupon_url, data)
        self.assertTrue("coupon with the coupon code ({code}) added successfully".format(code=data['code']) in response.content)

        data = {
            'code': 'A2314', 'course_id': self.course.id.to_deprecated_string(),
            'description': 'asdsasda', 'created_by': self.instructor, 'discount': 99
        }
        response = self.client.post(add_coupon_url, data)
        self.assertTrue("coupon with the coupon code ({code}) already exist".format(code='A2314') in response.content)

        response = self.client.post(self.url)
        self.assertTrue('<td>ADSADASDSAD</td>' in response.content)
        self.assertTrue('<td>A2314</td>' in response.content)
        self.assertFalse('<td>111</td>' in response.content)

        data = {
            'code': 'A2345314', 'course_id': self.course.id.to_deprecated_string(),
            'description': 'asdsasda', 'created_by': self.instructor, 'discount': 199
        }
        response = self.client.post(add_coupon_url, data)
        self.assertTrue("Please Enter the Coupon Discount Value Less than or Equal to 100" in response.content)

        data['discount'] = '25%'
        response = self.client.post(add_coupon_url, data=data)
        self.assertTrue('Please Enter the Integer Value for Coupon Discount' in response.content)

        course_registration = CourseRegistrationCode(
            code='Vs23Ws4j', course_id=self.course.id.to_deprecated_string(),
            transaction_group_name='Test Group', created_by=self.instructor
        )
        course_registration.save()

        data['code'] = 'Vs23Ws4j'
        response = self.client.post(add_coupon_url, data)
        self.assertTrue("The code ({code}) that you have tried to define is already in use as a registration code"
                        .format(code=data['code']) in response.content)

    def test_delete_coupon(self):
        """
        Test Delete Coupon Scenarios. Handle all the HttpResponses return by remove_coupon view
        """
        coupon = Coupon(
            code='AS452', description='asdsadsa', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=10, created_by=self.instructor
        )

        coupon.save()

        response = self.client.post(self.url)
        self.assertTrue('<td>AS452</td>' in response.content)

        # URL for remove_coupon
        delete_coupon_url = reverse('remove_coupon', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(delete_coupon_url, {'id': coupon.id})
        self.assertTrue('coupon with the coupon id ({coupon_id}) updated successfully'.format(coupon_id=coupon.id) in response.content)

        coupon.is_active = False
        coupon.save()

        response = self.client.post(delete_coupon_url, {'id': coupon.id})
        self.assertTrue('coupon with the coupon id ({coupon_id}) is already inactive'.format(coupon_id=coupon.id) in response.content)

        response = self.client.post(delete_coupon_url, {'id': 24454})
        self.assertTrue('coupon with the coupon id ({coupon_id}) DoesNotExist'.format(coupon_id=24454) in response.content)

        response = self.client.post(delete_coupon_url, {'id': ''})
        self.assertTrue('coupon id is None' in response.content)

    def test_get_coupon_info(self):
        """
        Test Edit Coupon Info Scenarios. Handle all the HttpResponses return by edit_coupon_info view
        """
        coupon = Coupon(
            code='AS452', description='asdsadsa', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=10, created_by=self.instructor
        )
        coupon.save()
        # URL for edit_coupon_info
        edit_url = reverse('get_coupon_info', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(edit_url, {'id': coupon.id})
        self.assertTrue('coupon with the coupon id ({coupon_id}) updated successfully'.format(coupon_id=coupon.id) in response.content)

        response = self.client.post(edit_url, {'id': 444444})
        self.assertTrue('coupon with the coupon id ({coupon_id}) DoesNotExist'.format(coupon_id=444444) in response.content)

        response = self.client.post(edit_url, {'id': ''})
        self.assertTrue('coupon id not found"' in response.content)

        coupon.is_active = False
        coupon.save()

        response = self.client.post(edit_url, {'id': coupon.id})
        self.assertTrue("coupon with the coupon id ({coupon_id}) is already inactive".format(coupon_id=coupon.id) in response.content)

    def test_update_coupon(self):
        """
        Test Update Coupon Info Scenarios. Handle all the HttpResponses return by update_coupon view
        """
        coupon = Coupon(
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
        update_coupon_url = reverse('update_coupon', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('coupon with the coupon id ({coupon_id}) updated Successfully'.format(coupon_id=coupon.id)in response.content)

        response = self.client.post(self.url)
        self.assertTrue('<td>update_code</td>' in response.content)
        self.assertTrue('<td>12</td>' in response.content)

        data['coupon_id'] = 1000  # Coupon Not Exist with this ID
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('coupon with the coupon id ({coupon_id}) DoesNotExist'.format(coupon_id=1000) in response.content)

        data['coupon_id'] = coupon.id
        data['discount'] = 123
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('Please Enter the Coupon Discount Value Less than or Equal to 100' in response.content)

        data['discount'] = '25%'
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('Please Enter the Integer Value for Coupon Discount' in response.content)

        data['coupon_id'] = ''  # Coupon id is not provided
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('coupon id not found' in response.content)

        coupon1 = Coupon(
            code='11111', description='coupon', course_id=self.course.id.to_deprecated_string(),
            percentage_discount=20, created_by=self.instructor
        )
        coupon1.save()
        data = {'coupon_id': coupon.id, 'code': '11111', 'discount': '12'}  # pylint: disable=E1101
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue('coupon with the coupon id ({coupon_id}) already exist'.format(coupon_id=coupon.id) in response.content)  # pylint: disable=E1101

        course_registration = CourseRegistrationCode(
            code='Vs23Ws4j', course_id=self.course.id.to_deprecated_string(),
            transaction_group_name='Test Group', created_by=self.instructor
        )
        course_registration.save()

        data = {'coupon_id': coupon.id, 'code': 'Vs23Ws4j',  # pylint: disable=E1101
                'discount': '6', 'course_id': coupon.course_id.to_deprecated_string()}  # pylint: disable=E1101
        response = self.client.post(update_coupon_url, data=data)
        self.assertTrue("The code ({code}) that you have tried to define is already in use as a registration code".
                        format(code=data['code']) in response.content)
