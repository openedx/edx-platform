import decimal
from django.core.urlresolvers import reverse
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
)
from django.shortcuts import redirect
from django.views.generic.base import View
from django.utils.translation import ugettext as _
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from mitxmako.shortcuts import render_to_response

from course_modes.models import CourseMode
from courseware.access import has_access
from student.models import CourseEnrollment
from student.views import course_from_id
from verify_student.models import SoftwareSecurePhotoVerification

class ChooseModeView(View):

    @method_decorator(login_required)
    def get(self, request, course_id, error=None):
        if CourseEnrollment.enrollment_mode_for_user(request.user, course_id) == 'verified':
            return redirect(reverse('dashboard'))
        modes = CourseMode.modes_for_course_dict(course_id)
        context = {
            "course_id": course_id,
            "modes": modes,
            "course_name": course_from_id(course_id).display_name,
            "chosen_price": None,
            "error": error,
        }
        if "verified" in modes:
            context["suggested_prices"] = modes["verified"].suggested_prices.split(",")
            context["currency"] = modes["verified"].currency.upper()
            context["min_price"] = modes["verified"].min_price

        return render_to_response("course_modes/choose.html", context)

    @method_decorator(login_required)
    def post(self, request, course_id):
        user = request.user

        # This is a bit redundant with logic in student.views.change_enrollement,
        # but I don't really have the time to refactor it more nicely and test.
        course = course_from_id(course_id)
        if not has_access(user, course, 'enroll'):
            error_msg = _("Enrollment is closed")
            return self.get(request, course_id, error=error_msg)

        requested_mode = self.get_requested_mode(request.POST.get("mode"))
        if requested_mode == "verified" and request.POST.get("honor-code"):
            requested_mode = "honor"

        allowed_modes = CourseMode.modes_for_course_dict(course_id)
        if requested_mode not in allowed_modes:
            return HttpResponseBadRequest(_("Enrollment mode not supported"))

        if requested_mode in ("audit", "honor"):
            CourseEnrollment.enroll(user, course_id)
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
                return self.get(request, course_id, error=error_msg)

            # Check for minimum pricing
            if amount_value < mode_info.min_price:
                error_msg = _("No selected price or selected price is too low.")
                return self.get(request, course_id, error=error_msg)

            donation_for_course = request.session.get("donation_for_course", {})
            donation_for_course[course_id] = amount_value
            request.session["donation_for_course"] = donation_for_course
            if SoftwareSecurePhotoVerification.user_has_valid_or_pending(request.user):
                return redirect(
                    reverse('verify_student_verified',
                            kwargs={'course_id': course_id})
                )

            return redirect(
                reverse('verify_student_show_requirements',
                        kwargs={'course_id': course_id}),
            )

    def get_requested_mode(self, user_choice):
        choices = {
            "Select Audit": "audit",
            "Select Certificate": "verified"
        }
        return choices.get(user_choice)
