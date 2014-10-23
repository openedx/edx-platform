from django.views.i18n import set_language as django_set_language
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from xmodule.modulestore.django import modulestore
from courseware.access import has_access
from util.json_request import JsonResponse
from courseware.grades import grade
from opaque_keys.edx import locator
from util.cache import cache_if_anonymous
from django.conf import settings
from courseware.courses import get_courses, sort_by_announcement
from edxmako.shortcuts import render_to_response
from django.contrib.auth.models import AnonymousUser

@csrf_exempt
def set_language(request):
    return django_set_language(request)


def check_student_grades(request):
    user = request.user
    course_id = request.POST['course_id']
    course_key = locator.CourseLocator.from_string(course_id)
    course = modulestore().get_course(course_key)

    # If user is course staff don't grade the user
    if has_access(user, 'staff', course):
        request.session['course_pass_%s' % course_id] = True
        return JsonResponse({'success': True, 'error': False})

    try:
        if grade(user, request, course)['grade']:
            request.session['course_pass_%s' % course_id] = True
            return JsonResponse({'success': True, 'error': False})
        else:
            return JsonResponse({'success': False, 'error': False})
    except:
        return JsonResponse({'success': False, 'error': True})


@ensure_csrf_cookie
@cache_if_anonymous
def all_courses(request, extra_context={}, user=AnonymousUser()):
    """
    Render the edX main page.

    extra_context is used to allow immediate display of certain modal windows, eg signup,
    as used by external_auth.
    """

    # The course selection work is done in courseware.courses.
    domain = settings.FEATURES.get('FORCE_UNIVERSITY_DOMAIN')  # normally False
    # do explicit check, because domain=None is valid
    if domain is False:
        domain = request.META.get('HTTP_HOST')

    # Hardcoded `AnonymousUser()` to hide unpublished courses always
    courses = get_courses(AnonymousUser(), domain=domain)
    courses = sort_by_announcement(courses)

    context = {'courses': courses}

    context.update(extra_context)
    return render_to_response('all_courses.html', context)
