"""
Student and course analytics.

Serve miscellaneous course and student data
"""


import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F
from django.urls import reverse
from edx_proctoring.api import get_exam_violation_report
from opaque_keys.edx.keys import CourseKey, UsageKey

import xmodule.graders as xmgraders
from common.djangoapps.student.models import CourseEnrollment, CourseEnrollmentAllowed
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.grades.api import context as grades_context
from lms.djangoapps.program_enrollments.api import fetch_program_enrollments_by_students
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.markup import HTML, Text

log = logging.getLogger(__name__)


STUDENT_FEATURES = ('id', 'username', 'first_name', 'last_name', 'is_staff', 'email',
                    'date_joined', 'last_login')
PROFILE_FEATURES = ('name', 'language', 'location', 'year_of_birth', 'gender',
                    'level_of_education', 'mailing_address', 'goals', 'meta',
                    'city', 'country')
PROGRAM_ENROLLMENT_FEATURES = ('external_user_key', )
ORDER_ITEM_FEATURES = ('list_price', 'unit_cost', 'status')
ORDER_FEATURES = ('purchase_time',)

SALE_FEATURES = ('total_amount', 'company_name', 'company_contact_name', 'company_contact_email', 'recipient_name',
                 'recipient_email', 'customer_reference_number', 'internal_reference', 'created')

SALE_ORDER_FEATURES = ('id', 'company_name', 'company_contact_name', 'company_contact_email', 'purchase_time',
                       'customer_reference_number', 'recipient_name', 'recipient_email', 'bill_to_street1',
                       'bill_to_street2', 'bill_to_city', 'bill_to_state', 'bill_to_postalcode',
                       'bill_to_country', 'order_type', 'created')

AVAILABLE_FEATURES = STUDENT_FEATURES + PROFILE_FEATURES + PROGRAM_ENROLLMENT_FEATURES
COURSE_REGISTRATION_FEATURES = ('code', 'course_id', 'created_by', 'created_at', 'is_valid')
COUPON_FEATURES = ('code', 'course_id', 'percentage_discount', 'description', 'expiration_date', 'is_active')
CERTIFICATE_FEATURES = ('course_id', 'mode', 'status', 'grade', 'created_date', 'is_active', 'error_reason')

UNAVAILABLE = "[unavailable]"


def issued_certificates(course_key, features):
    """
    Return list of issued certificates as dictionaries against the given course key.

    issued_certificates(course_key, features)
    would return [
        {course_id: 'abc', 'total_issued_certificate': '5', 'mode': 'honor'}
        {course_id: 'abc', 'total_issued_certificate': '10', 'mode': 'verified'}
        {course_id: 'abc', 'total_issued_certificate': '15', 'mode': 'Professional Education'}
    ]
    """

    report_run_date = datetime.date.today().strftime("%B %d, %Y")
    certificate_features = [x for x in CERTIFICATE_FEATURES if x in features]
    generated_certificates = list(GeneratedCertificate.eligible_certificates.filter(
        course_id=course_key,
        status=CertificateStatuses.downloadable
    ).values(*certificate_features).annotate(total_issued_certificate=Count('mode')))

    # Report run date
    for data in generated_certificates:
        data['report_run_date'] = report_run_date
        data['course_id'] = str(data['course_id'])

    return generated_certificates


def enrolled_students_features(course_key, features):
    """
    Return list of student features as dictionaries.

    enrolled_students_features(course_key, ['username', 'first_name'])
    would return [
        {'username': 'username1', 'first_name': 'firstname1'}
        {'username': 'username2', 'first_name': 'firstname2'}
        {'username': 'username3', 'first_name': 'firstname3'}
    ]
    """
    include_cohort_column = 'cohort' in features
    include_team_column = 'team' in features
    include_city_column = 'city' in features
    include_enrollment_mode = 'enrollment_mode' in features
    include_verification_status = 'verification_status' in features
    include_program_enrollments = 'external_user_key' in features
    external_user_key_dict = {}

    students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
    ).order_by('username').select_related('profile')

    if include_cohort_column:
        students = students.prefetch_related('course_groups')

    if include_team_column:
        students = students.prefetch_related('teams')

    if include_program_enrollments and len(students) > 0:
        program_enrollments = fetch_program_enrollments_by_students(users=students, realized_only=True)
        for program_enrollment in program_enrollments:
            external_user_key_dict[program_enrollment.user_id] = program_enrollment.external_user_key

    def extract_attr(student, feature):
        """Evaluate a student attribute that is ready for JSON serialization"""
        attr = getattr(student, feature)
        try:
            DjangoJSONEncoder().default(attr)
            return attr
        except TypeError:
            return str(attr)

    def extract_student(student, features):
        """ convert student to dictionary """
        student_features = [x for x in STUDENT_FEATURES if x in features]
        profile_features = [x for x in PROFILE_FEATURES if x in features]

        # For data extractions on the 'meta' field
        # the feature name should be in the format of 'meta.foo' where
        # 'foo' is the keyname in the meta dictionary
        meta_features = []
        for feature in features:
            if 'meta.' in feature:
                meta_key = feature.split('.')[1]
                meta_features.append((feature, meta_key))

        student_dict = {feature: extract_attr(student, feature) for feature in student_features}
        profile = student.profile
        if profile is not None:
            profile_dict = {feature: extract_attr(profile, feature) for feature in profile_features}
            student_dict.update(profile_dict)

            # now fetch the requested meta fields
            meta_dict = json.loads(profile.meta) if profile.meta else {}
            for meta_feature, meta_key in meta_features:
                student_dict[meta_feature] = meta_dict.get(meta_key)

            # There are two separate places where the city value can be stored,
            # one used by account settings and the other used by the registration form.
            # If the account settings value (meta.city) is set, it takes precedence.
            meta_city = meta_dict.get('city')
            if include_city_column and meta_city:
                student_dict['city'] = meta_city

        if include_cohort_column:
            # Note that we use student.course_groups.all() here instead of
            # student.course_groups.filter(). The latter creates a fresh query,
            # therefore negating the performance gain from prefetch_related().
            student_dict['cohort'] = next(
                (cohort.name for cohort in student.course_groups.all() if cohort.course_id == course_key),
                "[unassigned]"
            )

        if include_team_column:
            student_dict['team'] = next(
                (team.name for team in student.teams.all() if team.course_id == course_key),
                UNAVAILABLE
            )

        if include_enrollment_mode or include_verification_status:
            enrollment_mode = CourseEnrollment.enrollment_mode_for_user(student, course_key)[0]
            if include_verification_status:
                student_dict['verification_status'] = IDVerificationService.verification_status_for_user(
                    student,
                    enrollment_mode
                )
            if include_enrollment_mode:
                student_dict['enrollment_mode'] = enrollment_mode

        if include_program_enrollments:
            # extra external_user_key
            student_dict['external_user_key'] = external_user_key_dict.get(student.id, '')

        return student_dict

    return [extract_student(student, features) for student in students]


def list_may_enroll(course_key, features):
    """
    Return info about students who may enroll in a course as a dict.

    list_may_enroll(course_key, ['email'])
    would return [
        {'email': 'email1'}
        {'email': 'email2'}
        {'email': 'email3'}
    ]

    Note that result does not include students who may enroll and have
    already done so.
    """
    may_enroll_and_unenrolled = CourseEnrollmentAllowed.may_enroll_and_unenrolled(course_key)

    def extract_student(student, features):
        """
        Build dict containing information about a single student.
        """
        return {feature: getattr(student, feature) for feature in features}

    return [extract_student(student, features) for student in may_enroll_and_unenrolled]


def list_inactive_enrolled_students(course_key, features):
    """
    Return info about students who are enrolled in a course but have not activated their account.

    list_enrolled_inactive_students(course_key, ['email'])
    would return [
        {'email': 'email1'}
        {'email': 'email2'}
        {'email': 'email3'}
    ]
    """
    enrolled_inactive_user_emails = CourseEnrollment.objects.filter(
        course_id=course_key,
        is_active=True,
        user__is_active=False
    ).annotate(
        email=F('user__email')
    ).values('email')

    def extract_student(student, features):
        """
        Build dict containing information about a single inactive enrolled student.
        """
        return {feature: student.get(feature, None) for feature in features}

    return [extract_student(student, features) for student in enrolled_inactive_user_emails]


def get_proctored_exam_results(course_key, features):
    """
    Return info about proctored exam results in a course as a dict.
    """
    comment_statuses = ['Rules Violation', 'Suspicious']

    def extract_details(exam_attempt, features, course_enrollments):
        """
        Build dict containing information about a single student exam_attempt.
        """
        proctored_exam = {
            feature: exam_attempt.get(feature) for feature in features if feature in exam_attempt
        }

        for status in comment_statuses:
            comment_list = exam_attempt.get(
                f'{status} Comments',
                []
            )
            proctored_exam.update({
                f'{status} Count': len(comment_list),
                f'{status} Comments': '; '.join(comment_list),
            })
        try:
            proctored_exam['track'] = course_enrollments[exam_attempt['user_id']]
        except KeyError:
            proctored_exam['track'] = 'Unknown'
        return proctored_exam

    exam_attempts = get_exam_violation_report(course_key)
    course_enrollments = get_enrollments_for_course(exam_attempts)
    return [extract_details(exam_attempt, features, course_enrollments) for exam_attempt in exam_attempts]


def get_enrollments_for_course(exam_attempts):
    """
     Returns all enrollments from a list of attempts. user_id is passed from proctoring.
     """
    if exam_attempts:
        users = []
        for e in exam_attempts:
            users.append(e['user_id'])

        enrollments = {c.user_id: c.mode for c in CourseEnrollment.objects.filter(
            course_id=CourseKey.from_string(exam_attempts[0]['course_id']), user_id__in=users)}
        return enrollments


def coupon_codes_features(features, coupons_list, course_id):
    """
    Return list of Coupon Codes as dictionaries.

    coupon_codes_features
    would return [
        {'course_id': 'edX/Open_DemoX/edx_demo_course,, 'discount': '213'  ..... }
        {'course_id': 'edX/Open_DemoX/edx_demo_course,, 'discount': '234'  ..... }
    ]
    """

    def extract_coupon(coupon, features):
        """ convert coupon_codes to dictionary
        :param coupon_codes:
        :param features:
        """
        coupon_features = [x for x in COUPON_FEATURES if x in features]

        coupon_dict = {feature: getattr(coupon, feature) for feature in coupon_features}
        coupon_redemptions = coupon.couponredemption_set.filter(
            order__status="purchased"
        )

        coupon_dict['code_redeemed_count'] = coupon_redemptions.count()

        seats_purchased_using_coupon = 0
        total_discounted_amount = 0
        for coupon_redemption in coupon_redemptions:
            cart_items = coupon_redemption.order.orderitem_set.all().select_subclasses()
            found_items = []
            for item in cart_items:
                if getattr(item, 'course_id', None):
                    if item.course_id == course_id:
                        found_items.append(item)
            for order_item in found_items:
                seats_purchased_using_coupon += order_item.qty
                discounted_amount_for_item = float(
                    order_item.list_price * order_item.qty) * (float(coupon.percentage_discount) / 100)
                total_discounted_amount += discounted_amount_for_item

        coupon_dict['total_discounted_seats'] = seats_purchased_using_coupon
        coupon_dict['total_discounted_amount'] = total_discounted_amount

        # We have to capture the redeemed_by value in the case of the downloading and spent registration
        # codes csv. In the case of active and generated registration codes the redeemed_by value will be None.
        # They have not been redeemed yet

        coupon_dict['expiration_date'] = coupon.display_expiry_date
        coupon_dict['course_id'] = str(coupon_dict['course_id'])
        return coupon_dict
    return [extract_coupon(coupon, features) for coupon in coupons_list]


def list_problem_responses(course_key, problem_location, limit_responses=None):
    """
    Return responses to a given problem as a dict.

    list_problem_responses(course_key, problem_location)

    would return [
        {'username': u'user1', 'state': u'...'},
        {'username': u'user2', 'state': u'...'},
        {'username': u'user3', 'state': u'...'},
    ]

    where `state` represents a student's response to the problem
    identified by `problem_location`.
    """
    if isinstance(problem_location, UsageKey):
        problem_key = problem_location
    else:
        problem_key = UsageKey.from_string(problem_location)
    # Are we dealing with an "old-style" problem location?
    run = problem_key.run
    if not run:
        problem_key = UsageKey.from_string(problem_location).map_into_course(course_key)
    if problem_key.course_key != course_key:
        return []

    smdat = StudentModule.objects.filter(
        course_id=course_key,
        module_state_key=problem_key
    ).select_related('student')
    smdat = smdat.order_by('student')
    if limit_responses is not None:
        smdat = smdat[:limit_responses]

    return [
        {'username': response.student.username, 'state': get_response_state(response)}
        for response in smdat
    ]


def get_response_state(response):
    """
    Returns state of a particular response as string.

    This method also does necessary encoding for displaying unicode data correctly.
    """
    def get_transformer():
        """
        Returns state transformer depending upon the problem type.
        """
        problem_state_transformers = {
            'openassessment': transform_ora_state,
            'problem': transform_capa_state
        }
        problem_type = response.module_type
        return problem_state_transformers.get(problem_type)

    problem_state = response.state
    problem_state_transformer = get_transformer()
    if not problem_state_transformer:
        return problem_state

    state = json.loads(problem_state)
    try:
        transformed_state = problem_state_transformer(state)
        return json.dumps(transformed_state, ensure_ascii=False)
    except TypeError:
        username = response.student.username
        err_msg = (
            'Error occurred while attempting to load learner state '
            '{username} for state {state}.'.format(
                username=username,
                state=problem_state
            )
        )
        log.error(err_msg)
        return problem_state


def transform_ora_state(state):
    """
    ORA problem state transformer transforms the problem states.

    Some state variables values are json dumped strings which needs to be loaded
    into a python object.
    """
    fields_to_transform = ['saved_response', 'saved_files_descriptions']

    for field in fields_to_transform:
        field_state = state.get(field)
        if not field_state:
            continue

        state[field] = json.loads(field_state)
    return state


def transform_capa_state(state):
    """
    Transforms the CAPA problem state.
    """
    return state


def course_registration_features(features, registration_codes, csv_type):
    """
    Return list of Course Registration Codes as dictionaries.

    course_registration_features
    would return [
        {'code': 'code1', 'course_id': 'edX/Open_DemoX/edx_demo_course, ..... }
        {'code': 'code2', 'course_id': 'edX/Open_DemoX/edx_demo_course, ..... }
    ]
    """

    def extract_course_registration(registration_code, features, csv_type):
        """ convert registration_code to dictionary
        :param registration_code:
        :param features:
        :param csv_type:
        """
        site_name = configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME)
        registration_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]

        course_registration_dict = {feature: getattr(registration_code, feature) for feature in registration_features}  # lint-amnesty, pylint: disable=line-too-long
        course_registration_dict['company_name'] = None
        if registration_code.invoice_item:
            course_registration_dict['company_name'] = registration_code.invoice_item.invoice.company_name
        course_registration_dict['redeemed_by'] = None
        if registration_code.invoice_item:
            sale_invoice = registration_code.invoice_item.invoice
            course_registration_dict['invoice_id'] = sale_invoice.id
            course_registration_dict['purchaser'] = sale_invoice.recipient_name
            course_registration_dict['customer_reference_number'] = sale_invoice.customer_reference_number
            course_registration_dict['internal_reference'] = sale_invoice.internal_reference

        course_registration_dict['redeem_code_url'] = 'http://{base_url}{redeem_code_url}'.format(
            base_url=site_name,
            redeem_code_url=reverse('register_code_redemption',
                                    kwargs={'registration_code': registration_code.code})
        )
        # we have to capture the redeemed_by value in the case of the downloading and spent registration
        # codes csv. In the case of active and generated registration codes the redeemed_by value will be None.
        #  They have not been redeemed yet
        if csv_type is not None:
            try:
                redemption_set = registration_code.registrationcoderedemption_set
                redeemed_by = redemption_set.get(registration_code=registration_code).redeemed_by
                course_registration_dict['redeemed_by'] = redeemed_by.email
            except ObjectDoesNotExist:
                pass

        course_registration_dict['course_id'] = str(course_registration_dict['course_id'])
        return course_registration_dict
    return [extract_course_registration(code, features, csv_type) for code in registration_codes]


def dump_grading_context(course):
    """
    Render information about course grading context
    (e.g. which problems are graded in what assignments)
    Useful for debugging grading_policy.json and policy.json

    Returns HTML string
    """
    hbar = "{}\n".format("-" * 77)
    msg = hbar
    msg += "Course grader:\n"

    msg += '%s\n' % course.grader.__class__
    graders = {}
    if isinstance(course.grader, xmgraders.WeightedSubsectionsGrader):
        msg += '\n'
        msg += "Graded sections:\n"
        for subgrader, category, weight in course.grader.subgraders:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n"\
                % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += hbar
    msg += "Listing grading context for course %s\n" % str(course.id)

    gcontext = grades_context.grading_context_for_course(course)
    msg += "graded sections:\n"

    msg += '%s\n' % list(gcontext['all_graded_subsections_by_type'].keys())
    for (gsomething, gsvals) in gcontext['all_graded_subsections_by_type'].items():
        msg += "--> Section %s:\n" % (gsomething)
        for sec in gsvals:
            sdesc = sec['subsection_block']
            frmat = getattr(sdesc, 'format', None)
            aname = ''
            if frmat in graders:
                gform = graders[frmat]
                aname = '%s %02d' % (gform.short_label, gform.index)
                gform.index += 1
            elif sdesc.display_name in graders:
                gform = graders[sdesc.display_name]
                aname = '%s' % gform.short_label
            notes = ''
            if getattr(sdesc, 'score_by_attempt', False):
                notes = ', score by attempt!'
            msg += "      %s (format=%s, Assignment=%s%s)\n"\
                % (sdesc.display_name, frmat, aname, notes)
    msg += "all graded blocks:\n"
    msg += "length=%d\n" % gcontext['count_all_graded_blocks']
    msg = HTML('<pre>{}</pre>').format(Text(msg))
    return msg
