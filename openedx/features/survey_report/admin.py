"""
Django Admin page for SurveyReport.
"""


from django.contrib import admin
from .models import SurveyReport

class SurveyReportAdmin(admin.ModelAdmin):
    """
    Admin to manage survey reports.
    """
    readonly_fields = (
        'courses_offered', 'learners', 'registered_learners',
        'enrollments', 'generated_certificates', 'extra_data',
        'created_at'
    )

    list_display = (
        'id', 'summary', 'created_at'
    )

    def summary(self, obj) -> str:
        """
        Show a summary of the survey report.
        info:
        - Courses: Total number of active unique courses.
        - Learners: Recently active users with login in some weeks.
        - Enrollments: Total number of active enrollments in the platform.
        """
        return f"Courses: {obj.courses_offered}, Learners: {obj.learners}, Enrollments: {obj.enrollments}"

    def has_add_permission(self, request):
        """
        Removes the "add" button from admin.
        """
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Removes the "save" buttons from admin change view.
        """
        extra_context = extra_context or {}

        extra_context['show_save'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save_and_add_another'] = False

        return super().changeform_view(request, object_id, form_url, extra_context)

admin.site.register(SurveyReport, SurveyReportAdmin)
