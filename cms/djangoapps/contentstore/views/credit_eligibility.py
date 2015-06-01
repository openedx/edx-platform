"""
Views related to credit eligibility criterion of a course.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_GET

from django_future.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.credit.api import get_credit_requirements
from student.auth import has_course_author_access
from xmodule.modulestore.django import modulestore


__all__ = ['credit_eligibility_handler', ]


@ensure_csrf_cookie
@require_GET
@login_required
def credit_eligibility_handler(request, course_key_string):
    """
    The restful handler for credit eligibility checklists.

    GET
        html: return html page for all checklists
        json: not currently supported
    """

    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)
    if request.method == 'GET':
        # get and display all credit eligibility requirements.
        requirements = get_credit_requirements(course_key)

        # show warning message to course author if 'minimum_grade_credit' of a
        # course is not set or 0.
        show_warning = False if course_module.minimum_grade_credit > 0 else True
        return render_to_response(
            'credit_eligibility.html',
            {
                'requirements': requirements,
                'context_course': course_module,
                'show_warning': show_warning,
            }
        )
