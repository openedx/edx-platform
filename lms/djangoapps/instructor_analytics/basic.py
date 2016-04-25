"""
Student and course analytics.

Serve miscellaneous course and student data
"""
import json
import datetime
from shoppingcart.models import (
    PaidCourseRegistration, CouponRedemption, CourseRegCodeItem,
    RegistrationCodeRedemption, CourseRegistrationCodeInvoiceItem
)
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from opaque_keys.edx.keys import UsageKey
import xmodule.graders as xmgraders
from microsite_configuration import microsite
from student.models import CourseEnrollmentAllowed
from edx_proctoring.api import get_all_exam_attempts
from courseware.models import StudentModule
from certificates.models import GeneratedCertificate
from django.db.models import Count
from certificates.models import CertificateStatuses
from courseware.grades import grading_context_for_course


STUDENT_FEATURES = ('id', 'username', 'first_name', 'last_name', 'is_staff', 'email')
PROFILE_FEATURES = ('name', 'language', 'location', 'year_of_birth', 'gender',
                    'level_of_education', 'mailing_address', 'goals', 'meta',
                    'city', 'country')
ORDER_ITEM_FEATURES = ('list_price', 'unit_cost', 'status')
ORDER_FEATURES = ('purchase_time',)

SALE_FEATURES = ('total_amount', 'company_name', 'company_contact_name', 'company_contact_email', 'recipient_name',
                 'recipient_email', 'customer_reference_number', 'internal_reference', 'created')

SALE_ORDER_FEATURES = ('id', 'company_name', 'company_contact_name', 'company_contact_email', 'purchase_time',
                       'customer_reference_number', 'recipient_name', 'recipient_email', 'bill_to_street1',
                       'bill_to_street2', 'bill_to_city', 'bill_to_state', 'bill_to_postalcode',
                       'bill_to_country', 'order_type', 'created')

AVAILABLE_FEATURES = STUDENT_FEATURES + PROFILE_FEATURES
COURSE_REGISTRATION_FEATURES = ('code', 'course_id', 'created_by', 'created_at', 'is_valid')
COUPON_FEATURES = ('code', 'course_id', 'percentage_discount', 'description', 'expiration_date', 'is_active')
CERTIFICATE_FEATURES = ('course_id', 'mode', 'status', 'grade', 'created_date', 'is_active', 'error_reason')

UNAVAILABLE = "[unavailable]"


def sale_order_record_features(course_id, features):
    """
    Return list of sale orders features as dictionaries.

    sales_records(course_id, ['company_name, total_codes', total_amount])
    would return [
        {'company_name': 'group_A', 'total_codes': '1', total_amount:'total_amount1 in decimal'.}
        {'company_name': 'group_B', 'total_codes': '2', total_amount:'total_amount2 in decimal'.}
        {'company_name': 'group_C', 'total_codes': '3', total_amount:'total_amount3 in decimal'.}
    ]
    """
    purchased_courses = PaidCourseRegistration.objects.filter(
        Q(course_id=course_id),
        Q(status='purchased') | Q(status='refunded')
    ).order_by('order')

    purchased_course_reg_codes = CourseRegCodeItem.objects.filter(
        Q(course_id=course_id),
        Q(status='purchased') | Q(status='refunded')
    ).order_by('order')

    def sale_order_info(purchased_course, features):
        """
        convert purchase transactions to dictionary
        """

        sale_order_features = [x for x in SALE_ORDER_FEATURES if x in features]
        order_item_features = [x for x in ORDER_ITEM_FEATURES if x in features]

        # Extracting order information
        sale_order_dict = dict((feature, getattr(purchased_course.order, feature))
                               for feature in sale_order_features)

        quantity = int(purchased_course.qty)
        unit_cost = float(purchased_course.unit_cost)
        sale_order_dict.update({"quantity": quantity})
        sale_order_dict.update({"total_amount": quantity * unit_cost})

        sale_order_dict.update({"logged_in_username": purchased_course.order.user.username})
        sale_order_dict.update({"logged_in_email": purchased_course.order.user.email})

        # Extracting OrderItem information of unit_cost, list_price and status
        order_item_dict = dict((feature, getattr(purchased_course, feature, None))
                               for feature in order_item_features)

        order_item_dict['list_price'] = purchased_course.get_list_price()

        sale_order_dict.update(
            {"total_discount": (order_item_dict['list_price'] - order_item_dict['unit_cost']) * quantity}
        )

        order_item_dict.update({"coupon_code": 'N/A'})

        coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(order_id=purchased_course.order_id)
        # if coupon is redeemed against the order, update the information in the order_item_dict
        if coupon_redemption.exists():
            coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
            order_item_dict.update({'coupon_code': ", ".join(coupon_codes)})

        sale_order_dict.update(dict(order_item_dict.items()))

        return sale_order_dict

    csv_data = [sale_order_info(purchased_course, features) for purchased_course in purchased_courses]
    csv_data.extend(
        [sale_order_info(purchased_course_reg_code, features)
         for purchased_course_reg_code in purchased_course_reg_codes]
    )
    return csv_data


def sale_record_features(course_id, features):
    """
    Return list of sales features as dictionaries.

    sales_records(course_id, ['company_name, total_codes', total_amount])
    would return [
        {'company_name': 'group_A', 'total_codes': '1', total_amount:'total_amount1 in decimal'.}
        {'company_name': 'group_B', 'total_codes': '2', total_amount:'total_amount2 in decimal'.}
        {'company_name': 'group_C', 'total_codes': '3', total_amount:'total_amount3 in decimal'.}
    ]
    """
    sales = CourseRegistrationCodeInvoiceItem.objects.select_related('invoice').filter(course_id=course_id)

    def sale_records_info(sale, features):
        """
        Convert sales records to dictionary

        """
        invoice = sale.invoice
        sale_features = [x for x in SALE_FEATURES if x in features]
        course_reg_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]

        # Extracting sale information
        sale_dict = dict((feature, getattr(invoice, feature))
                         for feature in sale_features)

        total_used_codes = RegistrationCodeRedemption.objects.filter(
            registration_code__in=sale.courseregistrationcode_set.all()
        ).count()
        sale_dict.update({"invoice_number": invoice.id})
        sale_dict.update({"total_codes": sale.courseregistrationcode_set.all().count()})
        sale_dict.update({'total_used_codes': total_used_codes})

        codes = [reg_code.code for reg_code in sale.courseregistrationcode_set.all()]

        # Extracting registration code information
        if len(codes) > 0:
            obj_course_reg_code = sale.courseregistrationcode_set.all()[:1].get()
            course_reg_dict = dict((feature, getattr(obj_course_reg_code, feature))
                                   for feature in course_reg_features)
        else:
            course_reg_dict = dict((feature, None)
                                   for feature in course_reg_features)

        course_reg_dict['course_id'] = course_id.to_deprecated_string()
        course_reg_dict.update({'codes': ", ".join(codes)})
        sale_dict.update(dict(course_reg_dict.items()))

        return sale_dict

    return [sale_records_info(sale, features) for sale in sales]


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

    students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
    ).order_by('username').select_related('profile')

    if include_cohort_column:
        students = students.prefetch_related('course_groups')

    if include_team_column:
        students = students.prefetch_related('teams')

    def extract_attr(student, feature):
        """Evaluate a student attribute that is ready for JSON serialization"""
        attr = getattr(student, feature)
        try:
            DjangoJSONEncoder().default(attr)
            return attr
        except TypeError:
            return unicode(attr)

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

        student_dict = dict((feature, extract_attr(student, feature))
                            for feature in student_features)
        profile = student.profile
        if profile is not None:
            profile_dict = dict((feature, extract_attr(profile, feature))
                                for feature in profile_features)
            student_dict.update(profile_dict)

            # now featch the requested meta fields
            meta_dict = json.loads(profile.meta) if profile.meta else {}
            for meta_feature, meta_key in meta_features:
                student_dict[meta_feature] = meta_dict.get(meta_key)

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
        return dict((feature, getattr(student, feature)) for feature in features)

    return [extract_student(student, features) for student in may_enroll_and_unenrolled]


def get_proctored_exam_results(course_key, features):
    """
    Return info about proctored exam results in a course as a dict.
    """
    def extract_student(exam_attempt, features):
        """
        Build dict containing information about a single student exam_attempt.
        """
        proctored_exam = dict(
            (feature, exam_attempt.get(feature)) for feature in features if feature in exam_attempt
        )
        proctored_exam.update({'exam_name': exam_attempt.get('proctored_exam').get('exam_name')})
        proctored_exam.update({'user_email': exam_attempt.get('user').get('email')})

        return proctored_exam

    exam_attempts = get_all_exam_attempts(course_key)
    return [extract_student(exam_attempt, features) for exam_attempt in exam_attempts]


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

        coupon_dict = dict((feature, getattr(coupon, feature)) for feature in coupon_features)
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
        coupon_dict['course_id'] = coupon_dict['course_id'].to_deprecated_string()
        return coupon_dict
    return [extract_coupon(coupon, features) for coupon in coupons_list]


def list_problem_responses(course_key, problem_location):
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
    problem_key = UsageKey.from_string(problem_location)
    # Are we dealing with an "old-style" problem location?
    run = problem_key.run
    if not run:
        problem_key = course_key.make_usage_key_from_deprecated_string(problem_location)
    if problem_key.course_key != course_key:
        return []

    smdat = StudentModule.objects.filter(
        course_id=course_key,
        module_state_key=problem_key
    )
    smdat = smdat.order_by('student')

    return [
        {'username': response.student.username, 'state': response.state}
        for response in smdat
    ]


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
        site_name = microsite.get_value('SITE_NAME', settings.SITE_NAME)
        registration_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]

        course_registration_dict = dict((feature, getattr(registration_code, feature)) for feature in registration_features)
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

        course_registration_dict['course_id'] = course_registration_dict['course_id'].to_deprecated_string()
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
        for subgrader, category, weight in course.grader.sections:
            msg += "  subgrader=%s, type=%s, category=%s, weight=%s\n"\
                % (subgrader.__class__, subgrader.type, category, weight)
            subgrader.index = 1
            graders[subgrader.type] = subgrader
    msg += hbar
    msg += "Listing grading context for course %s\n" % course.id.to_deprecated_string()

    gcontext = grading_context_for_course(course)
    msg += "graded sections:\n"

    msg += '%s\n' % gcontext['all_graded_sections'].keys()
    for (gsomething, gsvals) in gcontext['all_graded_sections'].items():
        msg += "--> Section %s:\n" % (gsomething)
        for sec in gsvals:
            sdesc = sec['section_block']
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
    msg += "length=%d\n" % len(gcontext['all_graded_blocks'])
    msg = '<pre>%s</pre>' % msg.replace('<', '&lt;')
    return msg
