"""
Views for the course_mode module
"""

import decimal
from ipware.ip import get_ip

from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from edxmako.shortcuts import render_to_response

from course_modes.models import CourseMode
from courseware.access import has_access
from student.models import CourseEnrollment
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.keys import CourseKey
from util.db import outer_atomic
from xmodule.modulestore.django import modulestore

from embargo import api as embargo_api


class ChooseModeView(View):
    """View used when the user is asked to pick a mode.

    When a get request is used, shows the selection page.

    When a post request is used, assumes that it is a form submission
    from the selection page, parses the response, and then sends user
    to the next step in the flow.

    """

    @method_decorator(transaction.non_atomic_requests)
    def dispatch(self, *args, **kwargs):        # pylint: disable=missing-docstring
        return super(ChooseModeView, self).dispatch(*args, **kwargs)

    @method_decorator(login_required)
    @method_decorator(transaction.atomic)
    def get(self, request, course_id, error=None):
        """Displays the course mode choice page.

        Args:
            request (`Request`): The Django Request object.
            course_id (unicode): The slash-separated course key.

        Keyword Args:
            error (unicode): If provided, display this error message
                on the page.

        Returns:
            Response

        """
        course_key = CourseKey.from_string(course_id)

        # Check whether the user has access to this course
        # based on country access rules.
        embargo_redirect = embargo_api.redirect_if_blocked(
            course_key,
            user=request.user,
            ip_address=get_ip(request),
            url=request.path
        )
        if embargo_redirect:
            return redirect(embargo_redirect)

        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)
        modes = CourseMode.modes_for_course_dict(course_key)

        # We assume that, if 'professional' is one of the modes, it is the *only* mode.
        # If we offer more modes alongside 'professional' in the future, this will need to route
        # to the usual "choose your track" page same is true for no-id-professional mode.
        has_enrolled_professional = (CourseMode.is_professional_slug(enrollment_mode) and is_active)
        if CourseMode.has_professional_mode(modes) and not has_enrolled_professional:
            return redirect(
                reverse(
                    'verify_student_start_flow',
                    kwargs={'course_id': unicode(course_key)}
                )
            )

        # If there isn't a verified mode available, then there's nothing
        # to do on this page.  The user has almost certainly been auto-registered
        # in the "honor" track by this point, so we send the user
        # to the dashboard.
        if not CourseMode.has_verified_mode(modes):
            return redirect(reverse('dashboard'))

        # If a user has already paid, redirect them to the dashboard.
        if is_active and (enrollment_mode in CourseMode.VERIFIED_MODES + [CourseMode.NO_ID_PROFESSIONAL_MODE]):
            return redirect(reverse('dashboard'))

        donation_for_course = request.session.get("donation_for_course", {})
        chosen_price = donation_for_course.get(unicode(course_key), None)

        course = modulestore().get_course(course_key)

        # When a credit mode is available, students will be given the option
        # to upgrade from a verified mode to a credit mode at the end of the course.
        # This allows students who have completed photo verification to be eligible
        # for univerity credit.
        # Since credit isn't one of the selectable options on the track selection page,
        # we need to check *all* available course modes in order to determine whether
        # a credit mode is available.  If so, then we show slightly different messaging
        # for the verified track.
        has_credit_upsell = any(
            CourseMode.is_credit_mode(mode) for mode
            in CourseMode.modes_for_course(course_key, only_selectable=False)
        )

        context = {
            "course_modes_choose_url": reverse("course_modes_choose", kwargs={'course_id': course_key.to_deprecated_string()}),
            "modes": modes,
            "has_credit_upsell": has_credit_upsell,
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "chosen_price": chosen_price,
            "error": error,
            "responsive": True,
            "nav_hidden": True,
        }
        if "verified" in modes:
            context["suggested_prices"] = [
                decimal.Decimal(x.strip())
                for x in modes["verified"].suggested_prices.split(",")
                if x.strip()
            ]
            context["currency"] = modes["verified"].currency.upper()
            context["min_price"] = modes["verified"].min_price
            context["verified_name"] = modes["verified"].name
            context["verified_description"] = modes["verified"].description

        return render_to_response("course_modes/choose.html", context)

    @method_decorator(transaction.non_atomic_requests)
    @method_decorator(login_required)
    @method_decorator(outer_atomic(read_committed=True))
    def post(self, request, course_id):
        """Takes the form submission from the page and parses it.

        Args:
            request (`Request`): The Django Request object.
            course_id (unicode): The slash-separated course key.

        Returns:
            Status code 400 when the requested mode is unsupported. When the honor mode
            is selected, redirects to the dashboard. When the verified mode is selected,
            returns error messages if the indicated contribution amount is invalid or
            below the minimum, otherwise redirects to the verification flow.

        """
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        user = request.user

        # This is a bit redundant with logic in student.views.change_enrollment,
        # but I don't really have the time to refactor it more nicely and test.
        course = modulestore().get_course(course_key)
        if not has_access(user, 'enroll', course):
            error_msg = _("Enrollment is closed")
            return self.get(request, course_id, error=error_msg)

        requested_mode = self._get_requested_mode(request.POST)

        allowed_modes = CourseMode.modes_for_course_dict(course_key)
        if requested_mode not in allowed_modes:
            return HttpResponseBadRequest(_("Enrollment mode not supported"))

        if requested_mode == 'honor':
            # The user will have already been enrolled in the honor mode at this
            # point, so we just redirect them to the dashboard, thereby avoiding
            # hitting the database a second time attempting to enroll them.
            return redirect(reverse('dashboard'))

        mode_info = allowed_modes[requested_mode]

        if requested_mode == 'verified':
            amount = request.POST.get("contribution") or \
                request.POST.get("contribution-other-amt") or 0

            try:
                # Validate the amount passed in and force it into two digits
                amount_value = decimal.Decimal(amount).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            except decimal.InvalidOperation:
                error_msg = _("Invalid amount selected.")
                return self.get(request, course_id, error=error_msg)

            # Check for minimum pricing
            if amount_value < mode_info.min_price:
                error_msg = _("No selected price or selected price is too low.")
                return self.get(request, course_id, error=error_msg)

            donation_for_course = request.session.get("donation_for_course", {})
            donation_for_course[unicode(course_key)] = amount_value
            request.session["donation_for_course"] = donation_for_course

            return redirect(
                reverse(
                    'verify_student_start_flow',
                    kwargs={'course_id': unicode(course_key)}
                )
            )

    def _get_requested_mode(self, request_dict):
        """Get the user's requested mode

        Args:
            request_dict (`QueryDict`): A dictionary-like object containing all given HTTP POST parameters.

        Returns:
            The course mode slug corresponding to the choice in the POST parameters,
            None if the choice in the POST parameters is missing or is an unsupported mode.

        """
        if 'verified_mode' in request_dict:
            return 'verified'
        if 'honor_mode' in request_dict:
            return 'honor'
        else:
            return None


def create_mode(request, course_id):
    """Add a mode to the course corresponding to the given course ID.

    Only available when settings.FEATURES['MODE_CREATION_FOR_TESTING'] is True.

    Attempts to use the following querystring parameters from the request:
        `mode_slug` (str): The mode to add, either 'honor', 'verified', or 'professional'
        `mode_display_name` (str): Describes the new course mode
        `min_price` (int): The minimum price a user must pay to enroll in the new course mode
        `suggested_prices` (str): Comma-separated prices to suggest to the user.
        `currency` (str): The currency in which to list prices.

    By default, this endpoint will create an 'honor' mode for the given course with display name
    'Honor Code', a minimum price of 0, no suggested prices, and using USD as the currency.

    Args:
        request (`Request`): The Django Request object.
        course_id (unicode): A course ID.

    Returns:
        Response
    """
    PARAMETERS = {
        'mode_slug': u'honor',
        'mode_display_name': u'Honor Code Certificate',
        'min_price': 0,
        'suggested_prices': u'',
        'currency': u'usd',
    }

    # Try pulling querystring parameters out of the request
    for parameter, default in PARAMETERS.iteritems():
        PARAMETERS[parameter] = request.GET.get(parameter, default)

    # Attempt to create the new mode for the given course
    course_key = CourseKey.from_string(course_id)
    CourseMode.objects.get_or_create(course_id=course_key, **PARAMETERS)

    # Return a success message and a 200 response
    return HttpResponse("Mode '{mode_slug}' created for '{course}'.".format(
        mode_slug=PARAMETERS['mode_slug'],
        course=course_id
    ))
