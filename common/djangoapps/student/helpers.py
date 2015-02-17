"""Helpers for the student app. """
import time
from datetime import datetime
from pytz import UTC
from django.utils.http import cookie_date
from django.conf import settings
from verify_student.models import SoftwareSecurePhotoVerification  # pylint: disable=F0401
from course_modes.models import CourseMode
from student_account.helpers import auth_pipeline_urls  # pylint: disable=unused-import,import-error


def set_logged_in_cookie(request, response):
    """Set a cookie indicating that the user is logged in.

    Some installations have an external marketing site configured
    that displays a different UI when the user is logged in
    (e.g. a link to the student dashboard instead of to the login page)

    Arguments:
        request (HttpRequest): The request to the view, used to calculate
            the cookie's expiration date based on the session expiration date.
        response (HttpResponse): The response on which the cookie will be set.

    Returns:
        HttpResponse

    """
    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
        expires_time = time.time() + max_age
        expires = cookie_date(expires_time)

    response.set_cookie(
        settings.EDXMKTG_COOKIE_NAME, 'true', max_age=max_age,
        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
        path='/', secure=None, httponly=None,
    )

    return response


def is_logged_in_cookie_set(request):
    """Check whether the request has the logged in cookie set. """
    return settings.EDXMKTG_COOKIE_NAME in request.COOKIES


# Enumeration of per-course verification statuses
# we display on the student dashboard.
VERIFY_STATUS_NEED_TO_VERIFY = "verify_need_to_verify"
VERIFY_STATUS_SUBMITTED = "verify_submitted"
VERIFY_STATUS_APPROVED = "verify_approved"
VERIFY_STATUS_MISSED_DEADLINE = "verify_missed_deadline"
VERIFY_STATUS_NEED_TO_REVERIFY = "verify_need_to_reverify"


def check_verify_status_by_course(user, course_enrollment_pairs, all_course_modes):
    """Determine the per-course verification statuses for a given user.

    The possible statuses are:
        * VERIFY_STATUS_NEED_TO_VERIFY: The student has not yet submitted photos for verification.
        * VERIFY_STATUS_SUBMITTED: The student has submitted photos for verification,
          but has have not yet been approved.
        * VERIFY_STATUS_APPROVED: The student has been successfully verified.
        * VERIFY_STATUS_MISSED_DEADLINE: The student did not submit photos within the course's deadline.
        * VERIFY_STATUS_NEED_TO_REVERIFY: The student has an active verification, but it is
            set to expire before the verification deadline for the course.

    It is is also possible that a course does NOT have a verification status if:
        * The user is not enrolled in a verified mode, meaning that the user didn't pay.
        * The course does not offer a verified mode.
        * The user submitted photos but an error occurred while verifying them.
        * The user submitted photos but the verification was denied.

    In the last two cases, we rely on messages in the sidebar rather than displaying
    messages for each course.

    Arguments:
        user (User): The currently logged-in user.
        course_enrollment_pairs (list): The courses the user is enrolled in.
            The list should contain tuples of `(Course, CourseEnrollment)`.
        all_course_modes (list): List of all course modes for the student's enrolled courses,
            including modes that have expired.

    Returns:
        dict: Mapping of course keys verification status dictionaries.
            If no verification status is applicable to a course, it will not
            be included in the dictionary.
            The dictionaries have these keys:
                * status (str): One of the enumerated status codes.
                * days_until_deadline (int): Number of days until the verification deadline.
                * verification_good_until (str): Date string for the verification expiration date.

    """
    status_by_course = {}

    # Retrieve all verifications for the user, sorted in descending
    # order by submission datetime
    verifications = SoftwareSecurePhotoVerification.objects.filter(user=user)

    # Check whether the user has an active or pending verification attempt
    # To avoid another database hit, we re-use the queryset we have already retrieved.
    has_active_or_pending = SoftwareSecurePhotoVerification.user_has_valid_or_pending(
        user, queryset=verifications
    )

    for course, enrollment in course_enrollment_pairs:

        # Get the verified mode (if any) for this course
        # We pass in the course modes we have already loaded to avoid
        # another database hit, as well as to ensure that expired
        # course modes are included in the search.
        verified_mode = CourseMode.verified_mode_for_course(
            course.id,
            modes=all_course_modes[course.id]
        )

        # If no verified mode has ever been offered, or the user hasn't enrolled
        # as verified, then the course won't display state related to its
        # verification status.
        if verified_mode is not None and enrollment.mode in CourseMode.VERIFIED_MODES:
            deadline = verified_mode.expiration_datetime
            relevant_verification = SoftwareSecurePhotoVerification.verification_for_datetime(deadline, verifications)

            # By default, don't show any status related to verification
            status = None

            # Check whether the user was approved or is awaiting approval
            if relevant_verification is not None:
                if relevant_verification.status == "approved":
                    status = VERIFY_STATUS_APPROVED
                elif relevant_verification.status == "submitted":
                    status = VERIFY_STATUS_SUBMITTED

            # If the user didn't submit at all, then tell them they need to verify
            # If the deadline has already passed, then tell them they missed it.
            # If they submitted but something went wrong (error or denied),
            # then don't show any messaging next to the course, since we already
            # show messages related to this on the left sidebar.
            submitted = (
                relevant_verification is not None and
                relevant_verification.status not in ["created", "ready"]
            )
            if status is None and not submitted:
                if deadline is None or deadline > datetime.now(UTC):
                    if has_active_or_pending:
                        # The user has an active verification, but the verification
                        # is set to expire before the deadline.  Tell the student
                        # to reverify.
                        status = VERIFY_STATUS_NEED_TO_REVERIFY
                    else:
                        status = VERIFY_STATUS_NEED_TO_VERIFY
                else:
                    status = VERIFY_STATUS_MISSED_DEADLINE

            # Set the status for the course only if we're displaying some kind of message
            # Otherwise, leave the course out of the dictionary.
            if status is not None:
                days_until_deadline = None
                verification_good_until = None

                now = datetime.now(UTC)
                if deadline is not None and deadline > now:
                    days_until_deadline = (deadline - now).days

                if relevant_verification is not None:
                    verification_good_until = relevant_verification.expiration_datetime.strftime("%m/%d/%Y")

                status_by_course[course.id] = {
                    'status': status,
                    'days_until_deadline': days_until_deadline,
                    'verification_good_until': verification_good_until
                }

    return status_by_course
