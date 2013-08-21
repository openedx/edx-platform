from django.http import HttpResponse
from django.views.generic.base import View

from mitxmako.shortcuts import render_to_response

from course_modes.models import CourseMode

class ChooseModeView(View):

    def get(self, request):
        course_id = request.GET.get("course_id")
        context = {
            "course_id" : course_id,
            "available_modes" : CourseMode.modes_for_course(course_id)
        }
        return render_to_response("course_modes/choose.html", context)

    def post(self, request):
        course_id = request.GET.get("course_id")
        mode_slug = request.POST.get("mode_slug")
        user = request.user

        # This is a bit redundant with logic in student.views.change_enrollement,
        # but I don't really have the time to refactor it more nicely and test.
        course = course_from_id(course_id)
        if has_access(user, course, 'enroll'):
            pass
