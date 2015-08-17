"""
Views for the verification flow
"""

import datetime
import decimal
import json
import logging
from pytz import UTC
from ipware.ip import get_ip

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _, ugettext_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic.base import View, RedirectView

import analytics
from eventtracking import tracker
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError

from commerce import ecommerce_api_client
from commerce.utils import audit_log
from course_modes.models import CourseMode
from courseware.url_helpers import get_redirect_url
from ecommerce_api_client.exceptions import SlumberBaseException
from edxmako.shortcuts import render_to_response, render_to_string
from embargo import api as embargo_api
from microsite_configuration import microsite
from openedx.core.djangoapps.user_api.accounts import NAME_MIN_LENGTH
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings, update_account_settings
from openedx.core.djangoapps.user_api.errors import UserNotFound, AccountValidationError
from openedx.core.djangoapps.credit.api import set_credit_requirement_status
from student.models import CourseEnrollment
from shoppingcart.models import Order, CertificateItem
from shoppingcart.processors import (
    get_signed_purchase_params, get_purchase_endpoint
)
from verify_student.ssencrypt import has_valid_signature
from verify_student.models import (
    SoftwareSecurePhotoVerification,
    VerificationCheckpoint,
    VerificationStatus,
    InCourseReverificationConfiguration
)
from util.json_request import JsonResponse
from util.date_utils import get_default_time_display
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from staticfiles.storage import staticfiles_storage


log = logging.getLogger(__name__)


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

    STEP_TITLES = {
        INTRO_STEP: ugettext_lazy("Intro"),
        MAKE_PAYMENT_STEP: ugettext_lazy("Make payment"),
        PAYMENT_CONFIRMATION_STEP: ugettext_lazy("Payment confirmation"),
        FACE_PHOTO_STEP: ugettext_lazy("Take photo"),
        ID_PHOTO_STEP: ugettext_lazy("Take a photo of your ID"),
        REVIEW_PHOTOS_STEP: ugettext_lazy("Review your info"),
        ENROLLMENT_CONFIRMATION_STEP: ugettext_lazy("Enrollment confirmation"),
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

        # Check whether the user has access to this course
        # based on country access rules.
        redirect_url = embargo_api.redirect_if_blocked(
            course_key,
            user=request.user,
            ip_address=get_ip(request),
            url=request.path
        )
        if redirect_url:
            return redirect(redirect_url)

        expired_verified_course_mode, unexpired_paid_course_mode = self._get_expired_verified_and_paid_mode(course_key)

        # Check that the course has an unexpired paid mode
        if unexpired_paid_course_mode is not None:
            if CourseMode.is_verified_mode(unexpired_paid_course_mode):
                log.info(
                    u"Entering verified workflow for user '%s', course '%s', with current step '%s'.",
                    request.user.id, course_id, current_step
                )
        elif expired_verified_course_mode is not None:
            # Check if there is an *expired* verified course mode;
            # if so, we should show a message explaining that the verification
            # deadline has passed.
            log.info(u"Verification deadline for '%s' has passed.", course_id)
            context = {
                'course': course,
                'deadline': (
                    get_default_time_display(expired_verified_course_mode.expiration_datetime)
                    if expired_verified_course_mode.expiration_datetime else ""
                )
            }
            return render_to_response("verify_student/missed_verification_deadline.html", context)
        else:
            # Otherwise, there has never been a verified/paid mode,
            # so return a page not found response.
            log.warn(
                u"No paid/verified course mode found for course '%s' for verification/payment flow request",
                course_id
            )
            raise Http404

        # Check whether the user has verified, paid, and enrolled.
        # A user is considered "paid" if he or she has an enrollment
        # with a paid course mode (such as "verified").
        # For this reason, every paid user is enrolled, but not
        # every enrolled user is paid.
        # If the course mode is not verified(i.e only paid) then already_verified is always True
        already_verified = self._check_already_verified(request.user) \
            if CourseMode.is_verified_mode(unexpired_paid_course_mode) else True
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
            already_paid,
            unexpired_paid_course_mode
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

        # Determine the photo verification status
        verification_good_until = self._verification_valid_until(request.user)

        # get available payment processors
        if unexpired_paid_course_mode.sku:
            # transaction will be conducted via ecommerce service
            processors = ecommerce_api_client(request.user).payment.processors.get()
        else:
            # transaction will be conducted using legacy shopping cart
            processors = [settings.CC_PROCESSOR_NAME]

        # Render the top-level page
        context = {
            'contribution_amount': contribution_amount,
            'course': course,
            'course_key': unicode(course_key),
            'course_mode': unexpired_paid_course_mode,
            'courseware_url': courseware_url,
            'current_step': current_step,
            'disable_courseware_js': True,
            'display_steps': display_steps,
            'is_active': json.dumps(request.user.is_active),
            'message_key': message,
            'platform_name': settings.PLATFORM_NAME,
            'processors': processors,
            'requirements': requirements,
            'user_full_name': full_name,
            'verification_deadline': (
                get_default_time_display(unexpired_paid_course_mode.expiration_datetime)
                if unexpired_paid_course_mode.expiration_datetime else ""
            ),
            'already_verified': already_verified,
            'verification_good_until': verification_good_until,
            'capture_sound': staticfiles_storage.url("audio/camera_capture.wav"),
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
                if already_paid:
                    # If the student has paid, but not verified, redirect to the verification flow.
                    url = reverse('verify_student_verify_now', kwargs=course_kwargs)
            else:
                url = reverse('verify_student_start_flow', kwargs=course_kwargs)

        # Redirect if necessary, otherwise implicitly return None
        if url is not None:
            return redirect(url)

    def _get_expired_verified_and_paid_mode(self, course_key):  # pylint: disable=invalid-name
        """Retrieve expired verified mode and unexpired paid mode(with min_price>0) for a course.

        Arguments:
            course_key (CourseKey): The location of the course.

        Returns:
            Tuple of `(expired_verified_mode, unexpired_paid_mode)`.  If provided,
                `expired_verified_mode` is an *expired* verified mode for the course.
                If provided, `unexpired_paid_mode` is an *unexpired* paid(with min_price>0)
                mode for the course.  Either of these may be None.

        """
        # Retrieve all the modes at once to reduce the number of database queries
        all_modes, unexpired_modes = CourseMode.all_and_unexpired_modes_for_courses([course_key])

        # Unexpired paid modes
        unexpired_paid_modes = [mode for mode in unexpired_modes[course_key] if mode.min_price]
        if len(unexpired_paid_modes) > 1:
            # There is more than one paid mode defined,
            # so choose the first one.
            log.warn(
                u"More than one paid modes are defined for course '%s' choosing the first one %s",
                course_key, unexpired_paid_modes[0]
            )
        unexpired_paid_mode = unexpired_paid_modes[0] if unexpired_paid_modes else None

        # Find an unexpired verified mode
        verified_mode = CourseMode.verified_mode_for_course(course_key, modes=unexpired_modes[course_key])
        expired_verified_mode = None

        if verified_mode is None:
            expired_verified_mode = CourseMode.verified_mode_for_course(course_key, modes=all_modes[course_key])

        return (expired_verified_mode, unexpired_paid_mode)

    def _display_steps(self, always_show_payment, already_verified, already_paid, course_mode):
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

        if already_verified or not CourseMode.is_verified_mode(course_mode):
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
                'title': unicode(self.STEP_TITLES[step]),
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

    def _verification_valid_until(self, user, date_format="%m/%d/%Y"):
        """
        Check whether the user has a valid or pending verification.

        Arguments:
            user:
            date_format: optional parameter for formatting datetime
                object to string in response

        Returns:
            datetime object in string format
        """
        photo_verifications = SoftwareSecurePhotoVerification.verification_valid_or_pending(user)
        # return 'expiration_datetime' of latest photo verification if found,
        # otherwise implicitly return ''
        if photo_verifications:
            return photo_verifications[0].expiration_datetime.strftime(date_format)

        return ''

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


def checkout_with_ecommerce_service(user, course_key, course_mode, processor):     # pylint: disable=invalid-name
    """ Create a new basket and trigger immediate checkout, using the E-Commerce API. """
    course_id = unicode(course_key)
    try:
        api = ecommerce_api_client(user)
        # Make an API call to create the order and retrieve the results
        result = api.baskets.post({
            'products': [{'sku': course_mode.sku}],
            'checkout': True,
            'payment_processor_name': processor
        })

        # Pass the payment parameters directly from the API response.
        return result.get('payment_data')
    except SlumberBaseException:
        params = {'username': user.username, 'mode': course_mode.slug, 'course_id': course_id}
        log.exception('Failed to create order for %(username)s %(mode)s mode of %(course_id)s', params)
        raise
    finally:
        audit_log(
            'checkout_requested',
            course_id=course_id,
            mode=course_mode.slug,
            processor_name=processor,
            user_id=user.id
        )


def checkout_with_shoppingcart(request, user, course_key, course_mode, amount):
    """ Create an order and trigger checkout using shoppingcart."""
    cart = Order.get_cart_for_user(user)
    cart.clear()
    enrollment_mode = course_mode.slug
    CertificateItem.add_to_order(cart, course_key, amount, enrollment_mode)

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

    payment_data = {
        'payment_processor_name': settings.CC_PROCESSOR_NAME,
        'payment_page_url': get_purchase_endpoint(),
        'payment_form_data': get_signed_purchase_params(
            cart,
            callback_url=callback_url,
            extra_data=[unicode(course_key), course_mode.slug]
        ),
    }
    return payment_data


@require_POST
@login_required
def create_order(request):
    """
    This endpoint is named 'create_order' for backward compatibility, but its
    actual use is to add a single product to the user's cart and request
    immediate checkout.
    """
    course_id = request.POST['course_id']
    course_id = CourseKey.from_string(course_id)
    donation_for_course = request.session.get('donation_for_course', {})
    contribution = request.POST.get("contribution", donation_for_course.get(unicode(course_id), 0))
    try:
        amount = decimal.Decimal(contribution).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
    except decimal.InvalidOperation:
        return HttpResponseBadRequest(_("Selected price is not valid number."))

    current_mode = None
    paid_modes = CourseMode.paid_modes_for_course(course_id)
    # Check if there are more than 1 paid(mode with min_price>0 e.g verified/professional/no-id-professional) modes
    # for course exist then choose the first one
    if paid_modes:
        if len(paid_modes) > 1:
            log.warn(u"Multiple paid course modes found for course '%s' for create order request", course_id)
        current_mode = paid_modes[0]

    # Make sure this course has a paid mode
    if not current_mode:
        log.warn(u"Create order requested for course '%s' without a paid mode.", course_id)
        return HttpResponseBadRequest(_("This course doesn't support paid certificates"))

    if CourseMode.is_professional_mode(current_mode):
        amount = current_mode.min_price

    if amount < current_mode.min_price:
        return HttpResponseBadRequest(_("No selected price or selected price is below minimum."))

    if current_mode.sku:
        # if request.POST doesn't contain 'processor' then the service's default payment processor will be used.
        payment_data = checkout_with_ecommerce_service(
            request.user,
            course_id,
            current_mode,
            request.POST.get('processor')
        )
    else:
        payment_data = checkout_with_shoppingcart(request, request.user, course_id, current_mode, amount)

    if 'processor' not in request.POST:
        # (XCOM-214) To be removed after release.
        # the absence of this key in the POST payload indicates that the request was initiated from
        # a stale js client, which expects a response containing only the 'payment_form_data' part of
        # the payment data result.
        payment_data = payment_data['payment_form_data']
    return HttpResponse(json.dumps(payment_data), content_type="application/json")


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

    # If the user wants to change his/her full name,
    # then try to do that before creating the attempt.
    if request.POST.get('full_name'):
        try:
            update_account_settings(request.user, {"name": request.POST.get('full_name')})
        except UserNotFound:
            return HttpResponseBadRequest(_("No profile found for user"))
        except AccountValidationError:
            msg = _(
                "Name must be at least {min_length} characters long."
            ).format(min_length=NAME_MIN_LENGTH)
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

    log.info(u"Submitted initial verification attempt for user %s", request.user.id)

    account_settings = get_account_settings(request.user)

    # Send a confirmation email to the user
    context = {
        'full_name': account_settings['name'],
        'platform_name': settings.PLATFORM_NAME
    }

    subject = _("Verification photos received")
    message = render_to_string('emails/photo_submission_confirmation.txt', context)
    from_address = microsite.get_value('default_from_email', settings.DEFAULT_FROM_EMAIL)
    to_address = account_settings['email']

    send_mail(subject, message, from_address, [to_address], fail_silently=False)

    return HttpResponse(200)


def _compose_message_reverification_email(
        course_key, user_id, related_assessment_location, status, request
):  # pylint: disable=invalid-name
    """
    Compose subject and message for photo reverification email.

    Args:
        course_key(CourseKey): CourseKey object
        user_id(str): User Id
        related_assessment_location(str): Location of reverification XBlock
        photo_verification(QuerySet): Queryset of SoftwareSecure objects
        status(str): Approval status
        is_secure(Bool): Is running on secure protocol or not

    Returns:
        None if any error occurred else Tuple of subject and message strings
    """
    try:
        usage_key = UsageKey.from_string(related_assessment_location)
        reverification_block = modulestore().get_item(usage_key)

        course = modulestore().get_course(course_key)
        redirect_url = get_redirect_url(course_key, usage_key.replace(course_key=course_key))

        subject = "Re-verification Status"
        context = {
            "status": status,
            "course_name": course.display_name_with_default,
            "assessment": reverification_block.related_assessment
        }

        # Allowed attempts is 1 if not set on verification block
        allowed_attempts = reverification_block.attempts + 1
        used_attempts = VerificationStatus.get_user_attempts(user_id, course_key, related_assessment_location)
        left_attempts = allowed_attempts - used_attempts
        is_attempt_allowed = left_attempts > 0
        verification_open = True
        if reverification_block.due:
            verification_open = timezone.now() <= reverification_block.due

        context["left_attempts"] = left_attempts
        context["is_attempt_allowed"] = is_attempt_allowed
        context["verification_open"] = verification_open
        context["due_date"] = get_default_time_display(reverification_block.due)

        context['platform_name'] = settings.PLATFORM_NAME
        context["used_attempts"] = used_attempts
        context["allowed_attempts"] = allowed_attempts
        context["support_link"] = microsite.get_value('email_from_address', settings.CONTACT_EMAIL)

        re_verification_link = reverse(
            'verify_student_incourse_reverify',
            args=(
                unicode(course_key),
                related_assessment_location
            )
        )

        context["course_link"] = request.build_absolute_uri(redirect_url)
        context["reverify_link"] = request.build_absolute_uri(re_verification_link)

        message = render_to_string('emails/reverification_processed.txt', context)
        log.info(
            "Sending email to User_Id=%s. Attempts left for this user are %s. "
            "Allowed attempts %s. "
            "Due Date %s",
            str(user_id), left_attempts, allowed_attempts, str(reverification_block.due)
        )
        return subject, message
    # Catch all exception to avoid raising back to view
    except:  # pylint: disable=bare-except
        log.exception("The email for re-verification sending failed for user_id %s", user_id)


def _send_email(user_id, subject, message):
    """ Send email to given user

    Args:
        user_id(str): User Id
        subject(str): Subject lines of emails
        message(str): Email message body

    Returns:
        None
    """
    from_address = microsite.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )
    user = User.objects.get(id=user_id)
    user.email_user(subject, message, from_address)


def _set_user_requirement_status(attempt, namespace, status, reason=None):
    """Sets the status of a credit requirement for the user,
    based on a verification checkpoint.
    """
    checkpoint = None
    try:
        checkpoint = VerificationCheckpoint.objects.get(photo_verification=attempt)
    except VerificationCheckpoint.DoesNotExist:
        log.error("Unable to find checkpoint for user with id %d", attempt.user.id)

    if checkpoint is not None:
        try:
            set_credit_requirement_status(
                attempt.user.username,
                checkpoint.course_id,
                namespace,
                checkpoint.checkpoint_location,
                status=status,
                reason=reason,
            )
        except Exception:  # pylint: disable=broad-except
            # Catch exception if unable to add credit requirement
            # status for user
            log.error("Unable to add Credit requirement status for user with id %d", attempt.user.id)


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

    has_valid_signature(
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
        log.error("Software Secure posted back for receipt_id %s, but not found", receipt_id)
        return HttpResponseBadRequest("edX ID {} not found".format(receipt_id))
    if result == "PASS":
        log.debug("Approving verification for %s", receipt_id)
        attempt.approve()
        status = "approved"
        _set_user_requirement_status(attempt, 'reverification', 'satisfied')

    elif result == "FAIL":
        log.debug("Denying verification for %s", receipt_id)
        attempt.deny(json.dumps(reason), error_code=error_code)
        status = "denied"
        _set_user_requirement_status(
            attempt, 'reverification', 'failed', json.dumps(reason)
        )
    elif result == "SYSTEM FAIL":
        log.debug("System failure for %s -- resetting to must_retry", receipt_id)
        attempt.system_error(json.dumps(reason), error_code=error_code)
        status = "error"
        log.error("Software Secure callback attempt for %s failed: %s", receipt_id, reason)
    else:
        log.error("Software Secure returned unknown result %s", result)
        return HttpResponseBadRequest(
            "Result {} not understood. Known results: PASS, FAIL, SYSTEM FAIL".format(result)
        )
    incourse_reverify_enabled = InCourseReverificationConfiguration.current().enabled
    if incourse_reverify_enabled:
        checkpoints = VerificationCheckpoint.objects.filter(photo_verification=attempt).all()
        VerificationStatus.add_status_from_checkpoints(checkpoints=checkpoints, user=attempt.user, status=status)
        # If this is re-verification then send the update email
        if checkpoints:
            user_id = attempt.user.id
            course_key = checkpoints[0].course_id
            related_assessment_location = checkpoints[0].checkpoint_location

            subject, message = _compose_message_reverification_email(
                course_key, user_id, related_assessment_location, status, request
            )

            _send_email(user_id, subject, message)
    return HttpResponse("OK!")


class ReverifyView(View):
    """
    Reverification occurs when a user's initial verification is denied
    or expires.  When this happens, users can re-submit photos through
    the re-verification flow.

    Unlike in-course reverification, this flow requires users to submit
    *both* face and ID photos.  In contrast, during in-course reverification,
    students submit only face photos, which are matched against the ID photo
    the user submitted during initial verification.

    """
    @method_decorator(login_required)
    def get(self, request):
        """
        Render the reverification flow.

        Most of the work is done client-side by composing the same
        Backbone views used in the initial verification flow.
        """
        status, _ = SoftwareSecurePhotoVerification.user_status(request.user)
        if status in ["must_reverify", "expired"]:
            context = {
                "user_full_name": request.user.profile.name,
                "platform_name": settings.PLATFORM_NAME,
                "capture_sound": staticfiles_storage.url("audio/camera_capture.wav"),
            }
            return render_to_response("verify_student/reverify.html", context)
        else:
            context = {
                "status": status
            }
            return render_to_response("verify_student/reverify_not_allowed.html", context)


class InCourseReverifyView(View):
    """
    The in-course reverification view.

    In-course reverification occurs while a student is taking a course.
    At points in the course, students are prompted to submit face photos,
    which are matched against the ID photos the user submitted during their
    initial verification.

    Students are prompted to enter this flow from an "In Course Reverification"
    XBlock (courseware component) that course authors add to the course.
    See https://github.com/edx/edx-reverification-block for more details.

    """
    @method_decorator(login_required)
    def get(self, request, course_id, usage_id):
        """Display the view for face photo submission.

        Args:
            request(HttpRequest): HttpRequest object
            course_id(str): A string of course id
            usage_id(str): Location of Reverification XBlock in courseware

        Returns:
            HttpResponse
        """
        # Check that in-course re-verification is enabled or not
        incourse_reverify_enabled = InCourseReverificationConfiguration.current().enabled

        if not incourse_reverify_enabled:
            log.error(
                u"In-course reverification is not enabled.  "
                u"You can enable it in Django admin by setting "
                u"InCourseReverificationConfiguration to enabled."
            )
            raise Http404

        user = request.user
        course_key = CourseKey.from_string(course_id)
        course = modulestore().get_course(course_key)
        if course is None:
            log.error(u"Could not find course '%s' for in-course reverification.", course_key)
            raise Http404

        checkpoint = VerificationCheckpoint.get_verification_checkpoint(course_key, usage_id)
        if checkpoint is None:
            log.error(
                u"No verification checkpoint exists for the "
                u"course '%s' and checkpoint location '%s'.",
                course_key, usage_id
            )
            raise Http404

        initial_verification = SoftwareSecurePhotoVerification.get_initial_verification(user)
        if not initial_verification:
            return self._redirect_no_initial_verification(user, course_key)

        # emit the reverification event
        self._track_reverification_events('edx.bi.reverify.started', user.id, course_id, checkpoint.checkpoint_name)

        context = {
            'course_key': unicode(course_key),
            'course_name': course.display_name_with_default,
            'checkpoint_name': checkpoint.checkpoint_name,
            'platform_name': settings.PLATFORM_NAME,
            'usage_id': usage_id,
            'capture_sound': staticfiles_storage.url("audio/camera_capture.wav"),
        }
        return render_to_response("verify_student/incourse_reverify.html", context)

    @method_decorator(login_required)
    def post(self, request, course_id, usage_id):
        """Submits the re-verification attempt to SoftwareSecure.

        Args:
            request(HttpRequest): HttpRequest object
            course_id(str): Course Id
            usage_id(str): Location of Reverification XBlock in courseware

        Returns:
            HttpResponse with status_code 400 if photo is missing or any error
            or redirect to the verification flow if initial verification
            doesn't exist otherwise HttpResponse with status code 200
        """
        # Check the in-course re-verification is enabled or not
        incourse_reverify_enabled = InCourseReverificationConfiguration.current().enabled
        if not incourse_reverify_enabled:
            raise Http404

        user = request.user
        try:
            course_key = CourseKey.from_string(course_id)
            usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)
        except InvalidKeyError:
            raise Http404(u"Invalid course_key or usage_key")

        course = modulestore().get_course(course_key)
        if course is None:
            log.error(u"Invalid course id '%s'", course_id)
            return HttpResponseBadRequest(_("Invalid course location."))

        checkpoint = VerificationCheckpoint.get_verification_checkpoint(course_key, usage_id)
        if checkpoint is None:
            log.error(
                u"Checkpoint is not defined. Could not submit verification attempt"
                u" for user '%s', course '%s' and checkpoint location '%s'.",
                request.user.id, course_key, usage_id
            )
            return HttpResponseBadRequest(_("Invalid checkpoint location."))

        init_verification = SoftwareSecurePhotoVerification.get_initial_verification(user)
        if not init_verification:
            return self._redirect_no_initial_verification(user, course_key)

        try:
            attempt = SoftwareSecurePhotoVerification.submit_faceimage(
                request.user, request.POST['face_image'], init_verification.photo_id_key
            )
            checkpoint.add_verification_attempt(attempt)
            VerificationStatus.add_verification_status(checkpoint, user, "submitted")

            # emit the reverification event
            self._track_reverification_events(
                'edx.bi.reverify.submitted',
                user.id, course_id, checkpoint.checkpoint_name
            )

            redirect_url = get_redirect_url(course_key, usage_key)
            response = JsonResponse({'url': redirect_url})

        except (ItemNotFoundError, NoPathToItem):
            log.warning(u"Could not find redirect URL for location %s in course %s", course_key, usage_key)
            redirect_url = reverse("courseware", args=(unicode(course_key),))
            response = JsonResponse({'url': redirect_url})

        except Http404 as expt:
            log.exception("Invalid location during photo verification.")
            response = HttpResponseBadRequest(expt.message)

        except IndexError:
            log.exception("Invalid image data during photo verification.")
            response = HttpResponseBadRequest(_("Invalid image data during photo verification."))

        except Exception:  # pylint: disable=broad-except
            log.exception("Could not submit verification attempt for user %s.", request.user.id)
            msg = _("Could not submit photos")
            response = HttpResponseBadRequest(msg)

        return response

    def _track_reverification_events(self, event_name, user_id, course_id, checkpoint):  # pylint: disable=invalid-name
        """Track re-verification events for a user against a reverification
        checkpoint of a course.

        Arguments:
            event_name (str): Name of event being tracked
            user_id (str): The ID of the user
            course_id (unicode): ID associated with the course
            checkpoint (str): Checkpoint name

        Returns:
            None
        """
        log.info(
            u"In-course reverification: event %s occurred for user '%s' in course '%s' at checkpoint '%s'",
            event_name, user_id, course_id, checkpoint
        )

        if settings.FEATURES.get('SEGMENT_IO_LMS') and hasattr(settings, 'SEGMENT_IO_LMS_KEY'):
            tracking_context = tracker.get_tracker().resolve_context()
            analytics.track(
                user_id,
                event_name,
                {
                    'category': "verification",
                    'label': unicode(course_id),
                    'checkpoint': checkpoint
                },
                context={
                    'Google Analytics': {
                        'clientId': tracking_context.get('client_id')
                    }
                }
            )

    def _redirect_no_initial_verification(self, user, course_key):
        """Redirect because the user does not have an initial verification.

        NOTE: currently, we assume that courses are configured such that
        the first re-verification always occurs AFTER the initial verification
        deadline.  Later, we may want to allow users to upgrade to a verified
        track, then submit an initial verification that also counts
        as a verification for the checkpoint in the course.

        Arguments:
            user (User): The user who made the request.
            course_key (CourseKey): The identifier for the course for which
                the user is attempting to re-verify.

        Returns:
            HttpResponse

        """
        log.warning(
            u"User %s does not have an initial verification, so "
            u"he/she will be redirected to the \"verify later\" flow "
            u"for the course %s.",
            user.id, course_key
        )
        return redirect(reverse('verify_student_verify_now', kwargs={'course_id': unicode(course_key)}))


class VerifyLaterView(RedirectView):
    """ This view has been deprecated and should redirect to the unified verification flow. """
    permanent = True

    def get_redirect_url(self, course_id, **kwargs):    # pylint: disable=unused-argument
        return reverse('verify_student_verify_now', kwargs={'course_id': unicode(course_id)})
