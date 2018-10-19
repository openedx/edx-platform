"""
Grade book view for instructor and pagination work (for grade book)
which is currently use by ccx and instructor apps.
"""
from django.db import transaction
from django.http import HttpResponseNotFound
from django.views.decorators.cache import cache_control
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.grades.config.waffle import waffle_flags, WRITABLE_GRADEBOOK
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.instructor.views.api import require_level


@transaction.non_atomic_requests
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def writable_gradebook(request, course_id):
    """
    Show the writable gradebook for this course:
    - Only displayed to course staff
    """
    course_key = CourseKey.from_string(course_id)
    if not waffle_flags()[WRITABLE_GRADEBOOK].is_enabled(course_key):
        return HttpResponseNotFound()

    course = get_course_with_access(request.user, 'load', course_key)

    course_grade = CourseGradeFactory().read(request.user, course)
    courseware_summary = course_grade.chapter_grades.values()
    course_sections = []

    for chapter in courseware_summary:
        chapter_name = chapter['display_name']
        for section in chapter['sections']:
            if section.problem_scores and section.graded and chapter_name not in course_sections:
                course_sections.append(chapter_name)

    return render_to_response('courseware/writable_gradebook.html', {
        'number_of_students': 2,
        'course': course,
        'course_id': course_key,
        'course_sections': course_sections,
        # Checked above
        'staff_access': True,
        'ordered_grades': sorted(course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True),
    })
