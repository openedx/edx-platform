"""
Admin site bindings for CourseActionState
"""

from django.contrib import admin

from common.djangoapps.course_action_state.models import CourseRerunState

admin.site.register(CourseRerunState)
