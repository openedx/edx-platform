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

class ChooseModeView(View):

    @method_decorator(login_required)
    def get(self, request):
        course_id = request.GET.get("course_id")
        context = {
            "course_id": course_id,
            "modes": CourseMode.modes_for_course_dict(course_id),
            "course_name": course_from_id(course_id).display_name
        }
        return render_to_response("course_modes/choose.html", context)


    def post(self, request):
        course_id = request.GET.get("course_id")
        user = request.user

        # This is a bit redundant with logic in student.views.change_enrollement,
        # but I don't really have the time to refactor it more nicely and test.
        course = course_from_id(course_id)
        if not has_access(user, course, 'enroll'):
            return HttpResponseBadRequest(_("Enrollment is closed"))

        requested_mode = self.get_requested_mode(request.POST.get("mode"))

        allowed_modes = CourseMode.modes_for_course_dict(course_id)
        if requested_mode not in allowed_modes:
            return HttpResponseBadRequest(_("Enrollment mode not supported"))

        if requested_mode in ("audit", "honor"):
            CourseEnrollment.enroll(user, course_id)
            return redirect('dashboard')

        if requested_mode == "verified":
            amount = request.POST.get("contribution") or \
                     request.POST.get("contribution-other-amt") or \
                     requested_mode.min_price

            donation_for_course = request.session.get("donation_for_course", {})
            donation_for_course[course_id] = float(amount)
            request.session["donation_for_course"] = donation_for_course

            return redirect(
                "{}?{}".format(
                    reverse('verify_student_verify'),
                    urlencode(dict(course_id=course_id))
                )
            )

    def get_requested_mode(self, user_choice):
        choices = {
            "Select Audit" : "audit",
            "Select Certificate" : "verified"
        }
        return choices.get(user_choice)
