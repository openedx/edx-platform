"""
Instructor tasks related to enrollments.
"""


import logging
from datetime import datetime
from time import time

from django.conf import settings
from django.utils.translation import ugettext as _
from pytz import UTC
from six import StringIO

from edxmako.shortcuts import render_to_string
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.instructor.paidcourse_enrollment_report import PaidCourseEnrollmentReportProvider
from lms.djangoapps.instructor_analytics.basic import enrolled_students_features, list_may_enroll
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor_task.models import ReportStore
from shoppingcart.models import (
    CouponRedemption,
    CourseRegCodeItem,
    CourseRegistrationCode,
    Invoice,
    InvoiceTransaction,
    PaidCourseRegistration,
    RegistrationCodeRedemption
)
from student.models import CourseAccessRole, CourseEnrollment
from util.file import course_filename_prefix_generator

from .runner import TaskProgress
from .utils import tracker_emit, upload_csv_to_report_store

TASK_LOG = logging.getLogger('edx.celery.task')
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']


def upload_enrollment_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    students_in_course = CourseEnrollment.objects.enrolled_and_dropped_out_users(course_id)
    task_progress = TaskProgress(action_name, students_in_course.count(), start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    # Loop over all our students and build our CSV lists in memory
    rows = []
    header = None
    current_step = {'step': 'Gathering Profile Information'}
    enrollment_report_provider = PaidCourseEnrollmentReportProvider()
    total_students = students_in_course.count()
    student_counter = 0
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, generating detailed enrollment report for total students: %s',
        task_info_string,
        action_name,
        current_step,
        total_students
    )

    for student in students_in_course:
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        # Now add a log entry after certain intervals to get a hint that task is in progress
        student_counter += 1
        if student_counter % 100 == 0:
            TASK_LOG.info(
                u'%s, Task type: %s, Current step: %s, gathering enrollment profile for students in progress: %s/%s',
                task_info_string,
                action_name,
                current_step,
                student_counter,
                total_students
            )

        user_data = enrollment_report_provider.get_user_profile(student.id)
        course_enrollment_data = enrollment_report_provider.get_enrollment_info(student, course_id)
        payment_data = enrollment_report_provider.get_payment_info(student, course_id)

        # display name map for the column headers
        enrollment_report_headers = {
            'User ID': _('User ID'),
            'Username': _('Username'),
            'Full Name': _('Full Name'),
            'First Name': _('First Name'),
            'Last Name': _('Last Name'),
            'Company Name': _('Company Name'),
            'Title': _('Title'),
            'Language': _('Language'),
            'Year of Birth': _('Year of Birth'),
            'Gender': _('Gender'),
            'Level of Education': _('Level of Education'),
            'Mailing Address': _('Mailing Address'),
            'Goals': _('Goals'),
            'City': _('City'),
            'Country': _('Country'),
            'Enrollment Date': _('Enrollment Date'),
            'Currently Enrolled': _('Currently Enrolled'),
            'Enrollment Source': _('Enrollment Source'),
            'Manual (Un)Enrollment Reason': _('Manual (Un)Enrollment Reason'),
            'Enrollment Role': _('Enrollment Role'),
            'List Price': _('List Price'),
            'Payment Amount': _('Payment Amount'),
            'Coupon Codes Used': _('Coupon Codes Used'),
            'Registration Code Used': _('Registration Code Used'),
            'Payment Status': _('Payment Status'),
            'Transaction Reference Number': _('Transaction Reference Number')
        }

        if not header:
            header = list(user_data.keys()) + list(course_enrollment_data.keys()) + list(payment_data.keys())
            display_headers = []
            for header_element in header:
                # translate header into a localizable display string
                display_headers.append(enrollment_report_headers.get(header_element, header_element))
            rows.append(display_headers)

        rows.append(list(user_data.values()) + list(course_enrollment_data.values()) + list(payment_data.values()))
        task_progress.succeeded += 1

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Detailed enrollment report generated for students: %s/%s',
        task_info_string,
        action_name,
        current_step,
        student_counter,
        total_students
    )

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'enrollment_report', course_id, start_date, config_name='FINANCIAL_REPORTS')

    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing detailed enrollment task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def upload_may_enroll_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about students who may enroll but have not done so
    yet, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about students who may enroll'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    student_data = list_may_enroll(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'may_enroll_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_students_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    current_step = {'step': 'Calculating Profile Info'}
    task_progress.update_task_state(extra_meta=current_step)

    # compute the student features table and format it
    query_features = task_input
    student_data = enrolled_students_features(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'student_profile_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def get_executive_report(course_id):
    """
    Returns dict containing information about the course executive summary.
    """
    single_purchase_total = PaidCourseRegistration.get_total_amount_of_purchased_item(course_id)
    bulk_purchase_total = CourseRegCodeItem.get_total_amount_of_purchased_item(course_id)
    paid_invoices_total = InvoiceTransaction.get_total_amount_of_paid_course_invoices(course_id)
    gross_paid_revenue = single_purchase_total + bulk_purchase_total + paid_invoices_total

    all_invoices_total = Invoice.get_invoice_total_amount_for_course(course_id)
    gross_pending_revenue = all_invoices_total - float(paid_invoices_total)

    gross_revenue = float(gross_paid_revenue) + float(gross_pending_revenue)

    refunded_self_purchased_seats = PaidCourseRegistration.get_self_purchased_seat_count(
        course_id, status='refunded'
    )
    refunded_bulk_purchased_seats = CourseRegCodeItem.get_bulk_purchased_seat_count(
        course_id, status='refunded'
    )
    total_seats_refunded = refunded_self_purchased_seats + refunded_bulk_purchased_seats

    self_purchased_refunds = PaidCourseRegistration.get_total_amount_of_purchased_item(
        course_id,
        status='refunded'
    )
    bulk_purchase_refunds = CourseRegCodeItem.get_total_amount_of_purchased_item(course_id, status='refunded')
    total_amount_refunded = self_purchased_refunds + bulk_purchase_refunds

    top_discounted_codes = CouponRedemption.get_top_discount_codes_used(course_id)
    total_coupon_codes_purchases = CouponRedemption.get_total_coupon_code_purchases(course_id)

    bulk_purchased_codes = CourseRegistrationCode.order_generated_registration_codes(course_id)

    unused_registration_codes = 0
    for registration_code in bulk_purchased_codes:
        if not RegistrationCodeRedemption.is_registration_code_redeemed(registration_code.code):
            unused_registration_codes += 1

    self_purchased_seat_count = PaidCourseRegistration.get_self_purchased_seat_count(course_id)
    bulk_purchased_seat_count = CourseRegCodeItem.get_bulk_purchased_seat_count(course_id)
    total_invoiced_seats = CourseRegistrationCode.invoice_generated_registration_codes(course_id).count()

    total_seats = self_purchased_seat_count + bulk_purchased_seat_count + total_invoiced_seats

    self_purchases_percentage = 0.0
    bulk_purchases_percentage = 0.0
    invoice_purchases_percentage = 0.0
    avg_price_paid = 0.0

    if total_seats != 0:
        self_purchases_percentage = (float(self_purchased_seat_count) / float(total_seats)) * 100
        bulk_purchases_percentage = (float(bulk_purchased_seat_count) / float(total_seats)) * 100
        invoice_purchases_percentage = (float(total_invoiced_seats) / float(total_seats)) * 100
        avg_price_paid = gross_revenue / total_seats

    course = get_course_by_id(course_id, depth=0)
    currency = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]

    return {
        'display_name': course.display_name,
        'start_date': course.start.strftime("%Y-%m-%d") if course.start is not None else 'N/A',
        'end_date': course.end.strftime("%Y-%m-%d") if course.end is not None else 'N/A',
        'total_seats': total_seats,
        'currency': currency,
        'gross_revenue': float(gross_revenue),
        'gross_paid_revenue': float(gross_paid_revenue),
        'gross_pending_revenue': gross_pending_revenue,
        'total_seats_refunded': total_seats_refunded,
        'total_amount_refunded': float(total_amount_refunded),
        'average_paid_price': float(avg_price_paid),
        'discount_codes_data': top_discounted_codes,
        'total_seats_using_discount_codes': total_coupon_codes_purchases,
        'total_self_purchase_seats': self_purchased_seat_count,
        'total_bulk_purchase_seats': bulk_purchased_seat_count,
        'total_invoiced_seats': total_invoiced_seats,
        'unused_bulk_purchase_code_count': unused_registration_codes,
        'self_purchases_percentage': self_purchases_percentage,
        'bulk_purchases_percentage': bulk_purchases_percentage,
        'invoice_purchases_percentage': invoice_purchases_percentage,
    }


def upload_exec_summary_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing information,
    which provides a snapshot of how the course is doing.
    """
    start_time = time()
    report_generation_date = datetime.now(UTC)
    status_interval = 100

    enrolled_users = CourseEnrollment.objects.users_enrolled_in(course_id)
    true_enrollment_count = 0
    for user in enrolled_users:
        if not user.is_staff and not CourseAccessRole.objects.filter(
                user=user, course_id=course_id, role__in=FILTERED_OUT_ROLES
        ).exists():
            true_enrollment_count += 1

    task_progress = TaskProgress(action_name, true_enrollment_count, start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )

    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)
    current_step = {'step': 'Gathering executive summary report information'}

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, generating executive summary report',
        task_info_string,
        action_name,
        current_step
    )

    if task_progress.attempted % status_interval == 0:
        task_progress.update_task_state(extra_meta=current_step)
    task_progress.attempted += 1

    # get the course executive summary report information.
    data_dict = get_executive_report(course_id)
    data_dict.update(
        {
            'total_enrollments': true_enrollment_count,
            'report_generation_date': report_generation_date.strftime("%Y-%m-%d"),
        }
    )

    # By this point, we've got the data that we need to generate html report.
    current_step = {'step': 'Uploading executive summary report HTML file'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    _upload_exec_summary_to_store(data_dict, 'executive_report', course_id, report_generation_date)
    task_progress.succeeded += 1
    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing executive summary report task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def _upload_exec_summary_to_store(data_dict, report_name, course_id, generated_at, config_name='FINANCIAL_REPORTS'):
    """
    Upload Executive Summary Html file using ReportStore.

    Arguments:
        data_dict: containing executive report data.
        report_name: Name of the resulting Html File.
        course_id: ID of the course
    """
    report_store = ReportStore.from_config(config_name)

    # Use the data dict and html template to generate the output buffer
    output_buffer = StringIO(render_to_string("instructor/instructor_dashboard_2/executive_summary.html", data_dict))

    report_store.store(
        course_id,
        u"{course_prefix}_{report_name}_{timestamp_str}.html".format(
            course_prefix=course_filename_prefix_generator(course_id),
            report_name=report_name,
            timestamp_str=generated_at.strftime("%Y-%m-%d-%H%M")
        ),
        output_buffer,
    )
    tracker_emit(report_name)
