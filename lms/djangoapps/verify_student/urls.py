from django.conf.urls import patterns, url

from verify_student import views
from verify_student.views import PayAndVerifyView

from django.conf import settings


urlpatterns = patterns(
    '',
    url(
        r'^show_requirements/{}/$'.format(settings.COURSE_ID_PATTERN),
        views.show_requirements,
        name="verify_student_show_requirements"
    ),

    # pylint sometimes seems to dislike the as_view() function because as_view() is
    # decorated with `classonlymethod` instead of `classmethod`.  It's inconsistent
    # about *which* as_view() calls it grumbles about, but we disable those warnings
    url(
        r'^verify/{}/$'.format(settings.COURSE_ID_PATTERN),
        views.VerifyView.as_view(),  # pylint: disable=no-value-for-parameter
        name="verify_student_verify"
    ),

    url(
        r'^verified/{}/$'.format(settings.COURSE_ID_PATTERN),
        views.VerifiedView.as_view(),
        name="verify_student_verified"
    ),

    url(
        r'^create_order',
        views.create_order,
        name="verify_student_create_order"
    ),

    url(
        r'^results_callback$',
        views.results_callback,
        name="verify_student_results_callback",
    ),

    url(
        r'^reverify$',
        views.ReverifyView.as_view(),
        name="verify_student_reverify"
    ),

    url(
        r'^midcourse_reverify/{}/$'.format(settings.COURSE_ID_PATTERN),
        views.MidCourseReverifyView.as_view(),  # pylint: disable=no-value-for-parameter
        name="verify_student_midcourse_reverify"
    ),

    url(
        r'^reverification_confirmation$',
        views.reverification_submission_confirmation,
        name="verify_student_reverification_confirmation"
    ),

    url(
        r'^midcourse_reverification_confirmation$',
        views.midcourse_reverification_confirmation,
        name="verify_student_midcourse_reverification_confirmation"
    ),

    url(
        r'^midcourse_reverify_dash$',
        views.midcourse_reverify_dash,
        name="verify_student_midcourse_reverify_dash"
    ),

    url(
        r'^reverification_window_expired$',
        views.reverification_window_expired,
        name="verify_student_reverification_window_expired"
    ),

    url(
        r'^toggle_failed_banner_off$',
        views.toggle_failed_banner_off,
        name="verify_student_toggle_failed_banner_off"
    ),
)


if settings.FEATURES.get("SEPARATE_VERIFICATION_FROM_PAYMENT"):

    urlpatterns += patterns(
        '',

        url(
            r'^submit-photos/$',
            views.submit_photos_for_verification,
            name="verify_student_submit_photos"
        ),

        # The user is starting the verification / payment process,
        # most likely after enrolling in a course and selecting
        # a "verified" track.
        url(
            r'^start-flow/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
            views.PayAndVerifyView.as_view(),  # pylint: disable=no-value-for-parameter
            name="verify_student_start_flow",
            kwargs={
                'message': PayAndVerifyView.FIRST_TIME_VERIFY_MSG
            }
        ),

        # The user is enrolled in a non-paid mode and wants to upgrade.
        # This is the same as the "start verification" flow,
        # except with slight messaging changes.
        url(
            r'^upgrade/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
            views.PayAndVerifyView.as_view(),  # pylint: disable=no-value-for-parameter
            name="verify_student_upgrade_and_verify",
            kwargs={
                'message': PayAndVerifyView.UPGRADE_MSG
            }
        ),

        # The user has paid and still needs to verify.
        # Since the user has "just paid", we display *all* steps
        # including payment.  The user resumes the flow
        # from the verification step.
        # Note that if the user has already verified, this will redirect
        # to the dashboard.
        url(
            r'^verify-now/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
            views.PayAndVerifyView.as_view(),  # pylint: disable=no-value-for-parameter
            name="verify_student_verify_now",
            kwargs={
                'always_show_payment': True,
                'current_step': PayAndVerifyView.FACE_PHOTO_STEP,
                'message': PayAndVerifyView.VERIFY_NOW_MSG
            }
        ),

        # The user has paid and still needs to verify,
        # but the user is NOT arriving directly from the payment flow.
        # This is equivalent to starting a new flow
        # with the payment steps and requirements hidden
        # (since the user already paid).
        url(
            r'^verify-later/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
            views.PayAndVerifyView.as_view(),  # pylint: disable=no-value-for-parameter
            name="verify_student_verify_later",
            kwargs={
                'message': PayAndVerifyView.VERIFY_LATER_MSG
            }
        ),

        # The user is returning to the flow after paying.
        # This usually occurs after a redirect from the shopping cart
        # once the order has been fulfilled.
        url(
            r'^payment-confirmation/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
            views.PayAndVerifyView.as_view(),  # pylint: disable=no-value-for-parameter
            name="verify_student_payment_confirmation",
            kwargs={
                'always_show_payment': True,
                'current_step': PayAndVerifyView.PAYMENT_CONFIRMATION_STEP,
                'message': PayAndVerifyView.PAYMENT_CONFIRMATION_MSG
            }
        ),
    )
