from django.views.i18n import set_language as django_set_language
from django.views.decorators.csrf import csrf_exempt
from xmodule.modulestore.django import modulestore
from courseware.access import has_access
from util.json_request import JsonResponse
from courseware.grades import grade
from opaque_keys.edx import locator

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