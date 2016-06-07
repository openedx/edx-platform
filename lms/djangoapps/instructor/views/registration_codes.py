"""
E-commerce Tab Instructor Dashboard Query Registration Code Status.
"""
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_GET, require_POST
from instructor.enrollment import get_email_params, send_mail_to_student
from django.utils.translation import ugettext as _
from courseware.courses import get_course_by_id
from instructor.views.api import require_level
from student.models import CourseEnrollment
from util.json_request import JsonResponse
from shoppingcart.models import CourseRegistrationCode, RegistrationCodeRedemption
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.views.decorators.cache import cache_control
import logging

log = logging.getLogger(__name__)


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_GET
def look_up_registration_code(request, course_id):
    """
    Look for the registration_code in the database.
    and check if it is still valid, allowed to redeem or not.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    code = request.GET.get('registration_code')
    course = get_course_by_id(course_key, depth=0)
    try:
        registration_code = CourseRegistrationCode.objects.get(code=code)
    except CourseRegistrationCode.DoesNotExist:
        return JsonResponse({
            'is_registration_code_exists': False,
            'is_registration_code_valid': False,
            'is_registration_code_redeemed': False,
            'message': _('The enrollment code ({code}) was not found for the {course_name} course.').format(
                code=code, course_name=course.display_name
            )
        }, status=400)  # status code 200: OK by default

    reg_code_already_redeemed = RegistrationCodeRedemption.is_registration_code_redeemed(code)

    registration_code_detail_url = reverse('registration_code_details', kwargs={'course_id': unicode(course_id)})

    return JsonResponse({
        'is_registration_code_exists': True,
        'is_registration_code_valid': registration_code.is_valid,
        'is_registration_code_redeemed': reg_code_already_redeemed,
        'registration_code_detail_url': registration_code_detail_url
    })  # status code 200: OK by default


@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
@require_POST
def registration_code_details(request, course_id):
    """
    Post handler to mark the registration code as
        1) valid
        2) invalid
        3) Unredeem.

    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    code = request.POST.get('registration_code')
    action_type = request.POST.get('action_type')
    course = get_course_by_id(course_key, depth=0)
    action_type_messages = {
        'invalidate_registration_code': _('This enrollment code has been canceled. It can no longer be used.'),
        'unredeem_registration_code': _('This enrollment code has been marked as unused.'),
        'validate_registration_code': _('The enrollment code has been restored.')
    }
    try:
        registration_code = CourseRegistrationCode.objects.get(code=code)
    except CourseRegistrationCode.DoesNotExist:
        return JsonResponse({
            'message': _('The enrollment code ({code}) was not found for the {course_name} course.').format(
                code=code, course_name=course.display_name
            )}, status=400)

    if action_type == 'invalidate_registration_code':
        registration_code.is_valid = False
        registration_code.save()
        if RegistrationCodeRedemption.is_registration_code_redeemed(code):
            code_redemption = RegistrationCodeRedemption.get_registration_code_redemption(code, course_key)
            delete_redemption_entry(request, code_redemption, course_key)

    if action_type == 'validate_registration_code':
        registration_code.is_valid = True
        registration_code.save()

    if action_type == 'unredeem_registration_code':
        code_redemption = RegistrationCodeRedemption.get_registration_code_redemption(code, course_key)
        if code_redemption is None:
            return JsonResponse({
                'message': _('The redemption does not exist against enrollment code ({code}).').format(
                    code=code)}, status=400)

        delete_redemption_entry(request, code_redemption, course_key)

    return JsonResponse({'message': action_type_messages[action_type]})


def delete_redemption_entry(request, code_redemption, course_key):
    """
    delete the redemption entry from the table and
    unenroll the user who used the registration code
    for the enrollment and send him/her the unenrollment email.
    """
    user = code_redemption.redeemed_by
    email_address = code_redemption.redeemed_by.email
    full_name = code_redemption.redeemed_by.profile.name
    CourseEnrollment.unenroll(user, course_key, skip_refund=True)

    course = get_course_by_id(course_key, depth=0)
    email_params = get_email_params(course, True, secure=request.is_secure())
    email_params['message'] = 'enrolled_unenroll'
    email_params['email_address'] = email_address
    email_params['full_name'] = full_name
    send_mail_to_student(email_address, email_params)

    # remove the redemption entry from the database.
    log.info('deleting redemption entry (%s) from the database.', code_redemption.id)
    code_redemption.delete()
