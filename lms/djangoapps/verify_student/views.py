"""
Views for the verification flow

"""
import json
import logging
import decimal
import datetime
from collections import namedtuple
from pytz import UTC

from edxmako.shortcuts import render_to_response, render_to_string

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseBadRequest,
    HttpResponseRedirect, Http404
)
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _, ugettext_lazy
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

from openedx.core.djangoapps.user_api.api import profile as profile_api

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
from microsite_configuration import microsite

from util.json_request import JsonResponse
from util.date_utils import get_default_time_display

log = logging.getLogger(__name__)

EVENT_NAME_USER_ENTERED_MIDCOURSE_REVERIFY_VIEW = 'edx.course.enrollment.reverify.started'
EVENT_NAME_USER_SUBMITTED_MIDCOURSE_REVERIFY = 'edx.course.enrollment.reverify.submitted'
EVENT_NAME_USER_REVERIFICATION_REVIEWED_BY_SOFTWARESECURE = 'edx.course.enrollment.reverify.reviewed'


class PayAndVerifyView(View):
    """View for the "verify and pay" flow.

    This view is somewhat complicated, because the user
    can enter it from a number of different places:

    * From the "choose your track" page.
    * After completing payment.
    * From the dashboard in order to complete verification.
    * From the dashboard in order to upgrade to a verified track.

    The page will display different steps and requirements
    depending on:

    * Whether the user has submitted a photo verification recently.
    * Whether the user has paid for the course.
    * How the user reached the page (mostly affects messaging)

    We are also super-paranoid about how users reach this page.
    If they somehow aren't enrolled, or the course doesn't exist,
    or they've unenrolled, or they've already paid/verified,
    ... then we try to redirect them to the page with the
    most appropriate messaging (including the dashboard).

    Note that this page does NOT handle re-verification
    (photo verification that was denied or had an error);
    that is handled by the "reverify" view.

    """

    # Step definitions
    #
    # These represent the numbered steps a user sees in
    # the verify / payment flow.
    #
    # Steps can either be:
    # - displayed or hidden
    # - complete or incomplete
    #
    # For example, when a user enters the verification/payment
    # flow for the first time, the user will see steps
    # for both payment and verification.  As the user
    # completes these steps (for example, submitting a photo)
    # the steps will be marked "complete".
    #
    # If a user has already verified for another course,
    # then the verification steps will be hidden,
    # since the user has already completed them.
    #
    # If a user re-enters the flow from another application
    # (for example, after completing payment through
    # a third-party payment processor), then the user
    # will resume the flow at an intermediate step.
    #
    INTRO_STEP = 'intro-step'
    MAKE_PAYMENT_STEP = 'make-payment-step'
    PAYMENT_CONFIRMATION_STEP = 'payment-confirmation-step'
    FACE_PHOTO_STEP = 'face-photo-step'
    ID_PHOTO_STEP = 'id-photo-step'
    REVIEW_PHOTOS_STEP = 'review-photos-step'
    ENROLLMENT_CONFIRMATION_STEP = 'enrollment-confirmation-step'

    ALL_STEPS = [
        INTRO_STEP,
        MAKE_PAYMENT_STEP,
        PAYMENT_CONFIRMATION_STEP,
        FACE_PHOTO_STEP,
        ID_PHOTO_STEP,
        REVIEW_PHOTOS_STEP,
        ENROLLMENT_CONFIRMATION_STEP
    ]

    PAYMENT_STEPS = [
        MAKE_PAYMENT_STEP,
        PAYMENT_CONFIRMATION_STEP
    ]

    VERIFICATION_STEPS = [
        FACE_PHOTO_STEP,
        ID_PHOTO_STEP,
        REVIEW_PHOTOS_STEP,
        ENROLLMENT_CONFIRMATION_STEP
    ]

    # These steps can be skipped using the ?skip-first-step GET param
    SKIP_STEPS = [
        INTRO_STEP,
    ]

    Step = namedtuple(
        'Step',
        [
            'title',
            'template_name'
        ]
    )

    STEP_INFO = {
        INTRO_STEP: Step(
            title=ugettext_lazy("Intro"),
            template_name="intro_step"
        ),
        MAKE_PAYMENT_STEP: Step(
            title=ugettext_lazy("Make payment"),
            template_name="make_payment_step"
        ),
        PAYMENT_CONFIRMATION_STEP: Step(
            title=ugettext_lazy("Payment confirmation"),
            template_name="payment_confirmation_step"
        ),
        FACE_PHOTO_STEP: Step(
            title=ugettext_lazy("Take photo"),
            template_name="face_photo_step"
        ),
        ID_PHOTO_STEP: Step(
            title=ugettext_lazy("Take a photo of your ID"),
            template_name="id_photo_step"
        ),
        REVIEW_PHOTOS_STEP: Step(
            title=ugettext_lazy("Review your info"),
            template_name="review_photos_step"
        ),
        ENROLLMENT_CONFIRMATION_STEP: Step(
            title=ugettext_lazy("Enrollment confirmation"),
            template_name="enrollment_confirmation_step"
        ),
    }

    # Messages
    #
    # Depending on how the user entered reached the page,
    # we will display different text messaging.
    # For example, we show users who are upgrading
    # slightly different copy than users who are verifying
    # for the first time.
    #
    FIRST_TIME_VERIFY_MSG = 'first-time-verify'
    VERIFY_NOW_MSG = 'verify-now'
    VERIFY_LATER_MSG = 'verify-later'
    UPGRADE_MSG = 'upgrade'
    PAYMENT_CONFIRMATION_MSG = 'payment-confirmation'

    # Requirements
    #
    # These explain to the user what he or she
    # will need to successfully pay and/or verify.
    #
    # These are determined by the steps displayed
    # to the user; for example, if the user does not
    # need to complete the verification steps,
    # then the photo ID and webcam requirements are hidden.
    #
    ACCOUNT_ACTIVATION_REQ = "account-activation-required"
    PHOTO_ID_REQ = "photo-id-required"
    WEBCAM_REQ = "webcam-required"

    STEP_REQUIREMENTS = {
        ID_PHOTO_STEP: [PHOTO_ID_REQ, WEBCAM_REQ],
        FACE_PHOTO_STEP: [WEBCAM_REQ],
    }

    @method_decorator(login_required)
    def get(
        self, request, course_id,
        always_show_payment=False,
        current_step=None,
        message=FIRST_TIME_VERIFY_MSG
    ):
        """Render the pay/verify requirements page.

        Arguments:
            request (HttpRequest): The request object.
            course_id (unicode): The ID of the course the user is trying
                to enroll in.

        Keyword Arguments:
            always_show_payment (bool): If True, show the payment steps
                even if the user has already paid.  This is useful
                for users returning to the flow after paying.
            current_step (string): The current step in the flow.
            message (string): The messaging to display.

        Returns:
            HttpResponse

        Raises:
            Http404: The course does not exist or does not
                have a verified mode.

        """
        # Parse the course key
        # The URL regex should guarantee that the key format is valid.
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)

        # Verify that the course exists and has a verified mode
        if course is None:
            log.warn(u"No course specified for verification flow request.")
            raise Http404

        # Verify that the course has a verified mode
        course_mode = CourseMode.verified_mode_for_course(course_key)
        if course_mode is None:
            log.warn(
                u"No verified course mode found for course '{course_id}' for verification flow request"
                .format(course_id=course_id)
            )
            raise Http404

        log.info(
            u"Entering verified workflow for user '{user}', course '{course_id}', with current step '{current_step}'."
            .format(user=request.user, course_id=course_id, current_step=current_step)
        )

        # Check whether the user has verified, paid, and enrolled.
        # A user is considered "paid" if he or she has an enrollment
        # with a paid course mode (such as "verified").
        # For this reason, every paid user is enrolled, but not
        # every enrolled user is paid.
        already_verified = self._check_already_verified(request.user)
        already_paid, is_enrolled = self._check_enrollment(request.user, course_key)

        # Redirect the user to a more appropriate page if the
        # messaging won't make sense based on the user's
        # enrollment / payment / verification status.
        redirect_response = self._redirect_if_necessary(
            message,
            already_verified,
            already_paid,
            is_enrolled,
            course_key
        )
        if redirect_response is not None:
            return redirect_response

        display_steps = self._display_steps(
            always_show_payment,
            already_verified,
            already_paid
        )
        requirements = self._requirements(display_steps, request.user.is_active)

        if current_step is None:
            current_step = display_steps[0]['name']

        # Allow the caller to skip the first page
        # This is useful if we want the user to be able to
        # use the "back" button to return to the previous step.
        # This parameter should only work for known skip-able steps
        if request.GET.get('skip-first-step') and current_step in self.SKIP_STEPS:
            display_step_names = [step['name'] for step in display_steps]
            current_step_idx = display_step_names.index(current_step)
            if (current_step_idx + 1) < len(display_steps):
                current_step = display_steps[current_step_idx + 1]['name']

        courseware_url = ""
        if not course.start or course.start < datetime.datetime.today().replace(tzinfo=UTC):
            courseware_url = reverse(
                'course_root',
                kwargs={'course_id': unicode(course_key)}
            )

        full_name = (
            request.user.profile.name
            if request.user.profile.name
            else ""
        )

        # If the user set a contribution amount on another page,
        # use that amount to pre-fill the price selection form.
        contribution_amount = request.session.get(
            'donation_for_course', {}
        ).get(unicode(course_key), '')

        # Remember whether the user is upgrading
        # so we can fire an analytics event upon payment.
        request.session['attempting_upgrade'] = (message == self.UPGRADE_MSG)

        # Render the top-level page
        context = {
            'contribution_amount': contribution_amount,
            'course': course,
            'course_key': unicode(course_key),
            'course_mode': course_mode,
            'courseware_url': courseware_url,
            'current_step': current_step,
            'disable_courseware_js': True,
            'display_steps': display_steps,
            'is_active': json.dumps(request.user.is_active),
            'message_key': message,
            'platform_name': settings.PLATFORM_NAME,
            'purchase_endpoint': get_purchase_endpoint(),
            'requirements': requirements,
            'user_full_name': full_name,
            'verification_deadline': (
                get_default_time_display(course_mode.expiration_datetime)
                if course_mode.expiration_datetime else ""
            ),
        }
        return render_to_response("verify_student/pay_and_verify.html", context)

    def _redirect_if_necessary(
        self,
        message,
        already_verified,
        already_paid,
        is_enrolled,
        course_key
    ):
        """Redirect the user to a more appropriate page if necessary.

        In some cases, a user may visit this page with
        verification / enrollment / payment state that
        we don't anticipate.  For example, a user may unenroll
        from the course after paying for it, then visit the
        "verify now" page to complete verification.

        When this happens, we try to redirect the user to
        the most appropriate page.

        Arguments:

            message (string): The messaging of the page.  Should be a key
                in `MESSAGES`.

            already_verified (bool): Whether the user has submitted
                a verification request recently.

            already_paid (bool): Whether the user is enrolled in a paid
                course mode.

            is_enrolled (bool): Whether the user has an active enrollment
                in the course.

            course_key (CourseKey): The key for the course.

        Returns:
            HttpResponse or None

        """
        url = None
        course_kwargs = {'course_id': unicode(course_key)}

        if already_verified and already_paid:
            # If they've already paid and verified, there's nothing else to do,
            # so redirect them to the dashboard.
            if message != self.PAYMENT_CONFIRMATION_MSG:
                url = reverse('dashboard')
        elif message in [self.VERIFY_NOW_MSG, self.VERIFY_LATER_MSG, self.PAYMENT_CONFIRMATION_MSG]:
            if is_enrolled:
                # If the user is already enrolled but hasn't yet paid,
                # then the "upgrade" messaging is more appropriate.
                if not already_paid:
                    url = reverse('verify_student_upgrade_and_verify', kwargs=course_kwargs)
            else:
                # If the user is NOT enrolled, then send him/her
                # to the first time verification page.
                url = reverse('verify_student_start_flow', kwargs=course_kwargs)
        elif message == self.UPGRADE_MSG:
            if is_enrolled:
                # If upgrading and we've paid but haven't verified,
                # then the "verify later" messaging makes more sense.
                if already_paid:
                    url = reverse('verify_student_verify_later', kwargs=course_kwargs)
            else:
                url = reverse('verify_student_start_flow', kwargs=course_kwargs)

        # Redirect if necessary, otherwise implicitly return None
        if url is not None:
            return redirect(url)

    def _display_steps(self, always_show_payment, already_verified, already_paid):
        """Determine which steps to display to the user.

        Includes all steps by default, but removes steps
        if the user has already completed them.

        Arguments:

            always_show_payment (bool): If True, display the payment steps
                even if the user has already paid.

            already_verified (bool): Whether the user has submitted
                a verification request recently.

            already_paid (bool): Whether the user is enrolled in a paid
                course mode.

        Returns:
            list

        """
        display_steps = self.ALL_STEPS
        remove_steps = set()

        if already_verified:
            remove_steps |= set(self.VERIFICATION_STEPS)

        if already_paid and not always_show_payment:
            remove_steps |= set(self.PAYMENT_STEPS)
        else:
            # The "make payment" step doubles as an intro step,
            # so if we're showing the payment step, hide the intro step.
            remove_steps |= set([self.INTRO_STEP])

        return [
            {
                'name': step,
                'title': unicode(self.STEP_INFO[step].title),
                'templateName': self.STEP_INFO[step].template_name
            }
            for step in display_steps
            if step not in remove_steps
        ]

    def _requirements(self, display_steps, is_active):
        """Determine which requirements to show the user.

        For example, if the user needs to submit a photo
        verification, tell the user that she will need
        a photo ID and a webcam.

        Arguments:
            display_steps (list): The steps to display to the user.
            is_active (bool): If False, adds a requirement to activate the user account.

        Returns:
            dict: Keys are requirement names, values are booleans
                indicating whether to show the requirement.

        """
        all_requirements = {
            self.ACCOUNT_ACTIVATION_REQ: not is_active,
            self.PHOTO_ID_REQ: False,
            self.WEBCAM_REQ: False,
        }

        display_steps = set(step['name'] for step in display_steps)

        for step, step_requirements in self.STEP_REQUIREMENTS.iteritems():
            if step in display_steps:
                for requirement in step_requirements:
                    all_requirements[requirement] = True

        return all_requirements

    def _check_already_verified(self, user):
        """Check whether the user has a valid or pending verification.

        Note that this includes cases in which the user's verification
        has not been accepted (either because it hasn't been processed,
        or there was an error).

        This should return True if the user has done their part:
        submitted photos within the expiration period.

        """
        return SoftwareSecurePhotoVerification.user_has_valid_or_pending(user)

    def _check_enrollment(self, user, course_key):
        """Check whether the user has an active enrollment and has paid.

        If a user is enrolled in a paid course mode, we assume
        that the user has paid.

        Arguments:
            user (User): The user to check.
            course_key (CourseKey): The key of the course to check.

        Returns:
            Tuple `(has_paid, is_active)` indicating whether the user
            has paid and whether the user has an active account.

        """
        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_key)
        has_paid = False

        if enrollment_mode is not None and is_active:
            all_modes = CourseMode.modes_for_course_dict(course_key)
            course_mode = all_modes.get(enrollment_mode)
            has_paid = (course_mode and course_mode.min_price > 0)

        return (has_paid, bool(is_active))


@require_POST
@login_required
def create_order(request):
    """
    Submit PhotoVerification and create a new Order for this verified cert
    """
    # Only submit photos if photo data is provided by the client.
    # TODO (ECOM-188): Once the A/B test of decoupling verified / payment
    # completes, we may be able to remove photo submission from this step
    # entirely.
    submit_photo = (
        'face_image' in request.POST and
        'photo_id_image' in request.POST
    )

    if (
        submit_photo and not
        SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user)
    ):
        attempt = SoftwareSecurePhotoVerification(user=request.user)
        try:
            b64_face_image = request.POST['face_image'].split(",")[1]
            b64_photo_id_image = request.POST['photo_id_image'].split(",")[1]
        except IndexError:
            log.error(u"Invalid image data during photo verification.")
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
        log.warn(u"Verification requested for course {course_id} without a verified mode.".format(course_id=course_id))
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
        cart,
        callback_url=callback_url,
        extra_data=[unicode(course_id), current_mode.slug]
    )

    params['success'] = True
    return HttpResponse(json.dumps(params), content_type="text/json")


@require_POST
@login_required
def submit_photos_for_verification(request):
    """Submit a photo verification attempt.

    Arguments:
        request (HttpRequest): The request to submit photos.

    Returns:
        HttpResponse: 200 on success, 400 if there are errors.

    """
    # Check the required parameters
    missing_params = set(['face_image', 'photo_id_image']) - set(request.POST.keys())
    if len(missing_params) > 0:
        msg = _("Missing required parameters: {missing}").format(missing=", ".join(missing_params))
        return HttpResponseBadRequest(msg)

    # If the user already has valid or pending request, the UI will hide
    # the verification steps.  For this reason, we reject any requests
    # for users that already have a valid or pending verification.
    if SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
        return HttpResponseBadRequest(_("You already have a valid or pending verification."))

    username = request.user.username

    # If the user wants to change his/her full name,
    # then try to do that before creating the attempt.
    if request.POST.get('full_name'):
        try:
            profile_api.update_profile(
                username,
                full_name=request.POST.get('full_name')
            )
        except profile_api.ProfileUserNotFound:
            return HttpResponseBadRequest(_("No profile found for user"))
        except profile_api.ProfileInvalidField:
            msg = _(
                "Name must be at least {min_length} characters long."
            ).format(min_length=profile_api.FULL_NAME_MIN_LENGTH)
            return HttpResponseBadRequest(msg)

    # Create the attempt
    attempt = SoftwareSecurePhotoVerification(user=request.user)
    try:
        b64_face_image = request.POST['face_image'].split(",")[1]
        b64_photo_id_image = request.POST['photo_id_image'].split(",")[1]
    except IndexError:
        msg = _("Image data is not valid.")
        return HttpResponseBadRequest(msg)

    attempt.upload_face_image(b64_face_image.decode('base64'))
    attempt.upload_photo_id_image(b64_photo_id_image.decode('base64'))
    attempt.mark_ready()
    attempt.submit()

    profile_dict = profile_api.profile_info(username)
    if profile_dict:
        # Send a confirmation email to the user
        context = {
            'full_name': profile_dict.get('full_name'),
            'platform_name': settings.PLATFORM_NAME
        }

        subject = _("Verification photos received")
        message = render_to_string('emails/photo_submission_confirmation.txt', context)
        from_address = microsite.get_value('default_from_email', settings.DEFAULT_FROM_EMAIL)
        to_address = profile_dict.get('email')

        send_mail(subject, message, from_address, [to_address], fail_silently=False)

    return HttpResponse(200)


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
        if course is None:
            raise Http404

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
def midcourse_reverification_confirmation(_request):  # pylint: disable=invalid-name
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
