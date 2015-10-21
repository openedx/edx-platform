"""
Defines concrete class for cybersource  Enrollment Report.

"""
from courseware.access import has_access
import collections
from django.conf import settings
from django.utils.translation import ugettext as _
from courseware.courses import get_course_by_id
from instructor.enrollment_report import BaseAbstractEnrollmentReportProvider
from microsite_configuration import microsite
from shoppingcart.models import RegistrationCodeRedemption, PaidCourseRegistration, CouponRedemption, OrderItem, \
    InvoiceTransaction
from student.models import CourseEnrollment, ManualEnrollmentAudit


class PaidCourseEnrollmentReportProvider(BaseAbstractEnrollmentReportProvider):
    """
    The concrete class for all CyberSource Enrollment Reports.
    """

    def get_enrollment_info(self, user, course_id):
        """
        Returns the User Enrollment information.
        """
        course = get_course_by_id(course_id, depth=0)
        is_course_staff = bool(has_access(user, 'staff', course))

        # check the user enrollment role
        if user.is_staff:
            platform_name = microsite.get_value('platform_name', settings.PLATFORM_NAME)
            enrollment_role = _('{platform_name} Staff').format(platform_name=platform_name)
        elif is_course_staff:
            enrollment_role = _('Course Staff')
        else:
            enrollment_role = _('Student')

        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)

        if is_course_staff:
            enrollment_source = _('Staff')
        else:
            # get the registration_code_redemption object if exists
            registration_code_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(
                course_enrollment)
            # get the paid_course registration item if exists
            paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
                user=user,
                course_id=course_id,
                course_enrollment=course_enrollment
            )

            # from where the user get here
            if registration_code_redemption is not None:
                enrollment_source = _('Used Registration Code')
            elif paid_course_reg_item is not None:
                enrollment_source = _('Credit Card - Individual')
            else:
                manual_enrollment = ManualEnrollmentAudit.get_manual_enrollment(course_enrollment)
                if manual_enrollment is not None:
                    enrollment_source = _(
                        'manually enrolled by {username} - reason: {reason}'
                    ).format(username=manual_enrollment.enrolled_by.username, reason=manual_enrollment.reason)
                else:
                    enrollment_source = _('Manually Enrolled')

        enrollment_date = course_enrollment.created.strftime("%B %d, %Y")
        currently_enrolled = course_enrollment.is_active

        course_enrollment_data = collections.OrderedDict()
        course_enrollment_data['Enrollment Date'] = enrollment_date
        course_enrollment_data['Currently Enrolled'] = currently_enrolled
        course_enrollment_data['Enrollment Source'] = enrollment_source
        course_enrollment_data['Enrollment Role'] = enrollment_role
        return course_enrollment_data

    def get_payment_info(self, user, course_id):
        """
        Returns the User Payment information.
        """
        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)
        paid_course_reg_item = PaidCourseRegistration.get_course_item_for_user_enrollment(
            user=user,
            course_id=course_id,
            course_enrollment=course_enrollment
        )
        payment_data = collections.OrderedDict()
        # check if the user made a single self purchase scenario
        # for enrollment in the course.
        if paid_course_reg_item is not None:
            coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(
                order_id=paid_course_reg_item.order_id)
            coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
            coupon_codes = ", ".join(coupon_codes)
            registration_code_used = 'N/A'

            list_price = paid_course_reg_item.get_list_price()
            payment_amount = paid_course_reg_item.unit_cost
            coupon_codes_used = coupon_codes
            payment_status = paid_course_reg_item.status
            transaction_reference_number = paid_course_reg_item.order_id

        else:
            # check if the user used a registration code for the enrollment.
            registration_code_redemption = RegistrationCodeRedemption.registration_code_used_for_enrollment(
                course_enrollment)
            if registration_code_redemption is not None:
                registration_code = registration_code_redemption.registration_code
                registration_code_used = registration_code.code
                if getattr(registration_code, 'invoice_item_id'):
                    list_price, payment_amount, payment_status, transaction_reference_number =\
                        self._get_invoice_data(registration_code_redemption)
                    coupon_codes_used = 'N/A'

                elif getattr(registration_code_redemption.registration_code, 'order_id'):
                    list_price, payment_amount, coupon_codes_used, payment_status, transaction_reference_number = \
                        self._get_order_data(registration_code_redemption, course_id)

                else:
                    # this happens when the registration code is not created via invoice or bulk purchase
                    # scenario.
                    list_price = 'N/A'
                    payment_amount = 'N/A'
                    coupon_codes_used = 'N/A'
                    registration_code_used = 'N/A'
                    payment_status = _('Data Integrity Error')
                    transaction_reference_number = 'N/A'
            else:
                list_price = 'N/A'
                payment_amount = 'N/A'
                coupon_codes_used = 'N/A'
                registration_code_used = 'N/A'
                payment_status = _('TBD')
                transaction_reference_number = 'N/A'

        payment_data['List Price'] = list_price
        payment_data['Payment Amount'] = payment_amount
        payment_data['Coupon Codes Used'] = coupon_codes_used
        payment_data['Registration Code Used'] = registration_code_used
        payment_data['Payment Status'] = payment_status
        payment_data['Transaction Reference Number'] = transaction_reference_number
        return payment_data

    def _get_order_data(self, registration_code_redemption, course_id):
        """
        Returns the order data
        """
        order_item = OrderItem.objects.get(order=registration_code_redemption.registration_code.order,
                                           courseregcodeitem__course_id=course_id)
        coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(
            order_id=registration_code_redemption.registration_code.order)
        coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
        coupon_codes = ", ".join(coupon_codes)

        list_price = order_item.get_list_price()
        payment_amount = order_item.unit_cost
        coupon_codes_used = coupon_codes
        payment_status = order_item.status
        transaction_reference_number = order_item.order_id
        return list_price, payment_amount, coupon_codes_used, payment_status, transaction_reference_number

    def _get_invoice_data(self, registration_code_redemption):
        """
        Returns the Invoice data
        """
        registration_code = registration_code_redemption.registration_code
        list_price = getattr(registration_code.invoice_item, 'unit_price')
        total_amount = registration_code_redemption.registration_code.invoice.total_amount
        qty = registration_code_redemption.registration_code.invoice_item.qty
        payment_amount = total_amount / qty
        invoice_transaction = InvoiceTransaction.get_invoice_transaction(
            invoice_id=registration_code_redemption.registration_code.invoice.id)
        if invoice_transaction is not None:
            # amount greater than 0 is invoice has bee paid
            if invoice_transaction.amount > 0:
                payment_status = 'Invoice Paid'
            else:
                # amount less than 0 is invoice has been refunded
                payment_status = 'Refunded'
        else:
            payment_status = 'Invoice Outstanding'
        transaction_reference_number = registration_code_redemption.registration_code.invoice_id
        return list_price, payment_amount, payment_status, transaction_reference_number
