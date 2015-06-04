"""
Fake page for updating the minimum grade course requirement status for a user.
"""

from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.credit.models import CreditCourse, CreditRequirement, CreditRequirementStatus
from xmodule.modulestore.django import modulestore


class UpdateMinGradeRequirementFakeView(View):
    """
    Fake view for updating minimum grade status in
    credit eligibility status table.
    """

    @method_decorator(login_required)
    def get(self, request):
        """
        Render a fake page for updating the minimum grade course requirement
        status for a user.
        """
        context = {
            'csrf_token': unicode(csrf(request)['csrf_token'])
        }

        return render_to_response("credit/fake_credit_eligibility_status.html", context)

    @method_decorator(login_required)
    def post(self, request):
        """
        After validating all conditions it will update minimum grade
        status in credit eligibility requirements status table.
        """
        context = {}
        course_key, error = None, None
        course_id = request.POST.get("txt_coursekey")
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            error = "Cannot make a valid CourseKey from id {}!".format(course_id)

        if course_key:
            if not modulestore().has_course(course_key):
                error = "Cannot find course with id {} in the modulestore".format(course_id)
            elif not CreditCourse.is_credit_course(course_key):
                error = "This Course {} is not set as credit course".format(course_id)
            else:
                requirement = CreditRequirement.get_course_requirement(course_key, "grade", "grade")
                if not requirement:
                    error = "This Course {} with grade is not available in requirements.".format(course_id)
                else:
                    CreditRequirementStatus.add_or_update_requirement_status(
                        request.user.username, requirement
                    )
                    context["status"] = True

        context["error"] = error

        return render_to_response("credit/fake_credit_eligibility_status.html", context)
