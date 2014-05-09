"""
Views for the course_mode module
"""

import decimal
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponseBadRequest,  Http404
)
from django.shortcuts import redirect
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from edxmako.shortcuts import render_to_response

from course_modes.models import CourseMode
from courseware.access import has_access
from student.models import CourseEnrollment
from student.views import course_from_id
from verify_student.models import SoftwareSecurePhotoVerification
from xmodule.modulestore.locations import SlashSeparatedCourseKey


class ChooseModeView(View):
    """
    View used when the user is asked to pick a mode

    When a get request is used, shows the selection page.
    When a post request is used, assumes that it is a form submission
        from the selection page, parses the response, and then sends user
        to the next step in the flow
    """
    @method_decorator(login_required)
    def get(self, request, course_id, error=None):
        """ Displays the course mode choice page """

        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        enrollment_mode = CourseEnrollment.enrollment_mode_for_user(request.user, course_key)
        upgrade = request.GET.get('upgrade', False)
        request.session['attempting_upgrade'] = upgrade

        # verified users do not need to register or upgrade
        if enrollment_mode == 'verified':
            return redirect(reverse('dashboard'))

        # registered users who are not trying to upgrade do not need to re-register
        if enrollment_mode is not None and upgrade is False:
            return redirect(reverse('dashboard'))

        modes = CourseMode.modes_for_course_dict(course_key)
        donation_for_course = request.session.get("donation_for_course", {})
        chosen_price = donation_for_course.get(course_key, None)

        course = course_from_id(course_key)
        context = {
            "course_modes_choose_url": reverse("course_modes_choose", kwargs={'course_id': course_key.to_deprecated_string()}),
            "modes": modes,
            "course_name": course.display_name_with_default,
            "course_org": course.display_org_with_default,
            "course_num": course.display_number_with_default,
            "chosen_price": chosen_price,
            "error": error,
            "upgrade": upgrade,
        }
        if "verified" in modes:
            context["suggested_prices"] = [decimal.Decimal(x) for x in modes["verified"].suggested_prices.split(",")]
            context["currency"] = modes["verified"].currency.upper()
            context["min_price"] = modes["verified"].min_price

        return render_to_response("course_modes/choose.html", context)

    @method_decorator(login_required)
    def post(self, request, course_id):
        """ Takes the form submission from the page and parses it """
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        user = request.user

        # This is a bit redundant with logic in student.views.change_enrollement,
        # but I don't really have the time to refactor it more nicely and test.
        course = course_from_id(course_key)
        if not has_access(user, 'enroll', course):
            error_msg = _("Enrollment is closed")
            return self.get(request, course_key, error=error_msg)

        upgrade = request.GET.get('upgrade', False)

        requested_mode = self.get_requested_mode(request.POST)

        allowed_modes = CourseMode.modes_for_course_dict(course_key)
        if requested_mode not in allowed_modes:
            return HttpResponseBadRequest(_("Enrollment mode not supported"))

        if requested_mode in ("audit", "honor"):
            CourseEnrollment.enroll(user, course_key, requested_mode)
            return redirect('dashboard')

        mode_info = allowed_modes[requested_mode]

        if requested_mode == "verified":
            amount = request.POST.get("contribution") or \
                request.POST.get("contribution-other-amt") or 0

            try:
                # validate the amount passed in and force it into two digits
                amount_value = decimal.Decimal(amount).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            except decimal.InvalidOperation:
                error_msg = _("Invalid amount selected.")
                return self.get(request, course_key, error=error_msg)

            # Check for minimum pricing
            if amount_value < mode_info.min_price:
                error_msg = _("No selected price or selected price is too low.")
                return self.get(request, course_key, error=error_msg)

            donation_for_course = request.session.get("donation_for_course", {})
            donation_for_course[course_key] = amount_value
            request.session["donation_for_course"] = donation_for_course
            if SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
                return redirect(
                    reverse('verify_student_verified',
                            kwargs={'course_id': course_key.to_deprecated_string()}) + "?upgrade={}".format(upgrade)
                )

            return redirect(
                reverse('verify_student_show_requirements',
                        kwargs={'course_id': course_key.to_deprecated_string()}) + "?upgrade={}".format(upgrade))

    def get_requested_mode(self, request_dict):
        """
        Given the request object of `user_choice`, return the
        corresponding course mode slug
        """
        if 'audit_mode' in request_dict:
            return 'audit'
        if 'certificate_mode' and request_dict.get("honor-code"):
            return 'honor'
        if 'certificate_mode' in request_dict:
            return 'verified'
