from django.conf.urls import patterns, url

from verify_student import views

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
