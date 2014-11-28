"""Helper functions for the student account app. """
from django.core.urlresolvers import reverse
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode
from third_party_auth import (  # pylint: disable=W0611
    pipeline, provider,
    is_enabled as third_party_auth_enabled
)


def auth_pipeline_urls(auth_entry, redirect_url=None, course_id=None):
    """Retrieve URLs for each enabled third-party auth provider.

    These URLs are used on the "sign up" and "sign in" buttons
    on the login/registration forms to allow users to begin
    authentication with a third-party provider.

    Optionally, we can redirect the user to an arbitrary
    url after auth completes successfully.  We use this
    to redirect the user to a page that required login,
    or to send users to the payment flow when enrolling
    in a course.

    Args:
        auth_entry (string): Either `pipeline.AUTH_ENTRY_LOGIN` or `pipeline.AUTH_ENTRY_REGISTER`

    Keyword Args:
        redirect_url (unicode): If provided, send users to this URL
            after they successfully authenticate.

        course_id (unicode): The ID of the course the user is enrolling in.
            We use this to send users to the track selection page
            if the course has a payment option.
            Note that `redirect_url` takes precedence over the redirect
            to the track selection page.

    Returns:
        dict mapping provider names to URLs

    """
    if not third_party_auth_enabled():
        return {}

    if redirect_url is not None:
        pipeline_redirect = redirect_url
    elif course_id is not None:
        # If the course is white-label (paid), then we send users
        # to the shopping cart.  (There is a third party auth pipeline
        # step that will add the course to the cart.)
        if CourseMode.is_white_label(CourseKey.from_string(course_id)):
            pipeline_redirect = reverse("shoppingcart.views.show_cart")

        # Otherwise, send the user to the track selection page.
        # The track selection page may redirect the user to the dashboard
        # (if the only available mode is honor), or directly to verification
        # (for professional ed).
        else:
            pipeline_redirect = reverse(
                "course_modes_choose",
                kwargs={'course_id': unicode(course_id)}
            )
    else:
        pipeline_redirect = None

    return {
        provider.NAME: pipeline.get_login_url(
            provider.NAME, auth_entry,
            enroll_course_id=course_id,
            redirect_url=pipeline_redirect
        )
        for provider in provider.Registry.enabled()
    }
