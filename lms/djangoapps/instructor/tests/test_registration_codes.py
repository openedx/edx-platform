"""
Test for the registration code status information.
"""
from course_modes.models import CourseMode
from courseware.tests.factories import InstructorFactory
from xmodule.modulestore.tests.factories import CourseFactory
from django.utils.translation import ugettext as _
from shoppingcart.models import (
    Invoice, CourseRegistrationCodeInvoiceItem, CourseRegistrationCode,
    CourseRegCodeItem, Order, RegistrationCodeRedemption
)
from student.models import CourseEnrollment
from student.roles import CourseSalesAdminRole
from nose.plugins.attrib import attr
import json
from student.tests.factories import UserFactory, CourseModeFactory
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


@attr('shard_1')
@override_settings(REGISTRATION_CODE_LENGTH=8)
class TestCourseRegistrationCodeStatus(SharedModuleStoreTestCase):
    """
    Test registration code status.
    """
    @classmethod
    def setUpClass(cls):
        super(TestCourseRegistrationCodeStatus, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestCourseRegistrationCodeStatus, self).setUp()
        CourseModeFactory.create(course_id=self.course.id, min_price=50)
        self.instructor = InstructorFactory(course_key=self.course.id)
        self.client.login(username=self.instructor.username, password='test')
        CourseSalesAdminRole(self.course.id).add_users(self.instructor)

        # create testing invoice
        self.sale_invoice = Invoice.objects.create(
            total_amount=1234.32, company_name='Test1', company_contact_name='TestName',
            company_contact_email='Test@company.com', recipient_name='Testw', recipient_email='test1@test.com',
            customer_reference_number='2Fwe23S', internal_reference="A", course_id=self.course.id, is_valid=True
        )
        self.invoice_item = CourseRegistrationCodeInvoiceItem.objects.create(
            invoice=self.sale_invoice,
            qty=1,
            unit_price=1234.32,
            course_id=self.course.id
        )
        self.lookup_code_url = reverse('look_up_registration_code',
                                       kwargs={'course_id': unicode(self.course.id)})

        self.registration_code_detail_url = reverse('registration_code_details',
                                                    kwargs={'course_id': unicode(self.course.id)})

        url = reverse('generate_registration_codes',
                      kwargs={'course_id': self.course.id.to_deprecated_string()})

        data = {
            'total_registration_codes': 12,
            'company_name': 'Test Group',
            'company_contact_name': 'Test@company.com',
            'company_contact_email': 'Test@company.com',
            'unit_price': 122.45,
            'recipient_name': 'Test123',
            'recipient_email': 'test@123.com',
            'address_line_1': 'Portland Street',
            'address_line_2': '',
            'address_line_3': '',
            'city': '',
            'state': '',
            'zip': '',
            'country': '',
            'customer_reference_number': '123A23F',
            'internal_reference': '',
            'invoice': ''
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200, response.content)

    def test_look_up_invalid_registration_code(self):
        """
        Verify the view returns HTTP status 400 if an invalid registration code is passed.
        Also, verify the data returned includes a message indicating the error,
        and the is_registration_code_valid is set to False.
        """
        data = {
            'registration_code': 'invalid_reg_code'
        }
        response = self.client.get(self.lookup_code_url, data)
        self.assertEqual(response.status_code, 400)
        json_dict = json.loads(response.content)
        message = _('The enrollment code ({code}) was not found for the {course_name} course.').format(
            course_name=self.course.display_name, code=data['registration_code']
        )
        self.assertEqual(message, json_dict['message'])
        self.assertFalse(json_dict['is_registration_code_valid'])
        self.assertFalse(json_dict['is_registration_code_redeemed'])

    def test_look_up_valid_registration_code(self):
        """
        test lookup for the valid registration code
        and that registration code has been redeemed by user
        and then mark the registration code as in_valid
        when marking as invalidate, it also lookup for
        registration redemption entry and also delete
        that redemption entry and un_enroll the student
        who used that registration code for their enrollment.
        """
        for i in range(2):
            CourseRegistrationCode.objects.create(
                code='reg_code{}'.format(i),
                course_id=unicode(self.course.id),
                created_by=self.instructor,
                invoice=self.sale_invoice,
                invoice_item=self.invoice_item,
                mode_slug=CourseMode.DEFAULT_MODE_SLUG
            )

        reg_code = CourseRegistrationCode.objects.all()[0]
        student = UserFactory()
        enrollment = CourseEnrollment.enroll(student, self.course.id)

        RegistrationCodeRedemption.objects.create(
            registration_code=reg_code,
            redeemed_by=student,
            course_enrollment=enrollment
        )

        data = {
            'registration_code': reg_code.code
        }
        response = self.client.get(self.lookup_code_url, data)
        self.assertEqual(response.status_code, 200)
        json_dict = json.loads(response.content)
        self.assertTrue(json_dict['is_registration_code_valid'])
        self.assertTrue(json_dict['is_registration_code_redeemed'])

        # now mark that registration code as invalid
        data = {
            'registration_code': reg_code.code,
            'action_type': 'invalidate_registration_code'
        }
        response = self.client.post(self.registration_code_detail_url, data)
        self.assertEqual(response.status_code, 200)

        json_dict = json.loads(response.content)
        message = _('This enrollment code has been canceled. It can no longer be used.')
        self.assertEqual(message, json_dict['message'])

        # now check that the registration code should be marked as invalid in the db.
        reg_code = CourseRegistrationCode.objects.get(code=reg_code.code)
        self.assertEqual(reg_code.is_valid, False)

        redemption = RegistrationCodeRedemption.get_registration_code_redemption(reg_code.code, self.course.id)
        self.assertIsNone(redemption)

        # now the student course enrollment should be false.
        enrollment = CourseEnrollment.get_enrollment(student, self.course.id)
        self.assertEqual(enrollment.is_active, False)

    def test_lookup_valid_redeemed_registration_code(self):
        """
        test to lookup for the valid and redeemed registration code
        and then mark that registration code as un_redeemed
        which will unenroll the user and delete the redemption
        entry from the database.
        """
        student = UserFactory()
        self.client.login(username=student.username, password='test')
        cart = Order.get_cart_for_user(student)
        cart.order_type = 'business'
        cart.save()
        CourseRegCodeItem.add_to_order(cart, self.course.id, 2)
        cart.purchase()

        reg_code = CourseRegistrationCode.objects.filter(order=cart)[0]

        enrollment = CourseEnrollment.enroll(student, self.course.id)

        RegistrationCodeRedemption.objects.create(
            registration_code=reg_code,
            redeemed_by=student,
            course_enrollment=enrollment
        )
        self.client.login(username=self.instructor.username, password='test')
        data = {
            'registration_code': reg_code.code
        }
        response = self.client.get(self.lookup_code_url, data)
        self.assertEqual(response.status_code, 200)
        json_dict = json.loads(response.content)
        self.assertTrue(json_dict['is_registration_code_valid'])
        self.assertTrue(json_dict['is_registration_code_redeemed'])

        # now mark the registration code as unredeemed
        # this will unenroll the user and removed the redemption entry from
        # the database.

        data = {
            'registration_code': reg_code.code,
            'action_type': 'unredeem_registration_code'
        }
        response = self.client.post(self.registration_code_detail_url, data)
        self.assertEqual(response.status_code, 200)

        json_dict = json.loads(response.content)
        message = _('This enrollment code has been marked as unused.')
        self.assertEqual(message, json_dict['message'])

        redemption = RegistrationCodeRedemption.get_registration_code_redemption(reg_code.code, self.course.id)
        self.assertIsNone(redemption)

        # now the student course enrollment should be false.
        enrollment = CourseEnrollment.get_enrollment(student, self.course.id)
        self.assertEqual(enrollment.is_active, False)

    def test_apply_invalid_reg_code_when_updating_code_information(self):
        """
        test to apply an invalid registration code
        when updating the registration code information.
        """
        data = {
            'registration_code': 'invalid_registration_code',
            'action_type': 'unredeem_registration_code'
        }
        response = self.client.post(self.registration_code_detail_url, data)
        self.assertEqual(response.status_code, 400)

        json_dict = json.loads(response.content)
        message = _('The enrollment code ({code}) was not found for the {course_name} course.').format(
            course_name=self.course.display_name, code=data['registration_code']
        )
        self.assertEqual(message, json_dict['message'])

    def test_mark_registration_code_as_valid(self):
        """
        test to mark the invalid registration code
        as valid
        """
        for i in range(2):
            CourseRegistrationCode.objects.create(
                code='reg_code{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice,
                invoice_item=self.invoice_item,
                mode_slug=CourseMode.DEFAULT_MODE_SLUG,
                is_valid=False
            )

        reg_code = CourseRegistrationCode.objects.all()[0]
        data = {
            'registration_code': reg_code.code,
            'action_type': 'validate_registration_code'
        }
        response = self.client.post(self.registration_code_detail_url, data)
        self.assertEqual(response.status_code, 200)

        json_dict = json.loads(response.content)
        message = _('The enrollment code has been restored.')
        self.assertEqual(message, json_dict['message'])

        # now check that the registration code should be marked as valid in the db.
        reg_code = CourseRegistrationCode.objects.get(code=reg_code.code)
        self.assertEqual(reg_code.is_valid, True)

    def test_returns_error_when_unredeeming_already_unredeemed_registration_code_redemption(self):
        """
        test to mark the already unredeemed registration code as unredeemed.
        """
        for i in range(2):
            CourseRegistrationCode.objects.create(
                code='reg_code{}'.format(i),
                course_id=self.course.id.to_deprecated_string(),
                created_by=self.instructor,
                invoice=self.sale_invoice,
                invoice_item=self.invoice_item,
                mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            )

        reg_code = CourseRegistrationCode.objects.all()[0]
        data = {
            'registration_code': reg_code.code,
            'action_type': 'unredeem_registration_code'
        }
        response = self.client.post(self.registration_code_detail_url, data)
        self.assertEqual(response.status_code, 400)

        json_dict = json.loads(response.content)
        message = _('The redemption does not exist against enrollment code ({code}).').format(code=reg_code.code)
        self.assertEqual(message, json_dict['message'])
