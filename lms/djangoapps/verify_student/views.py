"""
Views for the verification flow

"""
import json
import logging
import decimal
import datetime
from pytz import UTC

from edxmako.shortcuts import render_to_response

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from course_modes.models import CourseMode
from student.models import CourseEnrollment
from student.views import reverification_info
from shoppingcart.models import Order, CertificateItem
from shoppingcart.processors import (
    get_signed_purchase_params, get_purchase_endpoint
)
from verify_student.models import (
    SoftwareSecurePhotoVerification,
)
from reverification.models import MidcourseReverificationWindow
import ssencrypt
from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.keys import CourseKey
from .exceptions import WindowExpiredException
from xmodule.modulestore.django import modulestore

from util.json_request import JsonResponse

log = logging.getLogger(__name__)

EVENT_NAME_USER_ENTERED_MIDCOURSE_REVERIFY_VIEW = 'edx.course.enrollment.reverify.started'
EVENT_NAME_USER_SUBMITTED_MIDCOURSE_REVERIFY = 'edx.course.enrollment.reverify.submitted'
EVENT_NAME_USER_REVERIFICATION_REVIEWED_BY_SOFTWARESECURE = 'edx.course.enrollment.reverify.reviewed'

class VerifyView(View):

    @method_decorator(login_required)
    def get(self, request, course_id):
        """
        Displays the main verification view, which contains three separate steps:
            - Taking the standard face photo
            - Taking the id photo
            - Confirming that the photos and payment price are correct
              before proceeding to payment
        """
        upgrade = request.GET.get('upgrade', False)

        course_id = CourseKey.from_string(course_id)
        # If the user has already been verified within the given time period,
        # redirect straight to the payment -- no need to verify again.
        if SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
            return redirect(
                reverse('verify_student_verified',
                        kwargs={'course_id': course_id.to_deprecated_string()}) + "?upgrade={}".format(upgrade)
            )
        elif CourseEnrollment.enrollment_mode_for_user(request.user, course_id) == ('verified', True):
            return redirect(reverse('dashboard'))
        else:
            # If they haven't completed a verification attempt, we have to
            # restart with a new one. We can't reuse an older one because we
            # won't be able to show them their encrypted photo_id -- it's easier
            # bookkeeping-wise just to start over.
            progress_state = "start"

        # we prefer professional over verify
        current_mode = CourseMode.verified_mode_for_course(course_id)

        # if the course doesn't have a verified mode, we want to kick them
        # from the flow
        if not current_mode:
            return redirect(reverse('dashboard'))
        if course_id.to_deprecated_string() in request.session.get("donation_for_course", {}):
            chosen_price = request.session["donation_for_course"][unicode(course_id)]
        else:
            chosen_price = current_mode.min_price

        course = modulestore().get_course(course_id)
        if current_mode.suggested_prices != '':
            suggested_prices = [
                decimal.Decimal(price)
                for price in current_mode.suggested_prices.split(",")
            ]
        else:
            suggested_prices = []

        context = {
            "progress_state": progress_state,
            "user_full_name": request.user.profile.name,
            "course_id": course_id.to_deprecated_string(),
            "course_modes_choose_url": reverse('course_modes_choose', kwargs={'course_id': course_id.to_deprecated_string()}),
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "purchase_endpoint": get_purchase_endpoint(),
            "suggested_prices": suggested_prices,
            "currency": current_mode.currency.upper(),
            "chosen_price": chosen_price,
            "min_price": current_mode.min_price,
            "upgrade": upgrade == u'True',
            "can_audit": CourseMode.mode_for_course(course_id, 'audit') is not None,
            "modes_dict": CourseMode.modes_for_course_dict(course_id),

            # TODO (ECOM-16): Remove once the AB test completes
            "autoreg": request.session.get('auto_register', False),
            "retake": request.GET.get('retake', False),
        }

        return render_to_response('verify_student/photo_verification.html', context)


class VerifiedView(View):
    """
    View that gets shown once the user has already gone through the
    verification flow
    """
    @method_decorator(login_required)
    def get(self, request, course_id):
        """
        Handle the case where we have a get request
        """
        upgrade = request.GET.get('upgrade', False)
        course_id = CourseKey.from_string(course_id)
        if CourseEnrollment.enrollment_mode_for_user(request.user, course_id) == ('verified', True):
            return redirect(reverse('dashboard'))


        modes_dict = CourseMode.modes_for_course_dict(course_id)

        # we prefer professional over verify
        current_mode = CourseMode.verified_mode_for_course(course_id)

        # if the course doesn't have a verified mode, we want to kick them
        # from the flow
        if not current_mode:
            return redirect(reverse('dashboard'))
        if course_id.to_deprecated_string() in request.session.get("donation_for_course", {}):
            chosen_price = request.session["donation_for_course"][unicode(course_id)]
        else:
            chosen_price = current_mode.min_price

        course = modulestore().get_course(course_id)
        context = {
            "course_id": course_id.to_deprecated_string(),
            "course_modes_choose_url": reverse('course_modes_choose', kwargs={'course_id': course_id.to_deprecated_string()}),
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "purchase_endpoint": get_purchase_endpoint(),
            "currency": current_mode.currency.upper(),
            "chosen_price": chosen_price,
            "create_order_url": reverse("verify_student_create_order"),
            "upgrade": upgrade == u'True',
            "can_audit": "audit" in modes_dict,
            "modes_dict": modes_dict,

            # TODO (ECOM-16): Remove once the AB test completes
            "autoreg": request.session.get('auto_register', False),
        }
        return render_to_response('verify_student/verified.html', context)


@login_required
def create_order(request):
    """
    Submit PhotoVerification and create a new Order for this verified cert
    """
    if not SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
        attempt = SoftwareSecurePhotoVerification(user=request.user)
        try:
            b64_face_image = request.POST['face_image'].split(",")[1]
            b64_photo_id_image = request.POST['photo_id_image'].split(",")[1]
        except IndexError:
            context = {
                'success': False,
            }
            return JsonResponse(context)
        attempt.upload_face_image(b64_face_image.decode('base64'))
        attempt.upload_photo_id_image(b64_photo_id_image.decode('base64'))
        attempt.mark_ready()

        attempt.save()

    course_id = request.POST['course_id']
    course_id = CourseKey.from_string(course_id)
    donation_for_course = request.session.get('donation_for_course', {})
    current_donation = donation_for_course.get(unicode(course_id), decimal.Decimal(0))
    contribution = request.POST.get("contribution", donation_for_course.get(unicode(course_id), 0))
    try:
        amount = decimal.Decimal(contribution).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
    except decimal.InvalidOperation:
        return HttpResponseBadRequest(_("Selected price is not valid number."))

    if amount != current_donation:
        donation_for_course[unicode(course_id)] = amount
        request.session['donation_for_course'] = donation_for_course

    # prefer professional mode over verified_mode
    current_mode = CourseMode.verified_mode_for_course(course_id)

    # make sure this course has a verified mode
    if not current_mode:
        return HttpResponseBadRequest(_("This course doesn't support verified certificates"))

    if current_mode.slug == 'professional':
        amount = current_mode.min_price

    if amount < current_mode.min_price:
        return HttpResponseBadRequest(_("No selected price or selected price is below minimum."))

    # I know, we should check this is valid. All kinds of stuff missing here
    cart = Order.get_cart_for_user(request.user)
    cart.clear()
    enrollment_mode = current_mode.slug
    CertificateItem.add_to_order(cart, course_id, amount, enrollment_mode)

    # Change the order's status so that we don't accidentally modify it later.
    # We need to do this to ensure that the parameters we send to the payment system
    # match what we store in the database.
    # (Ordinarily we would do this client-side when the user submits the form, but since
    # the JavaScript on this page does that immediately, we make the change here instead.
    # This avoids a second AJAX call and some additional complication of the JavaScript.)
    # If a user later re-enters the verification / payment flow, she will create a new order.
    cart.start_purchase()

    callback_url = request.build_absolute_uri(
        reverse("shoppingcart.views.postpay_callback")
    )

    params = get_signed_purchase_params(
        cart, callback_url=callback_url
    )

    params['success'] = True
    params['merchant_defined_data1'] = unicode(course_id)
    return HttpResponse(json.dumps(params), content_type="text/json")


@require_POST
@csrf_exempt  # SS does its own message signing, and their API won't have a cookie value
def results_callback(request):
    """
    Software Secure will call this callback to tell us whether a user is
    verified to be who they said they are.
    """
    body = request.body

    try:
        body_dict = json.loads(body)
    except ValueError:
        log.exception("Invalid JSON received from Software Secure:\n\n{}\n".format(body))
        return HttpResponseBadRequest("Invalid JSON. Received:\n\n{}".format(body))

    if not isinstance(body_dict, dict):
        log.error("Reply from Software Secure is not a dict:\n\n{}\n".format(body))
        return HttpResponseBadRequest("JSON should be dict. Received:\n\n{}".format(body))

    headers = {
        "Authorization": request.META.get("HTTP_AUTHORIZATION", ""),
        "Date": request.META.get("HTTP_DATE", "")
    }

    sig_valid = ssencrypt.has_valid_signature(
        "POST",
        headers,
        body_dict,
        settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_ACCESS_KEY"],
        settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_SECRET_KEY"]
    )

    _response, access_key_and_sig = headers["Authorization"].split(" ")
    access_key = access_key_and_sig.split(":")[0]

    # This is what we should be doing...
    #if not sig_valid:
    #    return HttpResponseBadRequest("Signature is invalid")

    # This is what we're doing until we can figure out why we disagree on sigs
    if access_key != settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_ACCESS_KEY"]:
        return HttpResponseBadRequest("Access key invalid")

    receipt_id = body_dict.get("EdX-ID")
    result = body_dict.get("Result")
    reason = body_dict.get("Reason", "")
    error_code = body_dict.get("MessageType", "")

    try:
        attempt = SoftwareSecurePhotoVerification.objects.get(receipt_id=receipt_id)
    except SoftwareSecurePhotoVerification.DoesNotExist:
        log.error("Software Secure posted back for receipt_id {}, but not found".format(receipt_id))
        return HttpResponseBadRequest("edX ID {} not found".format(receipt_id))

    if result == "PASS":
        log.debug("Approving verification for {}".format(receipt_id))
        attempt.approve()
    elif result == "FAIL":
        log.debug("Denying verification for {}".format(receipt_id))
        attempt.deny(json.dumps(reason), error_code=error_code)
    elif result == "SYSTEM FAIL":
        log.debug("System failure for {} -- resetting to must_retry".format(receipt_id))
        attempt.system_error(json.dumps(reason), error_code=error_code)
        log.error("Software Secure callback attempt for %s failed: %s", receipt_id, reason)
    else:
        log.error("Software Secure returned unknown result {}".format(result))
        return HttpResponseBadRequest(
            "Result {} not understood. Known results: PASS, FAIL, SYSTEM FAIL".format(result)
        )

    # If this is a reverification, log an event
    if attempt.window:
        course_id = attempt.window.course_id
        course_enrollment = CourseEnrollment.get_or_create_enrollment(attempt.user, course_id)
        course_enrollment.emit_event(EVENT_NAME_USER_REVERIFICATION_REVIEWED_BY_SOFTWARESECURE)

    return HttpResponse("OK!")


@login_required
def show_requirements(request, course_id):
    """
    Show the requirements necessary for the verification flow.
    """
    # TODO: seems borked for professional; we're told we need to take photos even if there's a pending verification
    course_id = CourseKey.from_string(course_id)
    upgrade = request.GET.get('upgrade', False)
    if CourseEnrollment.enrollment_mode_for_user(request.user, course_id) == ('verified', True):
        return redirect(reverse('dashboard'))
    if SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
        return redirect(
            reverse('verify_student_verified',
            kwargs={'course_id': course_id.to_deprecated_string()}) + "?upgrade={}".format(upgrade)
        )

    upgrade = request.GET.get('upgrade', False)
    course = modulestore().get_course(course_id)
    modes_dict = CourseMode.modes_for_course_dict(course_id)
    context = {
        "course_id": course_id.to_deprecated_string(),
        "course_modes_choose_url": reverse("course_modes_choose", kwargs={'course_id': course_id.to_deprecated_string()}),
        "verify_student_url": reverse('verify_student_verify', kwargs={'course_id': course_id.to_deprecated_string()}),
        "course_name": course.display_name_with_default,
        "course_org": course.display_org_with_default,
        "course_num": course.display_number_with_default,
        "is_not_active": not request.user.is_active,
        "upgrade": upgrade == u'True',
        "modes_dict": modes_dict,

        # TODO (ECOM-16): Remove once the AB test completes
        "autoreg": request.session.get('auto_register', False),
    }
    return render_to_response("verify_student/show_requirements.html", context)


class ReverifyView(View):
    """
    The main reverification view. Under similar constraints as the main verification view.
    Has to perform these functions:
        - take new face photo
        - take new id photo
        - submit photos to photo verification service

    Does not need to be attached to a particular course.
    Does not need to worry about pricing
    """
    @method_decorator(login_required)
    def get(self, request):
        """
        display this view
        """
        context = {
            "user_full_name": request.user.profile.name,
            "error": False,
        }

        return render_to_response("verify_student/photo_reverification.html", context)

    @method_decorator(login_required)
    def post(self, request):
        """
        submits the reverification to SoftwareSecure
        """

        try:
            attempt = SoftwareSecurePhotoVerification(user=request.user)
            b64_face_image = request.POST['face_image'].split(",")[1]
            b64_photo_id_image = request.POST['photo_id_image'].split(",")[1]

            attempt.upload_face_image(b64_face_image.decode('base64'))
            attempt.upload_photo_id_image(b64_photo_id_image.decode('base64'))
            attempt.mark_ready()

            # save this attempt
            attempt.save()
            # then submit it across
            attempt.submit()
            return HttpResponseRedirect(reverse('verify_student_reverification_confirmation'))
        except Exception:
            log.exception(
                "Could not submit verification attempt for user {}".format(request.user.id)
            )
            context = {
                "user_full_name": request.user.profile.name,
                "error": True,
            }
            return render_to_response("verify_student/photo_reverification.html", context)


class MidCourseReverifyView(View):
    """
    The mid-course reverification view.
    Needs to perform these functions:
        - take new face photo
        - retrieve the old id photo
        - submit these photos to photo verification service

    Does not need to worry about pricing
    """
    @method_decorator(login_required)
    def get(self, request, course_id):
        """
        display this view
        """
        course_id = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_id)
        course_enrollment = CourseEnrollment.get_or_create_enrollment(request.user, course_id)
        course_enrollment.update_enrollment(mode="verified")
        course_enrollment.emit_event(EVENT_NAME_USER_ENTERED_MIDCOURSE_REVERIFY_VIEW)
        context = {
            "user_full_name": request.user.profile.name,
            "error": False,
            "course_id": course_id.to_deprecated_string(),
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "reverify": True,
        }

        return render_to_response("verify_student/midcourse_photo_reverification.html", context)

    @method_decorator(login_required)
    def post(self, request, course_id):
        """
        submits the reverification to SoftwareSecure
        """
        try:
            now = datetime.datetime.now(UTC)
            course_id = CourseKey.from_string(course_id)
            window = MidcourseReverificationWindow.get_window(course_id, now)
            if window is None:
                raise WindowExpiredException
            attempt = SoftwareSecurePhotoVerification(user=request.user, window=window)
            b64_face_image = request.POST['face_image'].split(",")[1]

            attempt.upload_face_image(b64_face_image.decode('base64'))
            attempt.fetch_photo_id_image()
            attempt.mark_ready()

            attempt.save()
            attempt.submit()
            course_enrollment = CourseEnrollment.get_or_create_enrollment(request.user, course_id)
            course_enrollment.update_enrollment(mode="verified")
            course_enrollment.emit_event(EVENT_NAME_USER_SUBMITTED_MIDCOURSE_REVERIFY)
            return HttpResponseRedirect(reverse('verify_student_midcourse_reverification_confirmation'))

        except WindowExpiredException:
            log.exception(
                "User {} attempted to re-verify, but the window expired before the attempt".format(request.user.id)
            )
            return HttpResponseRedirect(reverse('verify_student_reverification_window_expired'))

        except Exception:
            log.exception(
                "Could not submit verification attempt for user {}".format(request.user.id)
            )
            context = {
                "user_full_name": request.user.profile.name,
                "error": True,
            }
            return render_to_response("verify_student/midcourse_photo_reverification.html", context)


@login_required
def midcourse_reverify_dash(request):
    """
    Shows the "course reverification dashboard", which displays the reverification status (must reverify,
    pending, approved, failed, etc) of all courses in which a student has a verified enrollment.
    """
    user = request.user
    course_enrollment_pairs = []
    for enrollment in CourseEnrollment.enrollments_for_user(user):
        try:
            course_enrollment_pairs.append((modulestore().get_course(enrollment.course_id), enrollment))
        except ItemNotFoundError:
            log.error("User {0} enrolled in non-existent course {1}".format(user.username, enrollment.course_id))

    statuses = ["approved", "pending", "must_reverify", "denied"]

    reverifications = reverification_info(course_enrollment_pairs, user, statuses)

    context = {
        "user_full_name": user.profile.name,
        'reverifications': reverifications,
        'referer': request.META.get('HTTP_REFERER'),
        'billing_email': settings.PAYMENT_SUPPORT_EMAIL,
    }
    return render_to_response("verify_student/midcourse_reverify_dash.html", context)


@login_required
@require_POST
def toggle_failed_banner_off(request):
    """
    Finds all denied midcourse reverifications for a user and permanently toggles
    the "Reverification Failed" banner off for those verifications.
    """
    user_id = request.user.id
    SoftwareSecurePhotoVerification.display_off(user_id)
    return HttpResponse('Success')



@login_required
def reverification_submission_confirmation(_request):
    """
    Shows the user a confirmation page if the submission to SoftwareSecure was successful
    """
    return render_to_response("verify_student/reverification_confirmation.html")


@login_required
def midcourse_reverification_confirmation(_request):  # pylint: disable=C0103
    """
    Shows the user a confirmation page if the submission to SoftwareSecure was successful
    """
    return render_to_response("verify_student/midcourse_reverification_confirmation.html")


@login_required
def reverification_window_expired(_request):
    """
    Displays an error page if a student tries to submit a reverification, but the window
    for that reverification has already expired.
    """
    # TODO need someone to review the copy for this template
    return render_to_response("verify_student/reverification_window_expired.html")
