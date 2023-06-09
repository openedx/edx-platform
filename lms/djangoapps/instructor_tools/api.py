from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from django.db import transaction
from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.instructor_task import api
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.instructor_tools.all_grades_CSV import get_all_csv_file, process_grade_file, merge_all_csv, process_merged

@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def calculate_all_grades_csv(request):
    all_course = CourseOverview.get_all_courses(['FUNiX'])

    for course in all_course:
        course_key = CourseKey.from_string(str(course))
        api.submit_calculate_grades_csv_not_async(request, course_key)
    
    all_csv_files = get_all_csv_file()
    all_grade_files = process_grade_file(all_csv_files)
    combined_file = merge_all_csv(all_grade_files)
    out_file = process_merged(combined_file)


    return JsonResponse({'output': out_file})