"""
Student and course analytics.

Serve miscellaneous course and student data
"""
from shoppingcart.models import (
    PaidCourseRegistration, CouponRedemption, Invoice, CourseRegCodeItem,
    OrderTypes, RegistrationCodeRedemption, CourseRegistrationCode
)
from django.db.models import Q
from django.contrib.auth.models import User
import xmodule.graders as xmgraders
from django.core.exceptions import ObjectDoesNotExist


STUDENT_FEATURES = ('id', 'username', 'first_name', 'last_name', 'is_staff', 'email')
PROFILE_FEATURES = ('name', 'language', 'location', 'year_of_birth', 'gender',
                    'level_of_education', 'mailing_address', 'goals', 'meta')
ORDER_ITEM_FEATURES = ('list_price', 'unit_cost', 'status')
ORDER_FEATURES = ('purchase_time',)

SALE_FEATURES = ('total_amount', 'company_name', 'company_contact_name', 'company_contact_email', 'recipient_name',
                 'recipient_email', 'customer_reference_number', 'internal_reference')

SALE_ORDER_FEATURES = ('id', 'company_name', 'company_contact_name', 'company_contact_email', 'purchase_time',
                       'customer_reference_number', 'recipient_name', 'recipient_email', 'bill_to_street1',
                       'bill_to_street2', 'bill_to_city', 'bill_to_state', 'bill_to_postalcode',
                       'bill_to_country', 'order_type',)

AVAILABLE_FEATURES = STUDENT_FEATURES + PROFILE_FEATURES
COURSE_REGISTRATION_FEATURES = ('code', 'course_id', 'created_by', 'created_at')
COUPON_FEATURES = ('course_id', 'percentage_discount', 'description')


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
        course_reg_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]
        order_item_features = [x for x in ORDER_ITEM_FEATURES if x in features]

        # Extracting order information
        sale_order_dict = dict((feature, getattr(purchased_course.order, feature))
                               for feature in sale_order_features)

        quantity = int(getattr(purchased_course, 'qty'))
        unit_cost = float(getattr(purchased_course, 'unit_cost'))
        sale_order_dict.update({"total_amount": quantity * unit_cost})

        sale_order_dict.update({"logged_in_username": purchased_course.order.user.username})
        sale_order_dict.update({"logged_in_email": purchased_course.order.user.email})

        sale_order_dict.update({"total_codes": 'N/A'})
        sale_order_dict.update({'total_used_codes': 'N/A'})

        # Extracting OrderItem information of unit_cost, list_price and status
        order_item_dict = dict((feature, getattr(purchased_course, feature, None))
                               for feature in order_item_features)
        order_item_dict.update({"coupon_code": 'N/A'})

        coupon_redemption = CouponRedemption.objects.select_related('coupon').filter(order_id=purchased_course.order_id)
        # if coupon is redeemed against the order, update the information in the order_item_dict
        if coupon_redemption.exists():
            coupon_codes = [redemption.coupon.code for redemption in coupon_redemption]
            order_item_dict.update({'coupon_code': ", ".join(coupon_codes)})

        sale_order_dict.update(dict(order_item_dict.items()))
        if getattr(purchased_course.order, 'order_type') == OrderTypes.BUSINESS:
            registration_codes = CourseRegistrationCode.objects.filter(order=purchased_course.order, course_id=course_id)
            sale_order_dict.update({"total_codes": registration_codes.count()})
            total_used_codes = RegistrationCodeRedemption.objects.filter(registration_code__in=registration_codes).count()
            sale_order_dict.update({'total_used_codes': total_used_codes})

            codes = [reg_code.code for reg_code in registration_codes]

            # Extracting registration code information
            obj_course_reg_code = registration_codes.all()[:1].get()
            course_reg_dict = dict((feature, getattr(obj_course_reg_code, feature))
                                   for feature in course_reg_features)

            course_reg_dict['course_id'] = course_id.to_deprecated_string()
            course_reg_dict.update({'codes': ", ".join(codes)})
            sale_order_dict.update(dict(course_reg_dict.items()))

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
    sales = Invoice.objects.filter(course_id=course_id)

    def sale_records_info(sale, features):
        """ convert sales records to dictionary """

        sale_features = [x for x in SALE_FEATURES if x in features]
        course_reg_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]

        # Extracting sale information
        sale_dict = dict((feature, getattr(sale, feature))
                         for feature in sale_features)

        total_used_codes = RegistrationCodeRedemption.objects.filter(
            registration_code__in=sale.courseregistrationcode_set.all()
        ).count()
        sale_dict.update({"invoice_number": getattr(sale, 'id')})
        sale_dict.update({"total_codes": sale.courseregistrationcode_set.all().count()})
        sale_dict.update({'total_used_codes': total_used_codes})

        codes = [reg_code.code for reg_code in sale.courseregistrationcode_set.all()]

        # Extracting registration code information
        obj_course_reg_code = sale.courseregistrationcode_set.all()[:1].get()
        course_reg_dict = dict((feature, getattr(obj_course_reg_code, feature))
                               for feature in course_reg_features)

        course_reg_dict['course_id'] = course_id.to_deprecated_string()
        course_reg_dict.update({'codes': ", ".join(codes)})
        sale_dict.update(dict(course_reg_dict.items()))

        return sale_dict

    return [sale_records_info(sale, features) for sale in sales]


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

    students = User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
    ).order_by('username').select_related('profile')

    if include_cohort_column:
        students = students.prefetch_related('course_groups')

    def extract_student(student, features):
        """ convert student to dictionary """
        student_features = [x for x in STUDENT_FEATURES if x in features]
        profile_features = [x for x in PROFILE_FEATURES if x in features]

        student_dict = dict((feature, getattr(student, feature))
                            for feature in student_features)
        profile = student.profile
        if profile is not None:
            profile_dict = dict((feature, getattr(profile, feature))
                                for feature in profile_features)
            student_dict.update(profile_dict)

        if include_cohort_column:
            # Note that we use student.course_groups.all() here instead of
            # student.course_groups.filter(). The latter creates a fresh query,
            # therefore negating the performance gain from prefetch_related().
            student_dict['cohort'] = next(
                (cohort.name for cohort in student.course_groups.all() if cohort.course_id == course_key),
                "[unassigned]"
            )
        return student_dict

    return [extract_student(student, features) for student in students]


def coupon_codes_features(features, coupons_list):
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
        coupon_dict['code_redeemed_count'] = coupon.couponredemption_set.all().count()

        # we have to capture the redeemed_by value in the case of the downloading and spent registration
        # codes csv. In the case of active and generated registration codes the redeemed_by value will be None.
        #  They have not been redeemed yet

        coupon_dict['course_id'] = coupon_dict['course_id'].to_deprecated_string()
        return coupon_dict
    return [extract_coupon(coupon, features) for coupon in coupons_list]


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
        registration_features = [x for x in COURSE_REGISTRATION_FEATURES if x in features]

        course_registration_dict = dict((feature, getattr(registration_code, feature)) for feature in registration_features)
        course_registration_dict['company_name'] = None
        if registration_code.invoice:
            course_registration_dict['company_name'] = getattr(registration_code.invoice, 'company_name')
        course_registration_dict['redeemed_by'] = None
        if registration_code.invoice:
            sale_invoice = Invoice.objects.get(id=registration_code.invoice_id)
            course_registration_dict['invoice_id'] = sale_invoice.id
            course_registration_dict['purchaser'] = sale_invoice.recipient_name
            course_registration_dict['customer_reference_number'] = sale_invoice.customer_reference_number
            course_registration_dict['internal_reference'] = sale_invoice.internal_reference

        # we have to capture the redeemed_by value in the case of the downloading and spent registration
        # codes csv. In the case of active and generated registration codes the redeemed_by value will be None.
        #  They have not been redeemed yet
        if csv_type is not None:
            try:
                redeemed_by = getattr(registration_code.registrationcoderedemption_set.get(registration_code=registration_code), 'redeemed_by')
                course_registration_dict['redeemed_by'] = getattr(redeemed_by, 'email')
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

    gcontext = course.grading_context
    msg += "graded sections:\n"

    msg += '%s\n' % gcontext['graded_sections'].keys()
    for (gsomething, gsvals) in gcontext['graded_sections'].items():
        msg += "--> Section %s:\n" % (gsomething)
        for sec in gsvals:
            sdesc = sec['section_descriptor']
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
    msg += "all descriptors:\n"
    msg += "length=%d\n" % len(gcontext['all_descriptors'])
    msg = '<pre>%s</pre>' % msg.replace('<', '&lt;')
    return msg
