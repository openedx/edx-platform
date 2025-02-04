"""
Admin site bindings for CourseActionState
"""

from django.contrib import admin

from common.djangoapps.course_action_state.models import CourseRerunState


class CourseRerunStateAdmin(admin.ModelAdmin):
    """ Django Admin form class for CourseRerunState model """
    exclude = ["course_key"]

    def get_queryset(self, request):
        # For any query against this table, remove course_key field
        # because that field might have bad data in it.
        qs = CourseRerunState.objects.defer('course_key')
        return qs


admin.site.register(CourseRerunState, CourseRerunStateAdmin)
