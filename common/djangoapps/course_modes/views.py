"""
Views for the course_mode module
"""

import decimal
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest
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
from util.db import commit_on_success_with_read_committed
from xmodule.modulestore.django import modulestore


class ChooseModeView(View):
    """View used when the user is asked to pick a mode.

    When a get request is used, shows the selection page.

    When a post request is used, assumes that it is a form submission
    from the selection page, parses the response, and then sends user
    to the next step in the flow.

    """

    @method_decorator(login_required)
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

        upgrade = request.GET.get('upgrade', False)
        request.session['attempting_upgrade'] = upgrade

        enrollment_mode, is_active = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)
        modes = CourseMode.modes_for_course_dict(course_key)

        # We assume that, if 'professional' is one of the modes, it is the *only* mode.
        # If we offer more modes alongside 'professional' in the future, this will need to route
        # to the usual "choose your track" page.
        has_enrolled_professional = (enrollment_mode == "professional" and is_active)
        if "professional" in modes and not has_enrolled_professional:
            return redirect(
                reverse(
                    'verify_student_show_requirements',
                    kwargs={'course_id': course_key.to_deprecated_string()}
                )
            )

        # If there isn't a verified mode available, then there's nothing
        # to do on this page.  The user has almost certainly been auto-registered
        # in the "honor" track by this point, so we send the user
        # to the dashboard.
        if not CourseMode.has_verified_mode(modes):
            return redirect(reverse('dashboard'))

        # If a user has already paid, redirect them to the dashboard.
        if is_active and enrollment_mode in CourseMode.VERIFIED_MODES:
            return redirect(reverse('dashboard'))

        donation_for_course = request.session.get("donation_for_course", {})
        chosen_price = donation_for_course.get(unicode(course_key), None)

        course = modulestore().get_course(course_key)
        context = {
            "course_modes_choose_url": reverse("course_modes_choose", kwargs={'course_id': course_key.to_deprecated_string()}),
            "modes": modes,
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "chosen_price": chosen_price,
            "error": error,
            "upgrade": upgrade,
            "can_audit": "audit" in modes,
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

    @method_decorator(login_required)
    @method_decorator(commit_on_success_with_read_committed)
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

        upgrade = request.GET.get('upgrade', False)

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
                reverse('verify_student_show_requirements',
                        kwargs={'course_id': course_key.to_deprecated_string()}) + "?upgrade={}".format(upgrade))

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
