"""
URL definitions for the verify_student app.
"""


from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.verify_student import views

urlpatterns = [
    # The user is starting the verification / payment process,
    # most likely after enrolling in a course and selecting
    # a "verified" track.
    url(
        r'^start-flow/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
        # Pylint seems to dislike the as_view() method because as_view() is
        # decorated with `classonlymethod` instead of `classmethod`.
        views.PayAndVerifyView.as_view(),
        name="verify_student_start_flow",
        kwargs={
            'message': views.PayAndVerifyView.FIRST_TIME_VERIFY_MSG
        }
    ),

    # This is for A/B testing.
    url(
        r'^begin-flow/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
        views.PayAndVerifyView.as_view(),
        name="verify_student_begin_flow",
        kwargs={
            'message': views.PayAndVerifyView.FIRST_TIME_VERIFY_MSG
        }
    ),

    # The user is enrolled in a non-paid mode and wants to upgrade.
    # This is the same as the "start verification" flow,
    # except with slight messaging changes.
    url(
        r'^upgrade/{course}/$'.format(course=settings.COURSE_ID_PATTERN),
        views.PayAndVerifyView.as_view(),
        name="verify_student_upgrade_and_verify",
        kwargs={
            'message': views.PayAndVerifyView.UPGRADE_MSG
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
        views.PayAndVerifyView.as_view(),
        name="verify_student_verify_now",
        kwargs={
            'always_show_payment': True,
            'current_step': views.PayAndVerifyView.FACE_PHOTO_STEP,
            'message': views.PayAndVerifyView.VERIFY_NOW_MSG
        }
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
        r'^submit-photos/$',
        views.SubmitPhotosView.as_view(),
        name="verify_student_submit_photos"
    ),

    url(
        r'^status/$',
        views.VerificationStatusAPIView.as_view(),
        name="verification_status_api"
    ),


    # End-point for reverification
    # Reverification occurs when a user's initial verification attempt
    # is denied or expires.  The user is allowed to retry by submitting
    # new photos.  This is different than *in-course* reverification,
    # in which a student submits only face photos, which are matched
    # against the ID photo from the user's initial verification attempt.
    url(
        r'^reverify$',
        views.ReverifyView.as_view(),
        name="verify_student_reverify"
    ),
]

# Fake response page for incourse reverification ( software secure )
if settings.FEATURES.get('ENABLE_SOFTWARE_SECURE_FAKE'):
    from lms.djangoapps.verify_student.tests.fake_software_secure import SoftwareSecureFakeView
    urlpatterns += [
        url(r'^software-secure-fake-response', SoftwareSecureFakeView.as_view()),
    ]
